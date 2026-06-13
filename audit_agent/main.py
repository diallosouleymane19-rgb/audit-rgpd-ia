"""
SMD GLOBAL CONSULTING LLC
Micro-Audits RGPD / EU AI Act pour TPE — API FastAPI
======================================================
Endpoints :
  POST /webhook/tally   ← Reçoit le formulaire Tally (Make.com)
  POST /audit           ← Déclenche un audit direct (tests / Make.com)
  GET  /health          ← Health check (Render.com, monitoring)
  GET  /                ← Bienvenue
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

# ─── Logging ───────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("main")


# ─── App lifecycle ─────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 SMD GLOBAL CONSULTING LLC — Audit RGPD/IA démarré")
    logger.info(f"   Modèle Claude : {settings.claude_model}")
    yield
    logger.info("🛑 Arrêt de l'API")


# ─── FastAPI ────────────────────────────────────────────────────────────────
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
    allow_origins=["*"],  # Restreindre en production
    allow_methods=["*"],
    allow_headers=["*"],
)

# Orchestrateur singleton (initialisé une fois au démarrage)
orchestrator = AuditOrchestrator()


# ═══════════════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════════════

def _parse_tally_payload(payload: dict) -> AuditInput:
    """
    Parse le payload Tally (webhook Make.com).
    Tally envoie les réponses dans payload["data"]["fields"] avec
    {"key": "question_id", "value": "OUI"} ou une liste de valeurs.
    """
    fields = {}
    for field in payload.get("data", {}).get("fields", []):
        key   = field.get("key", "")
        value = field.get("value", "")
        # Normaliser les valeurs multiples en string
        if isinstance(value, list):
            value = value[0] if value else ""
        fields[key] = str(value).strip().upper()

    # Mapping Tally field ID → AuditInput fields
    # (À adapter selon les IDs réels du formulaire Tally)
    return AuditInput(
        nom_entreprise = fields.get("nom_entreprise", ""),
        nom_dirigeant  = fields.get("nom_dirigeant", ""),
        email_client   = fields.get("email_client", ""),
        secteur        = fields.get("secteur", ""),
        nb_salaries    = int(fields.get("nb_salaries", "1") or 1),

        # Bloc A — Registre des traitements
        A1=fields.get("A1","NON"), A2=fields.get("A2","NON"), A3=fields.get("A3","NON"),

        # Bloc B — Site web / Cookies
        B1=fields.get("B1","NON"), B2=fields.get("B2","NON"), B3=fields.get("B3","NON"),
        B4=fields.get("B4","NON"),

        # Bloc C — Sécurité des données
        C1=fields.get("C1","NON"), C2=fields.get("C2","NON"), C3=fields.get("C3","NON"),
        C4=fields.get("C4","NON"),

        # Bloc D — Sous-traitants
        D1=fields.get("D1","NON"), D2=fields.get("D2","NON"), D3=fields.get("D3","NON"),

        # Bloc E — Droits des personnes
        E1=fields.get("E1","NON"), E2=fields.get("E2","NON"),

        # Bloc F — Email marketing
        F1=fields.get("F1","NON"), F2=fields.get("F2","NON"),

        # Bloc G — EU AI Act
        G1=fields.get("G1","NON"), G2=fields.get("G2","NON"), G3=fields.get("G3","NON"),
        G4=fields.get("G4","NON"),
    )


async def _run_full_pipeline(data: AuditInput) -> AuditResult:
    """
    Pipeline complet :
    1. Audit multi-agents (RGPD + AI Act + Scoring + Rapport)
    2. Génération PDF via PDF.co
    3. Sauvegarde Notion
    4. Envoi email client + notification interne
    """
    # Étape 1 — Audit
    result = await orchestrator.run(data)
    logger.info(f"✅ Audit OK — {data.nom_entreprise} | {result.scores.score_global}/100")

    # Étape 2 — PDF
    try:
        pdf_url = await generate_pdf(result)
        result.pdf_url = pdf_url
        result.statut  = "generated"
    except Exception as e:
        logger.error(f"❌ Erreur PDF.co : {e}")
        pdf_url = None

    # Étape 3 — Notion
    try:
        notion_id = await save_audit_to_notion(result)
        if notion_id:
            result.notion_page_id = notion_id
    except Exception as e:
        logger.error(f"❌ Erreur Notion : {e}")

    # Étape 4 — Email
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
        "service":  "SMD GLOBAL CONSULTING LLC — Audit RGPD/IA",
        "version":  "1.0.0",
        "status":   "running",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/health", tags=["Info"])
async def health():
    """Health check pour Render.com et uptime monitors."""
    return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}


@app.post("/webhook/tally", tags=["Webhooks"], status_code=status.HTTP_202_ACCEPTED)
async def webhook_tally(request: Request, background_tasks: BackgroundTasks):
    """
    Webhook Make.com ← Tally.
    Accepte le payload Tally, parse les réponses du formulaire,
    déclenche le pipeline en arrière-plan et retourne immédiatement 202.
    """
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

    # Lancer le pipeline en background (réponse immédiate à Tally)
    background_tasks.add_task(_run_full_pipeline, data)

    return {
        "status":  "accepted",
        "message": f"Audit en cours pour {data.nom_entreprise}",
        "email":   data.email_client,
    }


@app.post("/audit", tags=["Audit"], response_model=dict)
async def run_audit(data: AuditInput):
    """
    Lance un audit complet (endpoint synchrone pour tests et Make.com direct).
    Retourne le résultat complet JSON après ~20-30 secondes.

    Body JSON : AuditInput (25 questions A1–G4 + 5 champs client)
    """
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
            "A": result.scores.score_A,
            "B": result.scores.score_B,
            "C": result.scores.score_C,
            "D": result.scores.score_D,
            "E": result.scores.score_E,
            "F": result.scores.score_F,
            "G": result.scores.score_G,
        },
    }


# ─── Démarrage local ───────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.port,
        reload=settings.debug,
        log_level="debug" if settings.debug else "info",
    )

