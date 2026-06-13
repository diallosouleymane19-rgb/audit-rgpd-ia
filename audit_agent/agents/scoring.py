"""
Agent Scoring — Validateur et consolidateur des scores.
Reçoit les sorties des agents RGPD et AI Act,
valide la cohérence, calcule le score global, identifie les priorités.
"""
from .base import BaseAgent
from models import RGPDAnalysis, AIActAnalysis, AuditScores


class ScoringAgent(BaseAgent):
    """
    Validateur des scores — croise les analyses RGPD et AI Act
    pour produire un score global cohérent et des priorités actionnables.
    """

    @property
    def system_prompt(self) -> str:
        return """Tu es un analyste de conformité réglementaire spécialisé dans la validation
et la consolidation des scores d'audit pour les TPE françaises.

TON RÔLE :
1. Valider la cohérence des scores calculés par les agents RGPD et AI Act
2. Calculer le score global sur 100 (somme des 7 blocs)
3. Déterminer le niveau de conformité et la couleur associée
4. Identifier les 3 risques les plus prioritaires
5. Lister les blocs critiques (< 40% de leur maximum)
6. Identifier les points forts (≥ 85% de leur maximum)

NIVEAUX DE CONFORMITÉ (score global / 100) :
- 85-100 → CONFORME   → couleur : vert
- 70-84  → ACCEPTABLE → couleur : jaune
- 40-69  → INSUFFISANT → couleur : orange
- 0-39   → CRITIQUE   → couleur : rouge

VALIDATION DES SCORES :
- Vérifier que chaque score de bloc respecte son maximum
- Vérifier que le score global = somme des 7 blocs
- Signaler toute incohérence

IDENTIFICATION DES PRIORITÉS :
Pour les risques prioritaires, prioriser par :
1. Impact financier potentiel (amende CNIL ou AI Act)
2. Probabilité d'un contrôle (bandeau cookies, registre = très contrôlés)
3. Facilité de correction (actions rapides d'abord)

RÈGLES :
- Être précis et chiffré dans les risques (mentionner les montants)
- Limiter les blocs critiques à ceux réellement sous 40% de leur max
- Points forts = blocs vraiment conformes (≥ 85%), pas juste "corrects" """

    @property
    def tool_name(self) -> str:
        return "consolider_scores"

    @property
    def tool_description(self) -> str:
        return "Consolide les scores de tous les blocs et détermine le niveau de conformité global."

    @property
    def tool_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "score_A":  {"type": "integer", "minimum": 0, "maximum": 15},
                "score_B":  {"type": "integer", "minimum": 0, "maximum": 20},
                "score_C":  {"type": "integer", "minimum": 0, "maximum": 20},
                "score_D":  {"type": "integer", "minimum": 0, "maximum": 15},
                "score_E":  {"type": "integer", "minimum": 0, "maximum": 10},
                "score_F":  {"type": "integer", "minimum": 0, "maximum": 10},
                "score_G":  {"type": "integer", "minimum": 0, "maximum": 10},
                "score_global": {"type": "integer", "minimum": 0, "maximum": 100},
                "niveau_conformite": {
                    "type": "string",
                    "enum": ["CRITIQUE", "INSUFFISANT", "ACCEPTABLE", "CONFORME"]
                },
                "couleur_niveau": {
                    "type": "string",
                    "enum": ["rouge", "orange", "jaune", "vert"]
                },
                "risque_prioritaire_1": {"type": "string"},
                "risque_prioritaire_2": {"type": "string"},
                "risque_prioritaire_3": {"type": "string"},
                "blocs_critiques": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Blocs avec score < 40% de leur maximum"
                },
                "points_forts": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Blocs avec score ≥ 85% de leur maximum"
                },
            },
            "required": [
                "score_A","score_B","score_C","score_D","score_E","score_F","score_G",
                "score_global","niveau_conformite","couleur_niveau",
                "risque_prioritaire_1","risque_prioritaire_2","risque_prioritaire_3",
                "blocs_critiques","points_forts",
            ],
        }

    def consolider(
        self, rgpd: RGPDAnalysis, aiact: AIActAnalysis
    ) -> AuditScores:
        """Consolide les résultats des deux agents et valide la cohérence."""

        prompt = f"""Consolide et valide les scores suivants issus des agents RGPD et AI Act :

SCORES AGENTS :
  Bloc A — Registre (max 15)  : {rgpd.score_A} pts | Statut : {rgpd.statut_A}
  Bloc B — Site web (max 20)  : {rgpd.score_B} pts | Statut : {rgpd.statut_B}
  Bloc C — Sécurité (max 20)  : {rgpd.score_C} pts | Statut : {rgpd.statut_C}
  Bloc D — Sous-traitants (max 15) : {rgpd.score_D} pts | Statut : {rgpd.statut_D}
  Bloc E — Droits (max 10)    : {rgpd.score_E} pts | Statut : {rgpd.statut_E}
  Bloc F — Email (max 10)     : {rgpd.score_F} pts | Statut : {rgpd.statut_F}
  Bloc G — AI Act (max 10)    : {aiact.score_G} pts | Statut : {aiact.statut_G}

RISQUES IDENTIFIÉS :
  CNIL : {rgpd.risques_cnil}
  AI Act : {aiact.risques_aiact}
  Utilise IA : {aiact.utilise_ia} | Niveau risque IA : {aiact.niveau_risque_ia}

ANALYSES PAR BLOC :
  A : {rgpd.analyse_bloc_A[:100]}...
  B : {rgpd.analyse_bloc_B[:100]}...
  C : {rgpd.analyse_bloc_C[:100]}...
  D : {rgpd.analyse_bloc_D[:100]}...
  E : {rgpd.analyse_bloc_E[:100]}...
  F : {rgpd.analyse_bloc_F[:100]}...
  G : {aiact.analyse_bloc_G[:100]}...

Valide la cohérence des scores, calcule le score global, détermine le niveau,
et identifie les 3 risques prioritaires et les blocs critiques."""

        raw = self.run(prompt)
        return AuditScores(**raw)
