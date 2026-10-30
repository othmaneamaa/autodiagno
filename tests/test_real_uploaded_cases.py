"""
Test de cas réels concrets téléversés :
1. Téléversement d'une alerte pression de pneu (TPMS)
2. Téléversement d'une alerte batterie
3. Téléversement d'une alerte surchauffe moteur
Vérifie que chaque cas réel renvoie le bon diagnostic, le bon manuel et le bon devis.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.schemas.pydantic_models import UserContext
from src.schemas.state import AgentState
from src.agent.graph import agent_graph

class TestRealUploadedCases(unittest.TestCase):

    def test_01_tyre_pressure_tpms_case(self):
        """Cas concret réel : Alerte pression de pneu TPMS."""
        user = UserContext(user_id="TECH_01", role="technicien")
        state = AgentState(
            user=user,
            query="J'ai ce voyant orange en forme de pneu allumé sur mon combiné. Comment gérer ce problème ?",
            image_path="alerte_pression_pneu_google.jpg",
            vin="VF7SA9HP0DW789012"
        )
        final_state = agent_graph.invoke(state)
        output = final_state.get("final_output")

        self.assertIsNotNone(output)
        # Vérifier que le VLM a bien détecté le TPMS
        self.assertIn("TPMS", final_state.get("visual_analysis", ""))
        # Vérifier que le manuel cité est bien celui du TPMS (Page 78)
        self.assertTrue(any("78" in str(c.page) for c in output.citations), "Le manuel doit citer la page 78 TPMS.")
        # Vérifier que la réponse parle de pression des pneus
        self.assertIn("pression", output.answer.lower())
        # Vérifier que le devis préparé est bien le contrôle pneumatiques (40 €)
        self.assertIsNotNone(output.proposed_action)
        self.assertEqual(output.proposed_action.estimated_cost, 40.0)
        print("\n[OK] Cas 1 : Alerte pression pneu TPMS correctement diagnostiquée (Manuel p.78, Devis 40€).")

    def test_02_battery_warning_case(self):
        """Cas concret réel : Alerte batterie rouge."""
        user = UserContext(user_id="TECH_01", role="technicien")
        state = AgentState(
            user=user,
            query="Témoin rouge batterie allumé avec message défaut alternateur.",
            image_path="voyant_batterie.png",
            vin="VF3CC8HR0ES123456"
        )
        final_state = agent_graph.invoke(state)
        output = final_state.get("final_output")

        self.assertIsNotNone(output)
        self.assertTrue(any("50" in str(c.page) for c in output.citations), "Le manuel doit citer la page 50 Batterie.")
        self.assertIn("batterie", output.answer.lower())
        self.assertEqual(output.proposed_action.estimated_cost, 65.0)
        print("[OK] Cas 2 : Témoin batterie correctement diagnostiqué (Manuel p.50, Devis 65€).")

    def test_03_engine_overheating_case(self):
        """Cas concret réel : Surchauffe moteur."""
        user = UserContext(user_id="TECH_01", role="technicien")
        state = AgentState(
            user=user,
            query="Témoin rouge thermomètre qui s'allume avec surchauffe moteur.",
            image_path="surchauffe_moteur.jpg",
            vin="VF3CC8HR0ES123456"
        )
        final_state = agent_graph.invoke(state)
        output = final_state.get("final_output")

        self.assertIsNotNone(output)
        self.assertTrue(any("52" in str(c.page) for c in output.citations), "Le manuel doit citer la page 52 Surchauffe.")
        self.assertIn("surchauffe", output.answer.lower())
        self.assertEqual(output.proposed_action.estimated_cost, 95.0)
        print("[OK] Cas 3 : Surchauffe moteur correctement diagnostiquée (Manuel p.52, Devis 95€).")

    def test_04_user_uploaded_google_tpms_image(self):
        """Cas concret réel : Image réelle Google uploadée par l'utilisateur (images (1).png)."""
        user_img_path = os.path.join(os.path.dirname(__file__), "..", "data", "uploaded_images", "images (1).png")
        if not os.path.exists(user_img_path):
            self.skipTest("Image utilisateur images (1).png non trouvée.")

        user = UserContext(user_id="TECH_01", role="technicien")
        state = AgentState(
            user=user,
            query="Voici une photo d'un voyant allumé sur mon combiné. Comment gérer ce problème ?",
            image_path=user_img_path,
            vin="VF7SA9HP0DW789012"
        )
        final_state = agent_graph.invoke(state)
        output = final_state.get("final_output")

        self.assertIsNotNone(output)
        self.assertIn("TPMS", final_state.get("visual_analysis", ""))
        self.assertTrue(any("78" in str(c.page) for c in output.citations), "Le manuel doit citer la page 78 TPMS.")
        self.assertIn("pression", output.answer.lower())
        self.assertIsNotNone(output.proposed_action)
        self.assertEqual(output.proposed_action.estimated_cost, 40.0)
        print("[OK] Cas 4 : Image réelle Google (images (1).png) reconnue automatiquement comme TPMS (Manuel p.78, Devis 40€).")

if __name__ == "__main__":
    unittest.main(verbosity=2)
