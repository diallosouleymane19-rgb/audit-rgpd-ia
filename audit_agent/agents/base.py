"""
Classe de base pour tous les agents Claude.
Gère l'appel API Anthropic avec tool_use pour forcer un JSON structuré.
"""
import json
import logging
from typing import Any
import anthropic

logger = logging.getLogger(__name__)


class BaseAgent:
    """
    Agent Claude de base.
    Chaque agent héritant de cette classe possède :
      - Un system_prompt spécialisé
      - Un outil 'output_schema' qui force Claude à retourner un JSON valide
      - Une méthode run() qui retourne toujours un dict typé
    """

    model: str = "claude-sonnet-4-6"
    max_tokens: int = 4096
    temperature: float = 0   # Déterministe pour la cohérence des scores

    def __init__(self, client: anthropic.Anthropic):
        self.client = client

    @property
    def system_prompt(self) -> str:
        raise NotImplementedError

    @property
    def tool_name(self) -> str:
        raise NotImplementedError

    @property
    def tool_description(self) -> str:
        raise NotImplementedError

    @property
    def tool_schema(self) -> dict:
        raise NotImplementedError

    def run(self, user_message: str) -> dict:
        """
        Appelle l'API Anthropic avec tool_use forcé.
        Retourne toujours le dict JSON produit par l'agent.
        """
        logger.info(f"[{self.__class__.__name__}] Démarrage de l'analyse…")

        response = self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            system=self.system_prompt,
            tools=[{
                "name": self.tool_name,
                "description": self.tool_description,
                "input_schema": self.tool_schema,
            }],
            tool_choice={"type": "tool", "name": self.tool_name},  # Force l'utilisation de l'outil
            messages=[{"role": "user", "content": user_message}],
        )

        # Extraire le résultat de l'outil
        for block in response.content:
            if block.type == "tool_use" and block.name == self.tool_name:
                logger.info(f"[{self.__class__.__name__}] ✅ Réponse reçue")
                return block.input

        raise ValueError(f"[{self.__class__.__name__}] Aucun tool_use trouvé dans la réponse")

    def _reponse_to_points(self, reponse: str, poids: int) -> int:
        """Calcule les points obtenus selon la réponse et le poids de la question."""
        r = reponse.upper()
        if r in ("OUI", "NA"):
            return poids
        if r == "PARTIEL":
            return round(poids / 2)
        return 0  # NON

    def _statut_from_pct(self, pct: float) -> str:
        if pct >= 0.85: return "✅"
        if pct >= 0.70: return "🟡"
        if pct >= 0.40: return "🟠"
        return "🔴"
