"""
Service PDF — Génération du rapport PDF via PDF.co.
Injecte les variables du rapport dans le template Word,
convertit en PDF et retourne l'URL de téléchargement.
"""
import httpx
import logging
from models import AuditInput, AuditResult
from config import settings

logger = logging.getLogger(__name__)

PDFCO_ENDPOINT = "https://api.pdf.co/v1/pdf/convert/from/doc"


def _build_macros(data: AuditInput, result: AuditResult) -> list[dict]:
    """Construit la liste des macros {key, value} pour PDF.co."""
    s = result.scores
    r = result.rgpd
    a = result.aiact
    rp = result.report

    return [
        {"key": "nom_entreprise",    "value": data.nom_entreprise},
        {"key": "nom_dirigeant",     "value": data.nom_dirigeant},
        {"key": "date_audit",        "value": result.date_audit},
        {"key": "secteur",           "value": data.secteur},
        {"key": "score_global",      "value": str(s.score_global)},
        {"key": "niveau_conformite", "value": s.niveau_conformite},
        # Scores par bloc
        {"key": "score_A",  "value": str(s.score_A)},
        {"key": "score_B",  "value": str(s.score_B)},
        {"key": "score_C",  "value": str(s.score_C)},
        {"key": "score_D",  "value": str(s.score_D)},
        {"key": "score_E",  "value": str(s.score_E)},
        {"key": "score_F",  "value": str(s.score_F)},
        {"key": "score_G",  "value": str(s.score_G)},
        # Statuts par bloc
        {"key": "statut_A", "value": r.statut_A},
        {"key": "statut_B", "value": r.statut_B},
        {"key": "statut_C", "value": r.statut_C},
        {"key": "statut_D", "value": r.statut_D},
        {"key": "statut_E", "value": r.statut_E},
        {"key": "statut_F", "value": r.statut_F},
        {"key": "statut_G", "value": a.statut_G},
        # Analyses par bloc
        {"key": "analyse_bloc_A", "value": r.analyse_bloc_A},
        {"key": "analyse_bloc_B", "value": r.analyse_bloc_B},
        {"key": "analyse_bloc_C", "value": r.analyse_bloc_C},
        {"key": "analyse_bloc_D", "value": r.analyse_bloc_D},
        {"key": "analyse_bloc_E", "value": r.analyse_bloc_E},
        {"key": "analyse_bloc_F", "value": r.analyse_bloc_F},
        {"key": "analyse_bloc_G", "value": a.analyse_bloc_G},
        # Plan d'action
        {"key": "action_urgente_1", "value": rp.action_urgente_1},
        {"key": "action_urgente_2", "value": rp.action_urgente_2},
        {"key": "action_urgente_3", "value": rp.action_urgente_3},
        {"key": "action_3mois_1",   "value": rp.action_3mois_1},
        {"key": "action_3mois_2",   "value": rp.action_3mois_2},
        {"key": "action_3mois_3",   "value": rp.action_3mois_3},
        {"key": "action_6mois_1",   "value": rp.action_6mois_1},
        {"key": "action_6mois_2",   "value": rp.action_6mois_2},
        # Synthèse
        {"key": "risques_financiers", "value": rp.risques_financiers},
        {"key": "conclusion",         "value": rp.conclusion},
    ]


async def generate_pdf(result: AuditResult) -> str:
    """
    Génère le PDF via PDF.co et retourne l'URL de téléchargement.
    Raises: httpx.HTTPError si l'API échoue.
    """
    data = result.input
    filename = (
        f"Rapport_Audit_RGPD_{data.nom_entreprise.replace(' ', '_')}"
        f"_{result.date_audit.replace('/', '')}.pdf"
    )

    payload = {
        "url":    settings.google_drive_template_url,
        "name":   filename,
        "async":  False,
        "macros": _build_macros(data, result),
    }

    logger.info(f"📄 Génération PDF — {filename}")
    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(
            PDFCO_ENDPOINT,
            json=payload,
            headers={
                "x-api-key":    settings.pdfco_api_key,
                "Content-Type": "application/json",
            },
        )
        response.raise_for_status()

    resp_json = response.json()
    if resp_json.get("error"):
        raise ValueError(f"PDF.co error: {resp_json.get('message', 'Unknown error')}")

    pdf_url = resp_json["url"]
    logger.info(f"  ✅ PDF généré : {pdf_url}")
    return pdf_url
