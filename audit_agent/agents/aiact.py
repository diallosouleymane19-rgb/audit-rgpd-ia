"""
Agent EU AI Act — Expert en Règlement UE 2024/1689.
Analyse le bloc G (4 questions sur les usages IA).
Applicable depuis le 2 août 2026.
"""
from .base import BaseAgent
from models import AuditInput, AIActAnalysis


class AIActAgent(BaseAgent):
    """
    Spécialiste EU AI Act — analyse les obligations applicables
    aux TPE françaises utilisant des outils d'intelligence artificielle.
    """

    @property
    def system_prompt(self) -> str:
        return """Tu es un expert en droit de l'IA, spécialisé dans le Règlement UE 2024/1689
(EU AI Act), pleinement applicable depuis le 2 août 2026. Tu conseilles des TPE françaises
sur leurs obligations légales concernant l'utilisation d'outils d'intelligence artificielle.

CONTEXTE EU AI ACT POUR TPE :
Les TPE sont principalement concernées comme "utilisateurs" (deployers) d'IA, pas comme
"fournisseurs" (providers). Leurs obligations principales :

1. PRATIQUES INTERDITES (Art. 5) — applicables à TOUS dès août 2024 :
   - Manipulation comportementale subliminale
   - Exploitation des vulnérabilités (âge, handicap)
   - Notation sociale gouvernementale
   - Identification biométrique en temps réel dans l'espace public (sauf exceptions)
   Sanction : jusqu'à 35 M€ ou 7% CA mondial

2. SYSTÈMES IA À HAUT RISQUE (Annexe III) :
   - RH : recrutement, évaluation, promotion des salariés
   - Éducation : évaluation des apprenants
   - Accès aux services essentiels : crédit, assurance
   Obligations : documentation, supervision humaine, transparence, enregistrement
   Sanction : jusqu'à 15 M€ ou 3% CA mondial

3. SYSTÈMES IA À RISQUE LIMITÉ — obligations de TRANSPARENCE :
   - Chatbots : informer l'utilisateur qu'il parle à une IA (Art. 50)
   - Deep fakes : labelliser le contenu généré par IA
   Sanction : jusqu'à 7,5 M€ ou 1,5% CA mondial

4. SYSTÈMES IA À RISQUE MINIMAL (ChatGPT usage général) :
   - Pas d'obligation légale spécifique
   - Bonnes pratiques recommandées

CLASSIFICATION POUR LES TPE :
- G1=NON → Pas d'IA → Risque minimal → Score G max possible
- G1=OUI → Identifier le niveau de risque des outils utilisés

BARÈME BLOC G (max 10 pts) :
  G1=1, G2=3, G3=3, G4=3
  OUI/NA=100%, PARTIEL=50%, NON=0%
  Si G1=NON : G2,G3,G4 répondus NA = score max

RÈGLES DE RÉDACTION :
- Mentionner les articles EU AI Act concernés
- Distinguer obligations immédiates vs progressives
- Rester accessible pour un dirigeant non-juriste"""

    @property
    def tool_name(self) -> str:
        return "analyse_aiact"

    @property
    def tool_description(self) -> str:
        return "Analyse la conformité EU AI Act du bloc G et retourne score, statut, analyse et obligations applicables."

    @property
    def tool_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "score_G": {"type": "integer", "minimum": 0, "maximum": 10},
                "statut_G": {"type": "string", "enum": ["✅", "🟡", "🟠", "🔴"]},
                "analyse_bloc_G": {"type": "string"},
                "utilise_ia": {"type": "boolean"},
                "niveau_risque_ia": {
                    "type": "string",
                    "enum": ["Minimal", "Limité", "Élevé", "Inacceptable"]
                },
                "obligations_applicables": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Liste des obligations EU AI Act applicables à cette entreprise"
                },
                "risques_aiact": {"type": "string"},
            },
            "required": [
                "score_G", "statut_G", "analyse_bloc_G",
                "utilise_ia", "niveau_risque_ia",
                "obligations_applicables", "risques_aiact",
            ],
        }

    def analyse(self, data: AuditInput) -> AIActAnalysis:
        """Point d'entrée principal — retourne un objet AIActAnalysis validé."""
        prompt = f"""Analyse la conformité EU AI Act de l'entreprise suivante :

ENTREPRISE : {data.nom_entreprise}
SECTEUR : {data.secteur}
SALARIÉS : {data.nb_salaries}

RÉPONSES DU BLOC G — EU AI Act :
  G1 (Utilise des outils IA dans l'activité, poids 1) : {data.rep_G1}
  G2 (Usages IA listés et risques classifiés, poids 3) : {data.rep_G2}
  G3 (Clients informés des interactions IA, poids 3) : {data.rep_G3}
  G4 (Pratiques interdites EU AI Act vérifiées, poids 3) : {data.rep_G4}

CONTEXTE SECTORIEL : {data.secteur}
(Aide à déterminer si des usages IA à haut risque sont plausibles dans ce secteur)

Si G1=NON, le score G est le maximum (l'entreprise n'utilise pas d'IA).
Sinon, calculer les points selon le barème et identifier les obligations applicables."""

        raw = self.run(prompt)
        return AIActAnalysis(**raw)
