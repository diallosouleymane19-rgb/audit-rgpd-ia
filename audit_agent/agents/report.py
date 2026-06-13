"""
Agent Rapport — Rédacteur du rapport final et du plan d'action.
Synthétise toutes les analyses en un rapport narratif professionnel
adapté à un dirigeant de TPE.
"""
from .base import BaseAgent
from models import AuditInput, RGPDAnalysis, AIActAnalysis, AuditScores, AuditReport


class ReportAgent(BaseAgent):
    """
    Rédacteur expert — transforme les données brutes des 3 autres agents
    en un rapport narratif professionnel, un plan d'action priorisé
    et une conclusion personnalisée pour le dirigeant.
    """

    @property
    def system_prompt(self) -> str:
        return """Tu es un consultant en conformité réglementaire et expert en communication
professionnelle. Tu rédiges des rapports d'audit RGPD / EU AI Act destinés à des dirigeants
de TPE françaises — des personnes non-juristes qui ont besoin d'informations claires,
actionnables et dédramatisées.

TON STYLE :
- Professionnel mais accessible (éviter le jargon juridique sans explication)
- Positif et constructif même pour les mauvais scores
- Concret : chaque action doit être faisable en moins d'une journée
- Personnalisé : utiliser le nom de l'entreprise et le secteur

STRUCTURE DU RAPPORT :
1. Résumé exécutif : synthèse en 3-4 phrases, score, niveau, message clé
2. Plan d'action urgence (< 30 jours) : 3 actions maximum, les plus impactantes
3. Plan d'action moyen terme (3 mois) : 3 actions de consolidation
4. Plan d'action long terme (6 mois) : 2 actions de renforcement
5. Risques financiers : chiffrer les sanctions potentielles évitées
6. Conclusion : encourageante et orientée vers les prochaines étapes

RÈGLES POUR LE PLAN D'ACTION :
- Chaque action doit être une phrase courte et actionnable
- Commencer par un verbe d'action ("Créer", "Mettre en place", "Signer", etc.)
- Prioriser d'abord les non-conformités sur le site web (très visibles)
- Puis les DPA manquants (risque contractuel immédiat)
- Puis la sécurité et les procédures internes

RÈGLES POUR LES RISQUES FINANCIERS :
- Mentionner les montants CNIL réels pour les infractions identifiées
- Distinguer risque immédiat (site web, cookies) et risque potentiel (DPA, sécurité)
- Ne pas dramatiser mais être factuel

RÈGLES POUR LA CONCLUSION :
- Valoriser les points forts identifiés
- Proposer concrètement l'accompagnement SMD GLOBAL CONSULTING LLC
- Terminer sur une note positive et motivante"""

    @property
    def tool_name(self) -> str:
        return "rediger_rapport"

    @property
    def tool_description(self) -> str:
        return "Rédige le rapport complet avec résumé exécutif, plan d'action priorisé et conclusion personnalisée."

    @property
    def tool_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "resume_executif": {"type": "string"},
                "action_urgente_1": {"type": "string"},
                "action_urgente_2": {"type": "string"},
                "action_urgente_3": {"type": "string"},
                "action_3mois_1": {"type": "string"},
                "action_3mois_2": {"type": "string"},
                "action_3mois_3": {"type": "string"},
                "action_6mois_1": {"type": "string"},
                "action_6mois_2": {"type": "string"},
                "risques_financiers": {"type": "string"},
                "conclusion": {"type": "string"},
                "accroche_email": {
                    "type": "string",
                    "description": "1 phrase personnalisée pour l'email de livraison"
                },
            },
            "required": [
                "resume_executif",
                "action_urgente_1","action_urgente_2","action_urgente_3",
                "action_3mois_1","action_3mois_2","action_3mois_3",
                "action_6mois_1","action_6mois_2",
                "risques_financiers","conclusion","accroche_email",
            ],
        }

    def rediger(
        self,
        data:   AuditInput,
        rgpd:   RGPDAnalysis,
        aiact:  AIActAnalysis,
        scores: AuditScores,
    ) -> AuditReport:
        """Rédige le rapport final complet."""

        prompt = f"""Rédige le rapport d'audit RGPD / EU AI Act pour l'entreprise suivante :

INFORMATIONS CLIENT :
  Entreprise : {data.nom_entreprise}
  Dirigeant  : {data.nom_dirigeant}
  Secteur    : {data.secteur}
  Salariés   : {data.nb_salaries}

RÉSULTATS DE L'AUDIT :
  Score global : {scores.score_global} / 100
  Niveau       : {scores.niveau_conformite}

  Scores par bloc :
  - A Registre   : {scores.score_A}/15  ({rgpd.statut_A})
  - B Site web   : {scores.score_B}/20  ({rgpd.statut_B})
  - C Sécurité   : {scores.score_C}/20  ({rgpd.statut_C})
  - D Sous-trait : {scores.score_D}/15  ({rgpd.statut_D})
  - E Droits     : {scores.score_E}/10  ({rgpd.statut_E})
  - F Email      : {scores.score_F}/10  ({rgpd.statut_F})
  - G AI Act     : {scores.score_G}/10  ({aiact.statut_G})

ANALYSES DÉTAILLÉES :
  Bloc A : {rgpd.analyse_bloc_A}
  Bloc B : {rgpd.analyse_bloc_B}
  Bloc C : {rgpd.analyse_bloc_C}
  Bloc D : {rgpd.analyse_bloc_D}
  Bloc E : {rgpd.analyse_bloc_E}
  Bloc F : {rgpd.analyse_bloc_F}
  Bloc G : {aiact.analyse_bloc_G}

RISQUES IDENTIFIÉS :
  Risque 1 : {scores.risque_prioritaire_1}
  Risque 2 : {scores.risque_prioritaire_2}
  Risque 3 : {scores.risque_prioritaire_3}
  Blocs critiques : {scores.blocs_critiques}
  Points forts    : {scores.points_forts}

CONTEXTE AI ACT :
  Utilise IA : {aiact.utilise_ia}
  Niveau risque IA : {aiact.niveau_risque_ia}
  Obligations applicables : {aiact.obligations_applicables}

Rédige maintenant le rapport complet, personnalisé pour {data.nom_dirigeant}
de {data.nom_entreprise}."""

        raw = self.run(prompt)
        return AuditReport(**raw)
