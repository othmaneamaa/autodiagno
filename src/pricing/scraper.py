"""
Scrapeur de prix pour pièces auto marocaines.
Cible principalement: Autops.ma, Cartec.ma
"""

import os
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict

import requests
from bs4 import BeautifulSoup

REQUESTS_AVAILABLE = True


@dataclass
class PriceItem:
    """Un élément de prix extrait d'un site."""
    site_name: str
    site_url: str
    product_name: str
    product_brand: str
    product_category: str
    price_mad: float
    currency: str = "MAD"
    last_updated: str = ""
    in_stock: bool = True
    scrape_timestamp: str = ""


class PricingScraper:
    """Scrapeur multi-sources pour prix pièces auto Maroc."""

    CATEGORY_MAPPING = {
        "systeme_freinage_liaisons_au_sol": {
            "keywords": ["plaquette frein", "disque frein", "etrier frein"],
            "fallback_price": 180.0
        },
        "groupe_motopropulseur_electronique": {
            "keywords": ["batterie voiture", "alternateur 12v", "bougie allumage"],
            "fallback_price": 850.0
        }
    }

    SITES_CONFIG = {
        "autops": {
            "base_url": "https://www.autops.ma",
            "search_url": "https://www.autops.ma/search?q={query}",
        },
        "cartec": {
            "base_url": "https://www.cartec.ma",
            "search_url": "https://www.cartec.ma/search?q={query}",
        }
    }

    def __init__(self, storage_path: str = "./data/pricing"):
        self.storage_path = os.path.abspath(storage_path)
        self.cache_file = os.path.join(self.storage_path, "prices_cache.json")
        self.last_update_file = os.path.join(self.storage_path, "last_update.txt")
        os.makedirs(self.storage_path, exist_ok=True)
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive"
        })

    def _load_cache(self) -> Optional[Dict[str, Any]]:
        if not os.path.exists(self.cache_file):
            return None

        try:
            with open(self.cache_file, "r", encoding="utf-8") as f:
                cache = json.load(f)

            if os.path.exists(self.last_update_file):
                with open(self.last_update_file, "r", encoding="utf-8") as f:
                    last_update = f.read().strip()
                    last_date = datetime.fromisoformat(last_update)
                    if datetime.now() - last_date < timedelta(hours=24):
                        return cache
        except Exception as e:
            print(f"Erreur chargement cache: {e}")

        return None

    def _save_cache(self, data: Dict[str, Any]):
        os.makedirs(self.storage_path, exist_ok=True)

        with open(self.cache_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        with open(self.last_update_file, "w", encoding="utf-8") as f:
            f.write(datetime.now().isoformat())

    def _parse_price(self, text: str) -> float:
        import re
        patterns = [
            r'([\d\s]+)[,\.]?(\d{2})\s*(?:MAD|DH|dhiram)',
            r'([\d\s]+)[,\.]?(\d{2})\s*(?:€|euro)',
        ]

        for pattern in patterns:
            match = re.search(pattern, text.lower())
            if match:
                try:
                    number_str = match.group(1).replace(' ', '') + '.' + match.group(2)
                    return float(number_str)
                except ValueError:
                    continue
        return 0.0

    def scrape_autops_search(self, query: str, category: str) -> List[PriceItem]:
        items = []

        try:
            search_url = self.SITES_CONFIG["autops"]["search_url"].format(query=query)
            response = self.session.get(search_url, timeout=15)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Chercher tous les blocs produits
            products = soup.find_all(['div', 'article'], class_=lambda c: c and any(
                x in str(c).lower() for x in ['product', 'item', 'card', 'box', 'col']
            ))

            if not products:
                # Fallback: chercher toutes les divs avec titre
                products = soup.find_all(['div', 'article'])[:30]

            for product in products[:15]:
                try:
                    name_el = product.find(['h2', 'h3', 'h4', 'a'])
                    product_name = name_el.get_text().strip() if name_el else "Pièce auto"

                    price_text = ""
                    price_el = product.find(['span', 'div', 'p'], class_=lambda c: c and 'price' in str(c).lower())
                    if price_el:
                        price_text = price_el.get_text().strip()

                    if not price_text:
                        all_text = product.get_text()
                        price_match = re.search(r'([\d\s]+)[,\.]?\d{2}\s*(?:MAD|DH)', all_text)
                        if price_match:
                            price_text = price_match.group(0)

                    price = self._parse_price(price_text)

                    brand = ""
                    brand_el = product.find(['span', 'div'], class_=lambda c: c and 'brand' in str(c).lower())
                    if brand_el:
                        brand = brand_el.get_text().strip()

                    if price > 0:
                        items.append(PriceItem(
                            site_name="Autops",
                            site_url=self.SITES_CONFIG["autops"]["base_url"],
                            product_name=product_name,
                            product_brand=brand if brand else "Marque inconnue",
                            product_category=category,
                            price_mad=price,
                            scrape_timestamp=datetime.now().isoformat()
                        ))
                except Exception:
                    continue

        except Exception as e:
            print(f"Erreur scraping Autops search '{query}': {e}")

        return items

    def scrape_cartec_search(self, query: str, category: str) -> List[PriceItem]:
        items = []

        try:
            search_url = self.SITES_CONFIG["cartec"]["search_url"].format(query=query)
            response = self.session.get(search_url, timeout=15)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            products = soup.find_all(['div', 'article'], class_=lambda c: c and any(
                x in str(c).lower() for x in ['product', 'item', 'card', 'box', 'col']
            ))

            if not products:
                products = soup.find_all(['div', 'article'])[:30]

            for product in products[:15]:
                try:
                    name_el = product.find(['h2', 'h3', 'h4', 'a'])
                    product_name = name_el.get_text().strip() if name_el else "Pièce auto"

                    price_text = ""
                    price_el = product.find(['span', 'div', 'p'], class_=lambda c: c and 'price' in str(c).lower())
                    if price_el:
                        price_text = price_el.get_text().strip()

                    if not price_text:
                        all_text = product.get_text()
                        price_match = re.search(r'([\d\s]+)[,\.]?\d{2}\s*(?:MAD|DH)', all_text)
                        if price_match:
                            price_text = price_match.group(0)

                    price = self._parse_price(price_text)

                    brand = ""
                    brand_el = product.find(['span', 'div'], class_=lambda c: c and 'brand' in str(c).lower())
                    if brand_el:
                        brand = brand_el.get_text().strip()

                    if price > 0:
                        items.append(PriceItem(
                            site_name="Cartec",
                            site_url=self.SITES_CONFIG["cartec"]["base_url"],
                            product_name=product_name,
                            product_brand=brand if brand else "Marque inconnue",
                            product_category=category,
                            price_mad=price,
                            scrape_timestamp=datetime.now().isoformat()
                        ))
                except Exception:
                    continue

        except Exception as e:
            print(f"Erreur scraping Cartec search '{query}': {e}")

        return items

    def search_parts(self, query: str, equipment_family: str) -> List[Dict[str, Any]]:
        cached = self._load_cache()
        if cached and query.lower() in cached.get("queries", {}):
            return cached["queries"][query.lower()]

        results = []

        config = self.CATEGORY_MAPPING.get(equipment_family, {})
        keywords = config.get("keywords", ["pièce auto"])

        for keyword in keywords:
            results.extend(self.scrape_autops_search(keyword, equipment_family))
            results.extend(self.scrape_cartec_search(keyword, equipment_family))

        if not results:
            fallback = config.get("fallback_price", 200.0)
            results = [PriceItem(
                site_name="Data Estimate",
                site_url="internal",
                product_name=f"Prix estimé {equipment_family.replace('_', ' ')}",
                product_brand="Estimé",
                product_category=equipment_family,
                price_mad=fallback,
                scrape_timestamp=datetime.now().isoformat()
            )]

        if not cached:
            cached = {"queries": {}}

        cached["queries"][query.lower()] = [asdict(item) for item in results]
        self._save_cache(cached)

        return cached["queries"][query.lower()]

    def refresh_all_prices(self) -> Dict[str, Any]:
        print("Démarrage du rafraîchissement quotidien des prix...")

        all_results = {
            "refresh_date": datetime.now().isoformat(),
            "refresh_type": "daily",
            "queries": {}
        }

        for family, config in self.CATEGORY_MAPPING.items():
            for keyword in config["keywords"]:
                query = f"{family} {keyword}"

                results = []
                try:
                    results.extend(self.scrape_autops_search(keyword, family))
                except Exception as e:
                    print(f"Erreur Autops {keyword}: {e}")

                try:
                    results.extend(self.scrape_cartec_search(keyword, family))
                except Exception as e:
                    print(f"Erreur Cartec {keyword}: {e}")

                if not results:
                    fallback = config.get("fallback_price", 200.0)
                    results = [PriceItem(
                        site_name="Data Estimate",
                        site_url="internal",
                        product_name=f"Prix estimé {keyword}",
                        product_brand="Estimé",
                        product_category=keyword,
                        price_mad=fallback,
                        scrape_timestamp=datetime.now().isoformat()
                    )]

                all_results["queries"][query.lower()] = [asdict(item) for item in results]

        self._save_cache(all_results)
        print(f"Rafraîchissement terminé. {len(all_results['queries'])} requêtes mises à jour.")

        return all_results
