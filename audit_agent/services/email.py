"""
Service Email — Livraison du rapport PDF par email via SMTP Gmail.
Envoie l'email au client + une notification interne à SMD GLOBAL.
"""
import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text      import MIMEText
from email.mime.base      import MIMEBase
from email                import encoders
from datetime             import datetime

import httpx

from config import settings
from models import AuditResult

logger = logging.getLogger(__name__)


def _html_email_client(result: AuditResult) -> str:
    """Génère le corps HTML de l'email client."""
    s = result.scores
    r = result.report
    couleurs = {"rouge":"#C0392B","orange":"#E67E22","jaune":"#F39C12","vert":"#1E8449"}
    couleur  = couleurs.get(s.couleur_niveau, "#2E75B6")

    return f"""
<!DOCTYPE html><html lang="fr"><head><meta charset="UTF-8"></head>
<body style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;background:#f5f5f5;padding:20px;">

<div style="background:#1F3864;padding:24px;border-radius:8px 8px 0 0;text-align:center;">
  <h1 style="color:#fff;font-size:20px;margin:0;">🛡️ SMD GLOBAL CONSULTING LLC</h1>
  <p style="color:#BDD7EE;margin:6px 0 0;font-size:13px;">Micro-Audit RGPD / EU AI Act</p>
</div>

<div style="background:#fff;padding:28px;border:1px solid #e0e0e0;">
  <p style="font-size:15px;color:#333;">Bonjour {result.input.nom_dirigeant},</p>

  <p style="font-size:14px;color:#555;line-height:1.7;">{r.accroche_email}</p>

  <div style="background:{couleur};color:#fff;padding:20px;border-radius:8px;
              text-align:center;margin:24px 0;">
    <p style="margin:0;font-size:36px;font-weight:800;">{s.score_global} / 100</p>
    <p style="margin:6px 0 0;font-size:14px;opacity:.9;">{s.niveau_conformite}</p>
  </div>

  <p style="font-size:14px;color:#555;line-height:1.7;">{r.resume_executif}</p>

  <div style="background:#f0f4f8;border-left:4px solid #2E75B6;
              padding:16px;margin:20px 0;border-radius:0 6px 6px 0;">
    <p style="margin:0 0 8px;font-weight:700;color:#1F3864;font-size:14px;">
      📋 Vos 3 priorités immédiates :
    </p>
    <p style="margin:4px 0;font-size:13px;color:#444;">1. {r.action_urgente_1}</p>
    <p style="margin:4px 0;font-size:13px;color:#444;">2. {r.action_urgente_2}</p>
    <p style="margin:4px 0;font-size:13px;color:#444;">3. {r.action_urgente_3}</p>
  </div>

  <p style="font-size:14px;color:#555;line-height:1.7;">
    Le rapport PDF complet (plan d'action détaillé, analyse de chaque bloc,
    risques financiers évités) est joint à cet email.
  </p>

  <p style="font-size:14px;color:#333;margin-top:24px;">
    Cordialement,<br>
    <strong>SMD GLOBAL CONSULTING LLC</strong><br>
    {settings.smtp_user}
  </p>
</div>

<div style="background:#1F3864;padding:12px;border-radius:0 0 8px 8px;text-align:center;">
  <p style="color:#BDD7EE;font-size:11px;margin:0;">
    Document confidentiel — usage exclusif de {result.input.nom_entreprise}
    — SMD GLOBAL CONSULTING LLC © {datetime.now().year}
  </p>
</div>

</body></html>"""


def _html_notif_interne(result: AuditResult) -> str:
    """Génère le corps HTML de la notification interne."""
    s = result.scores
    return f"""
<h2>✅ Nouvel audit livré</h2>
<ul>
  <li><strong>Client :</strong> {result.input.nom_entreprise}</li>
  <li><strong>Dirigeant :</strong> {result.input.nom_dirigeant}</li>
  <li><strong>Email :</strong> {result.input.email_client}</li>
  <li><strong>Secteur :</strong> {result.input.secteur}</li>
  <li><strong>Score :</strong> {s.score_global}/100 — {s.niveau_conformite}</li>
  <li><strong>Date :</strong> {result.date_audit}</li>
  <li><strong>PDF :</strong> {result.pdf_url or 'Non généré'}</li>
  <li><strong>Drive :</strong> {result.drive_url or 'Non archivé'}</li>
</ul>"""


async def send_report_email(result: AuditResult, pdf_url: str) -> bool:
    """
    Envoie le rapport PDF au client et une notification interne.
    Retourne True si succès.
    """
    logger.info(f"📧 Envoi email — {result.input.email_client}")

    # Télécharger le PDF depuis PDF.co
    async with httpx.AsyncClient(timeout=60) as client:
        pdf_response = await client.get(pdf_url)
        pdf_response.raise_for_status()
    pdf_bytes = pdf_response.content

    # ─── Email client ────────────────────────────────────────
    msg = MIMEMultipart("mixed")
    msg["From"]    = f"{settings.email_from_name} <{settings.smtp_user}>"
    msg["To"]      = result.input.email_client
    msg["Subject"] = (
        f"🛡️ Votre Rapport Micro-Audit RGPD / IA Act — "
        f"{result.input.nom_entreprise} | Score : {result.scores.score_global}/100"
    )

    # Corps HTML
    msg.attach(MIMEText(_html_email_client(result), "html", "utf-8"))

    # Pièce jointe PDF
    filename = (
        f"Rapport_Audit_RGPD_{result.input.nom_entreprise.replace(' ', '_')}.pdf"
    )
    attachment = MIMEBase("application", "octet-stream")
    attachment.set_payload(pdf_bytes)
    encoders.encode_base64(attachment)
    attachment.add_header("Content-Disposition", f'attachment; filename="{filename}"')
    msg.attach(attachment)

    # ─── Email notification interne ─────────────────────────
    notif = MIMEMultipart("mixed")
    notif["From"]    = f"{settings.email_from_name} <{settings.smtp_user}>"
    notif["To"]      = settings.smtp_user
    notif["Subject"] = (
        f"✅ Audit livré — {result.input.nom_entreprise} | "
        f"{result.scores.score_global}/100 — {result.scores.niveau_conformite}"
    )
    notif.attach(MIMEText(_html_notif_interne(result), "html", "utf-8"))

    # ─── Envoi SMTP ─────────────────────────────────────────
    with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
        server.starttls()
        server.login(settings.smtp_user, settings.smtp_password)
        server.sendmail(settings.smtp_user, result.input.email_client, msg.as_string())
        server.sendmail(settings.smtp_user, settings.smtp_user, notif.as_string())

    logger.info(f"  ✅ Emails envoyés — client : {result.input.email_client}")
    return True
