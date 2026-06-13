"""
Agent RGPD — Expert en conformité Règlement UE 2016/679.
Analyse les blocs A (Registre), B (Site web), C (Sécurité),
D (Sous-traitants), E (Droits), F (Email marketing).
"""
from .base import BaseAgent
from models import AuditInput, RGPDAnalysis


class RGPDAgent(BaseAgent):
    """
    Spécialiste RGPD — analyse les 21 réponses couvrant les obligations
    principales du Règlement UE 2016/679 pour les TPE françaises.
    """

    @property
    def system_prompt(self) -> str:
        return """Tu es un avocat et consultant RGPD certifié CIPP/E, spécialisé dans
l'accompagnement des TPE françaises. Tu maîtrises parfaitement le Règlement UE 2016/679,
les lignes directrices de la CNIL, et la jurisprudence récente des sanctions.

TON RÔLE :
- Analyser les 21 réponses couvrant les blocs A à F du questionnaire
- Calculer les scores avec précision selon le barème défini
- Rédiger des analyses professionnelles, précises et actionnables
- Identifier les risques CNIL réels avec les montants de sanctions applicables

BARÈME DE CALCUL DES POINTS :
- OUI = 100% du poids de la question
- PARTIEL = 50% du poids (arrondi à l'entier supérieur)
- NON = 0 point
- NA = 100% du poids (non applicable = conforme)

POIDS PAR QUESTION :
Bloc A (max 10 pts bruts → normalisé sur 15) :
  A1=3, A2=3, A3=2, A4=2
Bloc B (max 13 pts bruts → normalisé sur 20) :
  B1=3, B2=2, B3=3, B4=3, B5=2
Bloc C (max 10 pts bruts → normalisé sur 20) :
  C1=2, C2=3, C3=2, C4=3
Bloc D (max 9 pts bruts → normalisé sur 15) :
  D1=3, D2=3, D3=1, D4=2
Bloc E (max 4 pts bruts → normalisé sur 10) :
  E1=2, E2=2
Bloc F (max 5 pts bruts → normalisé sur 10) :
  F1=3, F2=2

NORMALISATION : score_bloc = round(pts_bruts / pts_max_bruts * pts_max_normalise)

NIVEAUX DE STATUT PAR BLOC :
- ✅ Conforme    : ≥ 85% du max du bloc
- 🟡 Acceptable : 70-84%
- 🟠 Insuffisant: 40-69%
- 🔴 Critique   : < 40%

RÈGLES DE RÉDACTION :
- Analyses en 2-3 phrases maximum par bloc
- Toujours citer l'article RGPD concerné (ex: Art. 30, Art. 32, Art. 28)
- Mentionner les sanctions réelles (montants CNIL connus)
- Ton professionnel mais accessible pour un dirigeant de TPE"""

    @property
    def tool_name(self) -> str:
        return "analyse_rgpd"

    @property
    def tool_description(self) -> str:
        return "Analyse la conformité RGPD des blocs A à F et retourne les scores, statuts et analyses."

    @property
    def tool_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "score_A": {"type": "integer", "minimum": 0, "maximum": 15},
                "score_B": {"type": "integer", "minimum": 0, "maximum": 20},
                "score_C": {"type": "integer", "minimum": 0, "maximum": 20},
                "score_D": {"type": "integer", "minimum": 0, "maximum": 15},
                "score_E": {"type": "integer", "minimum": 0, "maximum": 10},
                "score_F": {"type": "integer", "minimum": 0, "maximum": 10},
                "statut_A": {"type": "string", "enum": ["✅", "🟡", "🟠", "🔴"]},
                "statut_B": {"type": "string", "enum": ["✅", "🟡", "🟠", "🔴"]},
                "statut_C": {"type": "string", "enum": ["✅", "🟡", "🟠", "🔴"]},
                "statut_D": {"type": "string", "enum": ["✅", "🟡", "🟠", "🔴"]},
                "statut_E": {"type": "string", "enum": ["✅", "🟡", "🟠", "🔴"]},
                "statut_F": {"type": "string", "enum": ["✅", "🟡", "🟠", "🔴"]},
                "analyse_bloc_A": {"type": "string"},
                "analyse_bloc_B": {"type": "string"},
                "analyse_bloc_C": {"type": "string"},
                "analyse_bloc_D": {"type": "string"},
                "analyse_bloc_E": {"type": "string"},
                "analyse_bloc_F": {"type": "string"},
                "risques_cnil": {"type": "string"},
            },
            "required": [
                "score_A","score_B","score_C","score_D","score_E","score_F",
                "statut_A","statut_B","statut_C","statut_D","statut_E","statut_F",
                "analyse_bloc_A","analyse_bloc_B","analyse_bloc_C",
                "analyse_bloc_D","analyse_bloc_E","analyse_bloc_F",
                "risques_cnil",
            ],
        }

    def analyse(self, data: AuditInput) -> RGPDAnalysis:
        """Point d'entrée principal — retourne un objet RGPDAnalysis validé."""
        prompt = f"""Analyse la conformité RGPD de l'entreprise suivante :

ENTREPRISE : {data.nom_entreprise}
SECTEUR : {data.secteur}
SALARIÉS : {data.nb_salaries}

RÉPONSES DU QUESTIONNAIRE :

Bloc A — Registre des traitements :
  A1 (Registre existe, poids 3) : {data.rep_A1}
  A2 (Registre complet, poids 3) : {data.rep_A2}
  A3 (Registre à jour 12 mois, poids 2) : {data.rep_A3}
  A4 (Données sensibles identifiées, poids 2) : {data.rep_A4}

Bloc B — Site web & Cookies :
  B1 (Politique confidentialité, poids 3) : {data.rep_B1}
  B2 (Mentions complètes, poids 2) : {data.rep_B2}
  B3 (Bandeau cookies, poids 3) : {data.rep_B3}
  B4 (Refus aussi simple qu'acceptation, poids 3) : {data.rep_B4}
  B5 (Cookies désactivés par défaut, poids 2) : {data.rep_B5}

Bloc C — Sécurité des données :
  C1 (Mots de passe forts, poids 2) : {data.rep_C1}
  C2 (2FA activé, poids 3) : {data.rep_C2}
  C3 (Sauvegardes automatisées, poids 2) : {data.rep_C3}
  C4 (Procédure violation 72h, poids 3) : {data.rep_C4}

Bloc D — Sous-traitants & Transferts :
  D1 (Prestataires identifiés, poids 3) : {data.rep_D1}
  D2 (DPA signés, poids 3) : {data.rep_D2}
  D3 (Transferts hors UE, poids 1) : {data.rep_D3}
  D4 (Garanties transfert vérifiées, poids 2) : {data.rep_D4}

Bloc E — Droits des personnes :
  E1 (Exercice droits facilité, poids 2) : {data.rep_E1}
  E2 (Procédure 30 jours, poids 2) : {data.rep_E2}

Bloc F — Email marketing :
  F1 (Consentement explicite, poids 3) : {data.rep_F1}
  F2 (Lien désabonnement, poids 2) : {data.rep_F2}

Calcule les scores, détermine les statuts, rédige les analyses et identifie les risques CNIL."""

        raw = self.run(prompt)
        return RGPDAnalysis(**raw)
