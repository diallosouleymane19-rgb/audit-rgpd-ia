"""
Modèles de données — Micro-Audit RGPD / IA Act
SMD GLOBAL CONSULTING LLC
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Literal, Optional
from enum import Enum


# ─────────────────────────────────────────────────────────
# TYPES DE BASE
# ─────────────────────────────────────────────────────────

ReponseType = Literal["OUI", "NON", "PARTIEL", "NA"]
NiveauType  = Literal["CRITIQUE", "INSUFFISANT", "ACCEPTABLE", "CONFORME"]
StatutType  = Literal["✅", "🟡", "🟠", "🔴"]


# ─────────────────────────────────────────────────────────
# ENTRÉE — Formulaire Tally
# ─────────────────────────────────────────────────────────

class AuditInput(BaseModel):
    """Données brutes reçues depuis le webhook Tally."""

    # Informations client
    nom_entreprise:  str = Field(..., description="Nom de l'entreprise auditée")
    secteur:         str = Field(..., description="Secteur d'activité")
    nb_salaries:     str = Field(..., description="Nombre de salariés (string pour flexibilité)")
    nom_dirigeant:   str = Field(..., description="Nom et prénom du dirigeant")
    email_client:    str = Field(..., description="Email de livraison du rapport")

    # Bloc A — Registre des traitements (4 questions, max 15 pts)
    rep_A1: ReponseType = Field(..., description="Registre des traitements existe")
    rep_A2: ReponseType = Field(..., description="Registre liste finalité/base légale/durée")
    rep_A3: ReponseType = Field(..., description="Registre mis à jour dans les 12 mois")
    rep_A4: ReponseType = Field(..., description="Données sensibles identifiées")

    # Bloc B — Site web & Cookies (5 questions, max 20 pts)
    rep_B1: ReponseType = Field(..., description="Politique de confidentialité présente")
    rep_B2: ReponseType = Field(..., description="Mentions complètes dans la politique")
    rep_B3: ReponseType = Field(..., description="Bandeau cookies présent")
    rep_B4: ReponseType = Field(..., description="Refus cookies aussi simple qu'acceptation")
    rep_B5: ReponseType = Field(..., description="Cookies analytiques désactivés par défaut")

    # Bloc C — Sécurité des données (4 questions, max 20 pts)
    rep_C1: ReponseType = Field(..., description="Mots de passe forts sur outils critiques")
    rep_C2: ReponseType = Field(..., description="Authentification 2FA activée")
    rep_C3: ReponseType = Field(..., description="Sauvegardes automatisées et testées")
    rep_C4: ReponseType = Field(..., description="Procédure notification CNIL 72h connue")

    # Bloc D — Sous-traitants & Transferts (4 questions, max 15 pts)
    rep_D1: ReponseType = Field(..., description="Prestataires data identifiés")
    rep_D2: ReponseType = Field(..., description="DPA signés avec chaque prestataire")
    rep_D3: ReponseType = Field(..., description="Transferts de données hors UE existants")
    rep_D4: ReponseType = Field(..., description="Garanties de transfert vérifiées (CCT)")

    # Bloc E — Droits des personnes (2 questions, max 10 pts)
    rep_E1: ReponseType = Field(..., description="Exercice des droits facilité")
    rep_E2: ReponseType = Field(..., description="Procédure réponse 30 jours formalisée")

    # Bloc F — Email marketing (2 questions, max 10 pts)
    rep_F1: ReponseType = Field(..., description="Email marketing avec consentement explicite")
    rep_F2: ReponseType = Field(..., description="Lien désabonnement dans chaque email")

    # Bloc G — EU AI Act (4 questions, max 10 pts)
    rep_G1: ReponseType = Field(..., description="Usages IA utilisés dans l'activité")
    rep_G2: ReponseType = Field(..., description="Usages IA listés et risques classifiés")
    rep_G3: ReponseType = Field(..., description="Clients informés des interactions IA")
    rep_G4: ReponseType = Field(..., description="Pratiques interdites EU AI Act vérifiées")


# ─────────────────────────────────────────────────────────
# SORTIE AGENT RGPD (Blocs A–F)
# ─────────────────────────────────────────────────────────

class RGPDAnalysis(BaseModel):
    """Sortie de l'Agent RGPD — analyse des blocs A à F."""

    score_A: int = Field(..., ge=0, le=15)
    score_B: int = Field(..., ge=0, le=20)
    score_C: int = Field(..., ge=0, le=20)
    score_D: int = Field(..., ge=0, le=15)
    score_E: int = Field(..., ge=0, le=10)
    score_F: int = Field(..., ge=0, le=10)

    statut_A: StatutType
    statut_B: StatutType
    statut_C: StatutType
    statut_D: StatutType
    statut_E: StatutType
    statut_F: StatutType

    analyse_bloc_A: str = Field(..., description="Analyse 2-3 phrases du bloc A")
    analyse_bloc_B: str = Field(..., description="Analyse 2-3 phrases du bloc B")
    analyse_bloc_C: str = Field(..., description="Analyse 2-3 phrases du bloc C")
    analyse_bloc_D: str = Field(..., description="Analyse 2-3 phrases du bloc D")
    analyse_bloc_E: str = Field(..., description="Analyse 2-3 phrases du bloc E")
    analyse_bloc_F: str = Field(..., description="Analyse 2-3 phrases du bloc F")

    risques_cnil: str = Field(..., description="Risques CNIL identifiés et sanctions potentielles")


