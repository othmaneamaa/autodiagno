#!/usr/bin/env python3
"""
Test de scraping RÉEL sur Autops.ma et Cartec.ma
"""
import sys
sys.path.insert(0, r"C:\Users\Lenovo\Desktop\pfa-project-mix")

from src.pricing.scraper import PricingScraper

scraper = PricingScraper()

print("=" * 60)
print("TEST SCRAPING RÉEL - AUTOPS.MA")
print("=" * 60)

# Test 1: Plaquettes frein
print("\n>>> Autops: 'plaquette frein'")
results = scraper.scrape_autops_search('plaquette frein', 'freinage')
print(f"Résultats trouvés: {len(results)}")
for r in results[:5]:
    print(f"  - {r.product_name} | {r.product_brand} | {r.price_mad} MAD")

# Test 2: Disques frein
print("\n>>> Autops: 'disque frein'")
results = scraper.scrape_autops_search('disque frein', 'freinage')
print(f"Résultats trouvés: {len(results)}")
for r in results[:5]:
    print(f"  - {r.product_name} | {r.product_brand} | {r.price_mad} MAD")

# Test 3: Batterie
print("\n>>> Autops: 'batterie 60ah'")
results = scraper.scrape_autops_search('batterie 60ah', 'electrique')
print(f"Résultats trouvés: {len(results)}")
for r in results[:5]:
    print(f"  - {r.product_name} | {r.product_brand} | {r.price_mad} MAD")

print("\n" + "=" * 60)
print("TEST SCRAPING RÉEL - CARTEC.MA")
print("=" * 60)

# Test 4: Cartec plaquettes
print("\n>>> Cartec: 'plaquette frein'")
results = scraper.scrape_cartec_search('plaquette frein', 'freinage')
print(f"Résultats trouvés: {len(results)}")
for r in results[:5]:
    print(f"  - {r.product_name} | {r.product_brand} | {r.price_mad} MAD")

# Test 5: Cartec alternateur
print("\n>>> Cartec: 'alternateur 120a'")
results = scraper.scrape_cartec_search('alternateur 120a', 'moteur')
print(f"Résultats trouvés: {len(results)}")
for r in results[:5]:
    print(f"  - {r.product_name} | {r.product_brand} | {r.price_mad} MAD")

# Test 6: Cartec batterie
print("\n>>> Cartec: 'batterie 70ah'")
results = scraper.scrape_cartec_search('batterie 70ah', 'electrique')
print(f"Résultats trouvés: {len(results)}")
for r in results[:5]:
    print(f"  - {r.product_name} | {r.product_brand} | {r.price_mad} MAD")

print("\n" + "=" * 60)
print("FIN TESTS")
print("=" * 60)