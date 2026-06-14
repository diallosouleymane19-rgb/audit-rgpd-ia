"""
SMD GLOBAL CONSULTING LLC
Micro-Audits RGPD / EU AI Act pour TPE — API FastAPI
"""
import logging
import asyncio
from datetime import datetime, timezone
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config import settings
from models import AuditInput, AuditResult
from orchestrator import AuditOrchestrator
from services.pdf    import generate_pdf
from services.email  import send_report_email
from services.notion import save_audit_to_notion, update_audit_notion_page

logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 SMD GLOBAL CONSULTING LLC — Audit RGPD/IA démarré")
    logger.info(f"   Modèle Claude : {settings.claude_model}")
    yield
    logger.info("🛑 Arrêt de l'API")


app = FastAPI(
    title="SMD GLOBAL — Audit RGPD/IA",
    description=(
        "Micro-Audits de Conformité RGPD / EU AI Act pour TPE françaises. "
        "Système multi-agents Claude automatisé."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

orchestrator = AuditOrchestrator()


# ═══════════════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════════════

def _parse_tally_payload(payload: dict) -> AuditInput:
    """
    Parse le payload Tally (webhook Make.com).
    Gère les deux formats :
      - Payload complet : {"data": {"fields": [...]}}
      - Objet data seul (Make.com {{1.data}}) : {"fields": [...]}
    Mappe par label de question (pas par ID auto-généré).
    """
    label_map: dict[str, str] = {}

    # Détection du format reçu
    if "fields" in payload:
        fields_list = payload.get("fields", [])
    else:
        fields_list = payload.get("data", {}).get("fields", [])

    for field in fields_list:
        raw_label = (field.get("label") or field.get("title") or "").strip()
        value = field.get("value", "")
        if isinstance(value, list):
            value = value[0] if value else ""
        if isinstance(value, (int, float)):
            value = str(int(value))
        label_map[raw_label.lower()] = str(value).strip()

    def find_oui_non(prefix: str) -> str:
        p = prefix.lower()
        for label, val in label_map.items():
            if label.startswith(p + " ") or label.startswith(p + ":") or label == p:
                v = val.upper()
                if v in ("OUI", "NON", "PARTIEL", "NA"):
                    return v
                if "OUI" in v:
                    return "OUI"
                return "NON"
        return "NON"

    def find_text(keywords: list, default: str = "") -> str:
        for kw in keywords:
            kw_low = kw.lower()
            for label, val in label_map.items():
                if kw_low in label and val:
                    return val
        return default

    return AuditInput(
        nom_entreprise = find_text(["nom de l'entreprise", "nom entreprise", "entreprise"], ""),
        nom_dirigeant  = find_text(["dirigeant", "prénom", "responsable", "gérant"], ""),
        email_client   = find_text(["email", "e-mail", "courriel", "mail"], ""),
        secteur        = find_text(["secteur", "activité"], ""),
        nb_salaries    = find_text(["salari", "nombre de salar", "employé"], "1") or "1",

        rep_A1 = find_oui_non("a1"), rep_A2 = find_oui_non("a2"),
        rep_A3 = find_oui_non("a3"), rep_A4 = find_oui_non("a4"),
        rep_B1 = find_oui_non("b1"), rep_B2 = find_oui_non("b2"),
        rep_B3 = find_oui_non("b3"), rep_B4 = find_oui_non("b4"),
        rep_B5 = find_oui_non("b5"),
        rep_C1 = find_oui_non("c1"), rep_C2 = find_oui_non("c2"),
        rep_C3 = find_oui_non("c3"), rep_C4 = find_oui_non("c4"),
        rep_D1 = find_oui_non("d1"), rep_D2 = find_oui_non("d2"),
        rep_D3 = find_oui_non("d3"), rep_D4 = find_oui_non("d4"),
        rep_E1 = find_oui_non("e1"), rep_E2 = find_oui_non("e2"),
        rep_F1 = find_oui_non("f1"), rep_F2 = find_oui_non("f2"),
        rep_G1 = find_oui_non("g1"), rep_G2 = find_oui_non("g2"),
        rep_G3 = find_oui_non("g3"), rep_G4 = find_oui_non("g4"),
    )


async def _run_full_pipeline(data: AuditInput) -> AuditResult:
    result = await orchestrator.run(data)
    logger.info(f"✅ Audit OK — {data.nom_entreprise} | {result.scores.score_global}/100")

    try:
        pdf_url = await generate_pdf(result)
        result.pdf_url = pdf_url
        result.statut  = "generated"
    except Exception as e:
        logger.error(f"❌ Erreur PDF.co : {e}")
        pdf_url = None

    try:
        notion_id = await save_audit_to_notion(result)
        if notion_id:
            result.notion_page_id = notion_id
    except Exception as e:
        logger.error(f"❌ Erreur Notion : {e}")

    if pdf_url:
        try:
            await send_report_email(result, pdf_url)
            result.statut = "delivered"
        except Exception as e:
            logger.error(f"❌ Erreur email : {e}")

    return result


# ═══════════════════════════════════════════════════════════════════════════
# ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════

@app.get("/", tags=["Info"])
async def root():
    return {
        "service":   "SMD GLOBAL CONSULTING LLC — Audit RGPD/IA",
        "version":   "1.0.0",
        "status":    "running",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/health", tags=["Info"])
async def health():
    return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}


@app.post("/webhook/tally", tags=["Webhooks"], status_code=status.HTTP_202_ACCEPTED)
async def webhook_tally(request: Request, background_tasks: BackgroundTasks):
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Payload JSON invalide")

    try:
        data = _parse_tally_payload(payload)
    except Exception as e:
        logger.error(f"❌ Parse Tally : {e}")
        raise HTTPException(status_code=422, detail=f"Données formulaire invalides : {e}")

    logger.info(f"📥 Webhook Tally — {data.nom_entreprise} <{data.email_client}>")
    background_tasks.add_task(_run_full_pipeline, data)

    return {
        "status":  "accepted",
        "message": f"Audit en cours pour {data.nom_entreprise}",
        "email":   data.email_client,
    }


@app.post("/audit", tags=["Audit"], response_model=dict)
async def run_audit(data: AuditInput):
    logger.info(f"🔍 Audit direct — {data.nom_entreprise}")
    result = await _run_full_pipeline(data)
    return {
        "statut":          result.statut,
        "nom_entreprise":  data.nom_entreprise,
        "score_global":    result.scores.score_global,
        "niveau":          result.scores.niveau_conformite,
        "date_audit":      result.date_audit,
        "pdf_url":         result.pdf_url,
        "notion_page_id":  result.notion_page_id,
        "resume_executif": result.report.resume_executif,
        "actions_urgentes": [
            result.report.action_urgente_1,
            result.report.action_urgente_2,
            result.report.action_urgente_3,
        ],
        "scores": {
            "A": result.scores.score_A, "B": result.scores.score_B,
            "C": result.scores.score_C, "D": result.scores.score_D,
            "E": result.scores.score_E, "F": result.scores.score_F,
            "G": result.scores.score_G,
        },
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.port,
        reload=settings.debug,
        log_level="debug" if settings.debug else "info",
    )
