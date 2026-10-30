"""
Script de test rapide du service MCP (sans interface Streamlit).
Permet de vérifier que les deux fonctionnalités "Consultation directe du Serveur MCP"
répondent correctement : historique du véhicule et liste des devis.
"""

import sys
import os
import json

# Ajouter la racine du projet dans sys.path
sys.path.insert(0, os.path.abspath("."))

try:
    from src.mcp_server.server import mcp_service
except Exception as exc:
    print(f"[ERREUR] Impossible d'importer mcp_service : {exc}")
    sys.exit(1)

# VIN de test (à adapter si vous voulez tester un autre véhicule)
VIN_TEST = "VF3CC8HR0ES123456"
ROLE_TEST = "technicien"

print("=" * 60)
print("TEST 1 : Historique du véhicule")
print("=" * 60)
try:
    hist = mcp_service.get_vehicle_history(VIN_TEST, user_role=ROLE_TEST)
    print(json.dumps(hist, indent=2, ensure_ascii=False))
except Exception as exc:
    print(f"[ERREUR] get_vehicle_history a échoué : {exc}")

print()
print("=" * 60)
print("TEST 2 : Devis déjà validés")
print("=" * 60)
try:
    estimates = mcp_service.db.get("created_estimates", [])
    print(json.dumps(estimates, indent=2, ensure_ascii=False))
except Exception as exc:
    print(f"[ERREUR] Lecture des devis a échoué : {exc}")

print()
print("=" * 60)
print("Tests terminés.")
print("=" * 60)
