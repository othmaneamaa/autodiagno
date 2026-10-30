"""
Serveur MCP (Model Context Protocol) pour AutoClaim.
Expose les outils de consultation d'historique et de création sécurisée de devis.
Gère l'idempotence, la validation des tokens d'approbation et le contrôle d'accès.
"""

import json
import os
import uuid
from typing import Dict, Any, List, Optional

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "synthetic", "mcp_database.json")

class MCPServer:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = os.path.abspath(db_path)
        self._load_db()

    def _load_db(self):
        if os.path.exists(self.db_path):
            with open(self.db_path, "r", encoding="utf-8") as f:
                self.db = json.load(f)
        else:
            self.db = {"vehicles": {}, "created_estimates": []}

    def _save_db(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        with open(self.db_path, "w", encoding="utf-8") as f:
            json.dump(self.db, f, indent=2, ensure_ascii=False)

    def get_all_vehicles(self) -> List[Dict[str, Any]]:
        """Retourne la liste de tous les véhicules enregistrés avec leurs spécifications techniques."""
        self._load_db()
        vehicles = list(self.db.get("vehicles", {}).values())
        return vehicles

    def get_vehicle_spec(self, vin: str) -> Optional[Dict[str, Any]]:
        """Retourne la fiche technique détaillée complète d'un véhicule spécifique."""
        self._load_db()
        vin = vin.strip().upper()
        return self.db.get("vehicles", {}).get(vin)

    def get_vehicle_history(self, vin: str, user_role: str) -> Dict[str, Any]:
        """
        Consulte l'historique d'interventions passées pour un véhicule donné.
        Contrôle d'accès : accessible à tous les rôles authentifiés.
        """
        vin = vin.strip().upper()
        vehicle = self.db.get("vehicles", {}).get(vin)
        if not vehicle:
            return {
                "success": False,
                "vin": vin,
                "error": f"Aucun véhicule enregistré avec le VIN : {vin}"
            }
        return {
            "success": True,
            "vin": vin,
            "model": vehicle["model"],
            "mileage_km": vehicle["mileage_km"],
            "interventions": vehicle.get("history", [])
        }

    def get_open_claims(self, vin: str, user_role: str) -> Dict[str, Any]:
        """
        Consulte la liste des dossiers de sinistres ou réclamations ouvertes pour un VIN.
        """
        vin = vin.strip().upper()
        vehicle = self.db.get("vehicles", {}).get(vin)
        if not vehicle:
            return {
                "success": False,
                "vin": vin,
                "error": f"Véhicule non trouvé pour le VIN : {vin}"
            }
        return {
            "success": True,
            "vin": vin,
            "open_claims": vehicle.get("open_claims", [])
        }

    def create_repair_estimate(
        self,
        vin: str,
        title: str,
        description: str,
        estimated_cost: float,
        approval_token: str,
        user_role: str,
        idempotency_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Crée un devis officiel d'intervention après validation humaine.
        Règles de sécurité :
        - Exige un approval_token valide.
        - Vérifie la clé d'idempotence pour interdire les doublons.
        - Exige que le rôle ait l'autorité de validation.
        """
        vin = vin.strip().upper()
        if not approval_token or not approval_token.startswith("APP-"):
            return {
                "success": False,
                "error": "Action refusée : jeton d'approbation humaine manquant ou invalide."
            }

        if user_role not in ["expert_valideur", "admin", "technicien"]:
            return {
                "success": False,
                "error": f"Action refusée : rôle '{user_role}' non autorisé à valider ce devis."
            }

        # Vérification d'idempotence
        if idempotency_key:
            for item in self.db.get("created_estimates", []):
                if item.get("idempotency_key") == idempotency_key:
                    return {
                        "success": True,
                        "status": "already_processed",
                        "message": "Requête déjà traitée (idempotence respectée).",
                        "estimate": item
                    }

        estimate_id = f"EST-{uuid.uuid4().hex[:8].upper()}"
        new_estimate = {
            "estimate_id": estimate_id,
            "vin": vin,
            "title": title,
            "description": description,
            "estimated_cost": estimated_cost,
            "approved_by_role": user_role,
            "approval_token": approval_token,
            "idempotency_key": idempotency_key or str(uuid.uuid4()),
            "status": "validated"
        }

        self.db.setdefault("created_estimates", []).append(new_estimate)
        self._save_db()

        return {
            "success": True,
            "status": "created",
            "estimate_id": estimate_id,
            "message": f"Devis {estimate_id} enregistré avec succès après approbation humaine.",
            "estimate": new_estimate
        }

# Instance globale
mcp_service = MCPServer()
