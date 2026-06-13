"""
Orchestrateur — Chef d'orchestre des 4 agents.
Exécute les agents en parallèle quand possible, puis en séquence.

Pipeline :
  [Agent RGPD] ─┐
                 ├─→ [Agent Scoring] ─→ [Agent Rapport] ─→ AuditResult
  [Agent AIAct] ─┘

Agents RGPD et AI Act tournent en parallèle (asyncio.gather).
Agent Scoring attend les deux résultats.
Agent Rapport attend le Scoring.
"""
import asyncio
import logging
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor

import anthropic

from config import settings
from models import AuditInput, AuditResult
from agents.rgpd    import RGPDAgent
from agents.aiact   import AIActAgent
from agents.scoring import ScoringAgent
from agents.report  import ReportAgent

logger = logging.getLogger(__name__)


class AuditOrchestrator:
    """
    Orchestre les 4 agents Claude pour produire un audit complet.
    Utilise un ThreadPoolExecutor pour le parallélisme (API calls synchrones).
    """

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        self.rgpd_agent    = RGPDAgent(self.client)
        self.aiact_agent   = AIActAgent(self.client)
        self.scoring_agent = ScoringAgent(self.client)
        self.report_agent  = ReportAgent(self.client)

    async def run(self, data: AuditInput) -> AuditResult:
        """
        Exécute le pipeline complet en ~15-20 secondes.
        Étape 1 (parallèle) : Agent RGPD + Agent AI Act
        Étape 2 (séquentiel) : Agent Scoring
        Étape 3 (séquentiel) : Agent Rapport
        """
        logger.info(f"🚀 Démarrage audit — {data.nom_entreprise}")
        start = datetime.now()

        # ─── Étape 1 : RGPD + AI Act en parallèle ───────────────
        logger.info("📋 Étape 1/3 — Agents RGPD + AI Act (parallèle)…")
        loop = asyncio.get_event_loop()

        with ThreadPoolExecutor(max_workers=2) as executor:
            future_rgpd  = loop.run_in_executor(executor, self.rgpd_agent.analyse,  data)
            future_aiact = loop.run_in_executor(executor, self.aiact_agent.analyse, data)
            rgpd_result, aiact_result = await asyncio.gather(future_rgpd, future_aiact)

        logger.info(f"  ✅ RGPD — Score blocs A-F : {rgpd_result.score_A}+{rgpd_result.score_B}+{rgpd_result.score_C}+{rgpd_result.score_D}+{rgpd_result.score_E}+{rgpd_result.score_F}")
        logger.info(f"  ✅ AI Act — Score bloc G : {aiact_result.score_G}/10")

        # ─── Étape 2 : Scoring ───────────────────────────────────
        logger.info("🧮 Étape 2/3 — Agent Scoring…")
        scores = await loop.run_in_executor(
            None, self.scoring_agent.consolider, rgpd_result, aiact_result
        )
        logger.info(f"  ✅ Score global : {scores.score_global}/100 — {scores.niveau_conformite}")

        # ─── Étape 3 : Rapport ───────────────────────────────────
        logger.info("📝 Étape 3/3 — Agent Rapport…")
        report = await loop.run_in_executor(
            None, self.report_agent.rediger, data, rgpd_result, aiact_result, scores
        )
        logger.info(f"  ✅ Rapport rédigé — {len(report.resume_executif)} caractères dans le résumé")

        # ─── Consolidation ───────────────────────────────────────
        elapsed = (datetime.now() - start).total_seconds()
        logger.info(f"✅ Audit terminé en {elapsed:.1f}s — {data.nom_entreprise} | {scores.score_global}/100")

        now = datetime.now(timezone.utc)
        return AuditResult(
            input=data,
            rgpd=rgpd_result,
            aiact=aiact_result,
            scores=scores,
            report=report,
            date_audit=now.strftime("%d/%m/%Y"),
            date_audit_iso=now.strftime("%Y-%m-%d"),
            statut="analysed",
        )

    def run_sync(self, data: AuditInput) -> AuditResult:
        """Version synchrone pour les tests et Make.com."""
        return asyncio.run(self.run(data))