# ─────────────────────────────────────────────────────────
# SORTIE AGENT AI ACT (Bloc G)
# ─────────────────────────────────────────────────────────

class AIActAnalysis(BaseModel):
    """Sortie de l'Agent EU AI Act — analyse du bloc G."""

    score_G: int = Field(..., ge=0, le=10)
    statut_G: StatutType
    analyse_bloc_G: str = Field(..., description="Analyse 2-3 phrases du bloc G")

    utilise_ia: bool = Field(..., description="True si l'entreprise utilise des outils IA")
    niveau_risque_ia: Literal["Minimal", "Limité", "Élevé", "Inacceptable"]
    obligations_applicables: list[str] = Field(
        ..., description="Liste des obligations EU AI Act applicables"
    )
    risques_aiact: str = Field(..., description="Sanctions potentielles EU AI Act")


# ─────────────────────────────────────────────────────────
# SORTIE AGENT SCORING
# ─────────────────────────────────────────────────────────

class AuditScores(BaseModel):
    """Sortie de l'Agent Scoring — validation et consolidation des scores."""

    # Scores validés
    score_A: int; score_B: int; score_C: int; score_D: int
    score_E: int; score_F: int; score_G: int
    score_global: int = Field(..., ge=0, le=100)

    # Niveau de conformité
    niveau_conformite: NiveauType
    couleur_niveau: Literal["rouge", "orange", "jaune", "vert"]

    # Top 3 risques prioritaires
    risque_prioritaire_1: str
    risque_prioritaire_2: str
    risque_prioritaire_3: str

    # Blocs critiques (score < 40%)
    blocs_critiques: list[str]

    # Points forts (score > 85%)
    points_forts: list[str]


# ─────────────────────────────────────────────────────────
# SORTIE AGENT RAPPORT
# ─────────────────────────────────────────────────────────

class AuditReport(BaseModel):
    """Sortie de l'Agent Rapport — narration complète et plan d'action."""

    # Résumé exécutif
    resume_executif: str = Field(..., description="Synthèse en 3-4 phrases pour le dirigeant")

    # Plan d'action priorisé
    action_urgente_1: str
    action_urgente_2: str
    action_urgente_3: str
    action_3mois_1: str
    action_3mois_2: str
    action_3mois_3: str
    action_6mois_1: str
    action_6mois_2: str

    # Contexte réglementaire
    risques_financiers: str = Field(
        ..., description="Risques CNIL + AI Act chiffrés"
    )

    # Conclusion personnalisée
    conclusion: str = Field(..., description="Conclusion avec prochaines étapes")

    # Phrase d'accroche pour l'email de livraison
    accroche_email: str = Field(
        ..., description="1 phrase personnalisée pour l'objet de l'email"
    )


# ─────────────────────────────────────────────────────────
# RÉSULTAT COMPLET DE L'AUDIT
# ─────────────────────────────────────────────────────────

class AuditResult(BaseModel):
    """Résultat complet consolidé de l'audit — tous les agents."""

    # Entrée
    input: AuditInput

    # Sorties agents
    rgpd:    RGPDAnalysis
    aiact:   AIActAnalysis
    scores:  AuditScores
    report:  AuditReport

    # Métadonnées
    date_audit:     str          # Format DD/MM/YYYY (affichage)
    date_audit_iso: str = ""     # Format YYYY-MM-DD (Notion date field)
    pdf_url:        Optional[str] = None
    drive_url:      Optional[str] = None
    notion_page_id: Optional[str] = None
    statut:         Literal["pending", "analysed", "generated", "delivered"] = "pending"
