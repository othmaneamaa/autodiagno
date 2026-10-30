"""
Exécuteur global de tous les tests pour AutoClaim.
Lance successivement :
1. Tests unitaires des composants (PyMuPDF, MCP, RBAC, Guardrails, Pydantic)
2. Tests d'intégration des endpoints FastAPI
3. Benchmark d'évaluation des 150 scénarios (Section 10)
4. Évaluation scientifique du Reranker (Section 5)
"""

import sys
import unittest

def run_suite():
    print("=" * 70)
    print("  🚀 LANCEMENT DE LA SUITE DE TESTS GLOBALE - AUTOCLAIM")
    print("=" * 70)

    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Découverte de tous les tests dans tests/
    suite.addTests(loader.discover("tests", pattern="test_*.py"))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print("\n" + "=" * 70)
    if result.wasSuccessful():
        print("  🎉 TOUS LES TESTS SONT PASSÉS AVEC SUCCÈS (100% SUCCÈS) !")
    else:
        print(f"  ❌ ÉCHECS DÉTECTÉS : {len(result.failures)} échecs, {len(result.errors)} erreurs.")
    print("=" * 70)

    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_suite()
    sys.exit(0 if success else 1)
