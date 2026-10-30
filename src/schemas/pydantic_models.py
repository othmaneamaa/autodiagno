"""
Schémas Pydantic stricts pour AutoClaim.
Conforme aux spécifications du document MAINTIDOC (Section 7 & 8).
"""

from typing import List, Optional, Literal, Dict, Any
from pydantic import BaseModel, Field

class Citation(BaseModel):
    """Citation exacte d'une source documentaire vérifiable."""
    document_id: str = Field(description="Identifiant unique du document ou manuel constructeur")
    page: int = Field(description="Numéro de page dans le document")
    element_id: Optional[str] = Field(default=None, description="Identifiant de la figure, schéma ou paragraphe")
    snippet: Optional[str] = Field(default=None, description="Extrait textuel justifiant l'affirmation")

class ProposedAction(BaseModel):
    """Action préparée par l'agent nécessitant approbation humaine explicite."""
    action_type: Literal["create_repair_estimate", "order_part", "schedule_inspection"] = Field(
        description="Type d'action sensible demandée"
    )
    vin: str = Field(description="Numéro de série du véhicule (17 caractères)")
    equipment_family: str = Field(description="Famille d'équipement concernée")
    title: str = Field(description="Titre descriptif du devis ou de l'intervention")
    description: str = Field(description="Détail des réparations justifié par les sources")
    estimated_cost: float = Field(default=0.0, description="Montant estimé en euros")
    approval_token: Optional[str] = Field(default=None, description="Jeton unique d'approbation humaine")
    idempotency_key: Optional[str] = Field(default=None, description="Clé d'idempotence anti-doublon")

class AutoClaimOutput(BaseModel):
    """Structure de réponse finale standardisée et validée."""
    status: Literal["success", "needs_clarification", "action_required", "refused", "error"] = Field(
        description="Statut opérationnel du traitement"
    )
    answer: str = Field(description="Réponse synthétique et technique pour le technicien")
    citations: List[Citation] = Field(
        default_factory=list,
        description="Citations obligatoires étayant les affirmations techniques"
    )
    uncertainties: List[str] = Field(
        default_factory=list,
        description="Éléments incertains, hypothèses non confirmées ou manques d'informations"
    )
    clarification_question: Optional[str] = Field(
        default=None,
        description="Question posée si l'image est floue ou les données incomplètes"
    )
    proposed_action: Optional[ProposedAction] = Field(
        default=None,
        description="Proposition de devis/ticket soumise à validation humaine"
    )
    # Champs d'enrichissement LLM (OmniRoute)
    llm_explanation: Optional[str] = Field(default=None, description="Explication technique approfondie générée par le LLM")
    youtube_tutorials: List[Dict[str, str]] = Field(default_factory=list, description="Liens YouTube tutoriels sélectionnés par le LLM")
    safety_alerts: List[str] = Field(default_factory=list, description="Alertes de sécurité supplémentaires (LLM)")
    estimated_labor_minutes: Optional[int] = Field(default=None, description="Temps main-d'œuvre estimé en minutes (LLM)")
    parts_needed: List[str] = Field(default_factory=list, description="Pièces nécessaires (LLM)")
    difficulty_level: Optional[str] = Field(default=None, description="Niveau difficulté: Facile|Moyen|Difficile|Expert (LLM)")

class UserContext(BaseModel):
    """Contexte d'authentification et de permissions de l'utilisateur."""
    user_id: str
    role: Literal["technicien", "expert_valideur", "gestionnaire_flotte", "admin"]
    authorized_groups: List[str] = Field(default_factory=lambda: ["groupe_standard"])
    approval_limit_euros: float = Field(default=500.0, description="Plafond max d'approbation autonome")
