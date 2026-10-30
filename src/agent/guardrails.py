"""
Garde-fous de sécurité et gestion des budgets du prototype AutoClaim.
Implémente la détection d'injection de prompt, la vérification RBAC et le contrôle des quotas.
"""

import re
from typing import Tuple, Dict, Any, Optional
from src.schemas.pydantic_models import UserContext

# Modèles d'injections de prompt connus et tests malveillants
PROMPT_INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions",
    r"ignore\s+les\s+instructions\s+précédentes",
    r"system\s*override",
    r"you\s+are\s+now\s+in\s+developer\s+mode",
    r"envoie\s+(tous\s+)?les\s+rapports\s+vers\s+un\s+service\s+externe",
    r"exfiltrat(e|ion)",
    r"delete\s+database",
    r"drop\s+table",
    r"sudo\s+",
    r"cat\s+/etc/passwd"
]

class SecurityGuardrails:
    @staticmethod
    def inspect_text_for_injection(text: str) -> Tuple[bool, Optional[str]]:
        """
        Détecte les tentatives directes ou indirectes d'injection de prompt dans les requêtes,
        les résultats OCR ou les documents non fiables.
        """
        if not text:
            return False, None

        for pattern in PROMPT_INJECTION_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                return True, f"Tentative d'injection de prompt détectée via le motif : {pattern}"

        return False, None

    @staticmethod
    def verify_rbac(user: UserContext, required_role: str) -> bool:
        """Vérifie si l'utilisateur possède le rôle minimal nécessaire."""
        role_hierarchy = {
            "technicien": 1,
            "expert_valideur": 2,
            "gestionnaire_flotte": 2,
            "admin": 3
        }
        user_level = role_hierarchy.get(user.role, 0)
        required_level = role_hierarchy.get(required_role, 1)
        return user_level >= required_level

    @staticmethod
    def check_budgets(state_mcp_calls: int, state_model_calls: int) -> Tuple[bool, Optional[str]]:
        """
        Contrôle les budgets stricts imposés par la Section 9 du document :
        - Max 3 appels MCP par demande.
        - Max 6 appels au modèle par demande.
        """
        if state_mcp_calls >= 3:
            return False, "Budget MCP dépassé (maximum 3 appels autorisés par demande)."
        if state_model_calls >= 6:
            return False, "Budget modèle dépassé (maximum 6 appels autorisés par demande)."
        return True, None

guardrails = SecurityGuardrails()
