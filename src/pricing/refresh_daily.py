"""
Pipeline de rafraîchissement quotidien des prix de pièces.
Doit être exécuté chaque jour (via cron ou scheduler).
"""

import os
import sys
from datetime import datetime

# Ajouter le chemin du projet
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from src.pricing.scraper import PricingScraper


def daily_price_refresh():
    """
    Rafraîchissement quotidien des prix.
    À exécuter chaque matin (ex: 6:00 UTC via cron).
    """
    print("=" * 60)
    print(" Rafraîchissement quotidien des prix - AutoClaim ")
    print("=" * 60)
    print(f"Début: {datetime.now().isoformat()}")
    print()

    scraper = PricingScraper()

    try:
        results = scraper.refresh_all_prices()

        print()
        print("Résultats:")
        print("-" * 40)
        for query, prices in results.get("queries", {}).items():
            print(f"  Requête: {query}")
            for p in prices:
                print(f"    - {p.get('product_name', 'N/A')}: {p.get('price_mad', 0):,.2f} MAD ({p.get('site_name', 'N/A')})")

        print()
        print(f"Fin: {datetime.now().isoformat()}")
        print(f"Total de requêtes mises à jour: {len(results.get('queries', {}))}")
        print("=" * 60)

        return results

    except Exception as e:
        print(f"Erreur lors du rafraîchissement: {e}")
        return None


if __name__ == "__main__":
    daily_price_refresh()
