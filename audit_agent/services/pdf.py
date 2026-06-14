"""
Service PDF — Génération du rapport PDF via PDF.co.
Upload le template sur PDF.co puis convertit en PDF avec injection des variables.
"""
import httpx
import logging
from models import AuditInput, AuditResult
from config import settings

logger = logging.getLogger(__name__)

PDFCO_BASE = "https://api.pdf.co/v1"
PDFCO_ENDPOINT = f"{PDFCO_BASE}/pdf/convert/from/doc"


async def _upload_template_to_pdfco() -> str:
    """
    Télécharge le template .docx depuis GitHub et l'uploade sur PDF.co.
    Retourne l'URL hébergée sur PDF.co (valide 1h).
    """
    async with httpx.AsyncClient(timeout=60) as client:
        # Étape 1 : obtenir une URL présignée PDF.co
        resp = await client.get(
            f"{PDFCO_BASE}/file/upload/get-presigned-url",
            params={
                "name": "template_audit.docx",
                "contenttype": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            },
            headers={"x-api-key": settings.pdfco_api_key}
        )
        resp.raise_for_status()
        presigned_data = resp.json()
        if presigned_data.get("error"):
            raise ValueError(f"PDF.co presign error: {presigned_data.get('message')}")
        upload_url = presigned_data["presignedUrl"]
        file_url   = presigned_data["url"]
        logger.info(f"  📤 URL présignée obtenue : {file_url}")

        # Étape 2 : télécharger le template depuis GitHub
        template_resp = await client.get(settings.google_drive_template_url)
        template_resp.raise_for_status()
        logger.info(f"  📥 Template téléchargé ({len(template_resp.content)} octets)")

        # Étape 3 : uploader vers PDF.co
        put_resp = await client.put(
            upload_url,
            content=template_resp.content,
            headers={
                "content-type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            }
        )
        put_resp.raise_for_status()
        logger.info(f"  ✅ Template uploadé sur PDF.co")

    return file_url


def _build_macros(data: AuditInput, result: AuditResult) -> list[dict]:
    """Construit la liste des macros {name, value} pour PDF.co."""
    s  = result.scores
    r  = result.rgpd
    a  = result.aiact
    rp = result.report

    return [
        {"name": "nom_entreprise",            "value": data.nom_entreprise},
        {"name": "nom_dirigeant",             "value": data.nom_dirigeant},
        {"name": "date_audit",                "value": result.date_audit},
        {"name": "secteur",                   "value": data.secteur},
        {"name": "nb_salaries",               "value": str(data.nb_salaries)},
        {"name": "ville",                     "value": ""},
        {"name": "score_global",              "value": str(s.score_global)},
        {"name": "niveau_conformite",         "value": s.niveau_conformite},
        {"name": "introduction_personnalisee","value": rp.resume_executif},
        {"name": "resume_executif",           "value": rp.resume_executif},
        {"name": "score_A",  "value": str(s.score_A)},
        {"name": "score_B",  "value": str(s.score_B)},
        {"name": "score_C",  "value": str(s.score_C)},
        {"name": "score_D",  "value": str(s.score_D)},
        {"name": "score_E",  "value": str(s.score_E)},
        {"name": "score_F",  "value": str(s.score_F)},
        {"name": "score_G",  "value": str(s.score_G)},
        {"name": "statut_A", "value": r.statut_A},
        {"name": "statut_B", "value": r.statut_B},
        {"name": "statut_C", "value": r.statut_C},
        {"name": "statut_D", "value": r.statut_D},
        {"name": "statut_E", "value": r.statut_E},
        {"name": "statut_F", "value": r.statut_F},
        {"name": "statut_G", "value": a.statut_G},
        {"name": "analyse_bloc_A", "value": r.analyse_bloc_A},
        {"name": "analyse_bloc_B", "value": r.analyse_bloc_B},
        {"name": "analyse_bloc_C", "value": r.analyse_bloc_C},
        {"name": "analyse_bloc_D", "value": r.analyse_bloc_D},
        {"name": "analyse_bloc_E", "value": r.analyse_bloc_E},
        {"name": "analyse_bloc_F", "value": r.analyse_bloc_F},
        {"name": "analyse_bloc_G", "value": a.analyse_bloc_G},
        {"name": "action_urgente_1", "value": rp.action_urgente_1},
        {"name": "action_urgente_2", "value": rp.action_urgente_2},
        {"name": "action_urgente_3", "value": rp.action_urgente_3},
        {"name": "action_3mois_1",   "value": rp.action_3mois_1},
        {"name": "action_3mois_2",   "value": rp.action_3mois_2},
        {"name": "action_3mois_3",   "value": rp.action_3mois_3},
        {"name": "action_6mois_1",   "value": rp.action_6mois_1},
        {"name": "action_6mois_2",   "value": rp.action_6mois_2},
        {"name": "risques_financiers","value": rp.risques_financiers},
        {"name": "conclusion",        "value": rp.conclusion},
    ]


async def generate_pdf(result: AuditResult) -> str:
    """
    1. Upload le template sur PDF.co
    2. Génère le PDF avec injection des variables
    3. Retourne l'URL de téléchargement
    """
    data = result.input
    filename = (
        f"Rapport_Audit_RGPD_{data.nom_entreprise.replace(' ', '_')}"
        f"_{result.date_audit.replace('/', '')}.pdf"
    )

    logger.info(f"📄 Génération PDF — {filename}")

    # Upload le template sur PDF.co
    template_url = await _upload_template_to_pdfco()

    payload = {
        "url":    template_url,
        "name":   filename,
        "async":  False,
        "macros": _build_macros(data, result),
    }

    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(
            PDFCO_ENDPOINT,
            json=payload,
            headers={
                "x-api-key":    settings.pdfco_api_key,
                "Content-Type": "application/json",
            },
        )

    if response.status_code != 200:
        logger.error(f"  ❌ PDF.co {response.status_code} — {response.text[:500]}")
        response.raise_for_status()

    resp_json = response.json()
    if resp_json.get("error"):
        logger.error(f"  ❌ PDF.co error : {resp_json}")
        raise ValueError(f"PDF.co error: {resp_json.get('message', 'Unknown error')}")

    pdf_url = resp_json["url"]
    logger.info(f"  ✅ PDF généré : {pdf_url}")
    return pdf_url
