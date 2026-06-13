"""
Service Notion — Persistance des audits dans la base Notion.
Crée une page par audit dans la base de données prospects/clients.
"""
import httpx
import logging
from models import AuditResult
from config import settings

logger = logging.getLogger(__name__)

NOTION_BASE = "https://api.notion.com/v1"
HEADERS = {
    "Authorization": f"Bearer {settings.notion_token}",
    "Content-Type":  "application/json",
    "Notion-Version": "2022-06-28",
}


def _rich_text(text: str) -> list[dict]:
    """Raccourci pour créer un rich_text Notion."""
    return [{"type": "text", "text": {"content": str(text)[:2000]}}]


def _build_properties(result: AuditResult) -> dict:
    """
    Construit les propriétés Notion pour la page d'audit.
    Adapte automatiquement selon les champs disponibles dans la base.
    """
    s = result.scores
    r = result.report

    return {
        # Titre de la page
        "Entreprise": {
            "title": _rich_text(result.input.nom_entreprise)
        },
        # Infos client
        "Dirigeant": {
            "rich_text": _rich_text(result.input.nom_dirigeant)
        },
        "Email": {
            "email": result.input.email_client
        },
        "Secteur": {
            "rich_text": _rich_text(result.input.secteur)
        },
        "Salariés": {
            "number": result.input.nb_salaries
        },
        # Résultats audit
        "Score global": {
            "number": s.score_global
        },
        "Niveau": {
            "select": {"name": s.niveau_conformite}
        },
        "Date audit": {
            "date": {"start": result.date_audit_iso}
        },
        # Scores par bloc
        "Score A": {"number": s.score_A},
        "Score B": {"number": s.score_B},
        "Score C": {"number": s.score_C},
        "Score D": {"number": s.score_D},
        "Score E": {"number": s.score_E},
        "Score F": {"number": s.score_F},
        "Score G": {"number": s.score_G},
        # URLs
        "PDF URL": {
            "url": result.pdf_url or None
        },
        "Drive URL": {
            "url": result.drive_url or None
        },
        # Statut pipeline
        "Statut": {
            "select": {"name": "Audit livré"}
        },
        # Résumé
        "Résumé exécutif": {
            "rich_text": _rich_text(r.resume_executif)
        },
        "Action urgente 1": {
            "rich_text": _rich_text(r.action_urgente_1)
        },
        "Risques financiers": {
            "rich_text": _rich_text(r.risques_financiers)
        },
    }


async def save_audit_to_notion(result: AuditResult) -> str | None:
    """
    Crée ou met à jour la page d'audit dans Notion.
    Retourne l'ID de la page Notion créée, ou None en cas d'erreur.
    """
    logger.info(f"📔 Notion — Sauvegarde audit {result.input.nom_entreprise}")

    # Construire le body de la page
    body = {
        "parent": {"database_id": settings.notion_db_id},
        "properties": _build_properties(result),
        "children": [
            # Section Plan d'action
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": _rich_text("📋 Plan d'action")
                }
            },
            {
                "object": "block",
                "type": "heading_3",
                "heading_3": {"rich_text": _rich_text("⚡ Actions urgentes (< 30 jours)")}
            },
            {
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {"rich_text": _rich_text(result.report.action_urgente_1)}
            },
            {
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {"rich_text": _rich_text(result.report.action_urgente_2)}
            },
            {
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {"rich_text": _rich_text(result.report.action_urgente_3)}
            },
            {
                "object": "block",
                "type": "heading_3",
                "heading_3": {"rich_text": _rich_text("📅 Actions 3 mois")}
            },
            {
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {"rich_text": _rich_text(result.report.action_3mois_1)}
            },
            {
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {"rich_text": _rich_text(result.report.action_3mois_2)}
            },
            {
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {"rich_text": _rich_text(result.report.action_3mois_3)}
            },
            # Section Conclusion
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {"rich_text": _rich_text("🏁 Conclusion")}
            },
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {"rich_text": _rich_text(result.report.conclusion)}
            },
        ]
    }

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            f"{NOTION_BASE}/pages",
            json=body,
            headers=HEADERS,
        )

    if response.status_code not in (200, 201):
        logger.error(f"  ❌ Notion error {response.status_code} — {response.text[:200]}")
        return None

    page_id = response.json().get("id", "")
    logger.info(f"  ✅ Page Notion créée — ID : {page_id}")
    return page_id


async def update_audit_notion_page(page_id: str, updates: dict) -> bool:
    """
    Met à jour une page Notion existante (ex: ajouter l'URL PDF après génération).
    updates = {"PDF URL": {"url": "https://..."}}
    """
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.patch(
            f"{NOTION_BASE}/pages/{page_id}",
            json={"properties": updates},
            headers=HEADERS,
        )
    return response.status_code in (200, 201)
