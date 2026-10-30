"""
État partagé du graphe d'agent LangGraph pour AutoClaim.
Gère la persistance de l'état, les budgets d'exécution et les étapes Human-in-the-Loop.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from src.schemas.pydantic_models import UserContext, ProposedAction, AutoClaimOutput, Citation

class AgentState(BaseModel):
    """État central du workflow agentique LangGraph."""
    # Entrées utilisateur
    user: UserContext
    query: str
    image_path: Optional[str] = None
    vin: Optional[str] = None

    # Analyses intermédiaires
    is_image_usable: bool = True
    visual_analysis: str = ""
    visual_category: str = ""  # Catégorie précise détectée: tpms_pression_pneu, surchauffe_moteur, etc.
    retrieved_chunks: List[Dict[str, Any]] = Field(default_factory=list)
    reranked_chunks: List[Dict[str, Any]] = Field(default_factory=list)
    citations: List[Citation] = Field(default_factory=list)

    # Outils MCP
    vehicle_history: Optional[Dict[str, Any]] = None
    open_claims: Optional[List[Dict[str, Any]]] = None

    # Sortie & Validation humaine
    draft_action: Optional[ProposedAction] = None
    human_approved: bool = False
    action_result: Optional[Dict[str, Any]] = None
    final_output: Optional[AutoClaimOutput] = None

    # Contrôle de sécurité et budgets
    budget_mcp_calls: int = 0
    budget_model_calls: int = 0
    max_mcp_calls: int = 3
    max_model_calls: int = 6
    is_prompt_injection_detected: bool = False
    errors: List[str] = Field(default_factory=list)
