"""
Test approfondi de la fonctionnalité d'analyse d'image (VLM + Détection physique de flou).
Vérifie :
1. Génération et détection d'une photo nette de voyant orange
2. Génération et détection d'une photo nette d'usure de plaquette de frein
3. Détection physique de flou/contraste insuffisant menant à l'abstention
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from scripts.generate_sample_images import generate_samples
from src.agent.nodes import inspect_image_file, node_analyze_image_and_query
from src.schemas.pydantic_models import UserContext
from src.schemas.state import AgentState
from src.agent.graph import agent_graph

class TestImageFeature(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Générer les vraies images de test
        generate_samples()
        cls.samples_dir = os.path.join(os.path.dirname(__file__), "..", "data", "sample_images")

    def test_01_inspect_engine_warning_image(self):
        """Vérifie que l'image du voyant moteur est nette et possède la couleur orange."""
        img_path = os.path.join(self.samples_dir, "voyant_moteur_peugeot.png")
        meta = inspect_image_file(img_path)

        self.assertIsNotNone(meta)
        self.assertFalse(meta["is_blurry"], "L'image du voyant moteur doit être considérée comme nette.")
        self.assertTrue(meta["has_orange"], "La couleur orange ambrée du voyant moteur doit être détectée.")
        print("\n[OK] Image Test 1 : Voyant moteur identifié avec composante orange et netteté validée.")

    def test_02_inspect_blurry_image(self):
        """Vérifie la détection physique du flou gaussien sur une image non exploitable."""
        img_path = os.path.join(self.samples_dir, "photo_floue_inconnue.png")
        meta = inspect_image_file(img_path)

        self.assertIsNotNone(meta)
        self.assertTrue(meta["is_blurry"], "L'image floue doit être détectée comme 'is_blurry = True'.")
        print("[OK] Image Test 2 : Filtre de détection de contours a bien mesuré l'absence de netteté.")

    def test_03_end_to_end_engine_warning(self):
        """Exécute l'agent complet avec la photo réelle du voyant moteur."""
        img_path = os.path.join(self.samples_dir, "voyant_moteur_peugeot.png")
        user = UserContext(user_id="TECH_01", role="technicien")
        state = AgentState(
            user=user,
            query="Que signifie ce voyant allumé sur mon combiné ?",
            image_path=img_path,
            vin="VF3CC8HR0ES123456"
        )
        final_state = agent_graph.invoke(state)
        output = final_state.get("final_output")

        self.assertIsNotNone(output)
        self.assertIn(output.status, ["success", "action_required"])
        self.assertGreaterEqual(len(output.citations), 1)
        self.assertIn("42", str(output.citations[0].page))
        print("[OK] Image Test 3 : Pipeline complet avec photo nette mène à la citation du Manuel p.42.")

    def test_04_end_to_end_blurry_image_clarification(self):
        """Exécute l'agent complet avec la photo réelle floue -> Vérifie le refus d'halluciner."""
        img_path = os.path.join(self.samples_dir, "photo_floue_inconnue.png")
        user = UserContext(user_id="TECH_01", role="technicien")
        state = AgentState(
            user=user,
            query="Quelle est cette pièce endommagée ?",
            image_path=img_path
        )
        final_state = agent_graph.invoke(state)
        output = final_state.get("final_output")

        self.assertIsNotNone(output)
        self.assertEqual(output.status, "needs_clarification")
        self.assertIsNotNone(output.clarification_question)
        self.assertIn("nette", output.clarification_question.lower())
        print("[OK] Image Test 4 : Face à une vraie image floue, l'agent demande une clarification sans halluciner.")

if __name__ == "__main__":
    unittest.main(verbosity=2)
