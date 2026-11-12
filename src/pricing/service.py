"""
Service de pricing pour AutoClaim.
Gère l'affichage des prix de pièces dans l'interface Streamlit.
"""

import os
import json
from datetime import datetime
from typing import Dict, List, Any, Optional


class PricingService:
    """Service pour gérer les prix des pièces auto."""

    def __init__(self, storage_path: str = "./data/pricing"):
        self.storage_path = os.path.abspath(storage_path)
        self.cache_file = os.path.join(self.storage_path, "prices_cache.json")
        os.makedirs(self.storage_path, exist_ok=True)

    def get_cached_prices(self, query: str, equipment_family: str) -> List[Dict[str, Any]]:
        """
        Retourne les prix mis en cache pour une requête.
        Recherche intelligente : correspondance exacte > mots-clés pièce > véhicule > famille > fallback.
        """
        if not os.path.exists(self.cache_file):
            self._initialize_cache()

        try:
            with open(self.cache_file, "r", encoding="utf-8") as f:
                cache = json.load(f)

            queries = cache.get("queries", {})
            query_lower = query.lower()
            family_lower = equipment_family.lower()

            # 1. Correspondance exacte sur la query complète
            if query_lower in queries:
                return queries[query_lower]

            # 2. Recherche par mots-clés pièce dans la query (ex: "plaquettes", "disques", "batterie")
            part_keywords = {
                "plaquette": ["plaquette", "plaquettes"],
                "disque": ["disque", "disques"],
                "etrier": ["etrier", "étrier"],
                "abs": ["abs", "capteur abs"],
                "liquide_frein": ["liquide frein", "liquide de frein", "dot 4"],
                "batterie": ["batterie"],
                "alternateur": ["alternateur"],
                "bougie": ["bougie", "bougies"],
                "demarreur": ["demarreur", "démarreur"],
                "adblue": ["adblue", "urea", "scr"],
                "surchauffe": ["surchauffe", "calorstat", "pompe a eau", "pompe à eau", "vase expansion", "moto-ventilateur"],
            }

            # Chercher clé cache contenant le mot-clé pièce + famille
            for part_name, keywords in part_keywords.items():
                if any(kw in query_lower for kw in keywords):
                    # Priorité 1 : clé spécifique pièce + véhicule (ex: "frein renault clio 4")
                    # Priorité 2 : clé spécifique pièce (ex: "frein plaquettes")
                    for cache_key in queries:
                        cache_key_lower = cache_key.lower()
                        if family_lower in cache_key_lower and part_name in cache_key_lower:
                            return queries[cache_key]

            # 3. Recherche par véhicule dans la query (ex: "clio 4", "208", "golf")
            vehicle_keywords = ["clio 4", "clio iv", "208", "308", "c3", "c4", "golf", "polo", "passat", "a3", "a4", "q2", "q3", "classe a", "classe c", "megane", "captur", "zoe", "arona", "leon", "scala", "karoq", "octavia", "a1", "tt", "cla", "c5", "ds7", "5008", "3008"]
            for vehicle in vehicle_keywords:
                if vehicle in query_lower:
                    for cache_key in queries:
                        cache_key_lower = cache_key.lower()
                        if family_lower in cache_key_lower and vehicle in cache_key_lower:
                            return queries[cache_key]

            # 4. Fallback : première clé contenant la famille d'équipement
            for key, value in queries.items():
                if family_lower in key.lower():
                    return value

            # 5. Dernier recours : fallback hardcodé
            return self._get_fallback_prices(equipment_family)

        except Exception as e:
            print(f"Erreur lecture cache pricing: {e}")
            return self._get_fallback_prices(equipment_family)

    def _get_fallback_prices(self, equipment_family: str) -> List[Dict[str, Any]]:
        """Retourne des prix par défaut si pas de données disponibles."""
        fallback_prices = {
            "systeme_freinage_liaisons_au_sol": [
                {"site_name": "Autops", "site_url": "https://www.autops.ma",
                 "product_name": "Plaquettes de frein avant (jeu)", "product_brand": "Bosch",
                 "product_category": "Freinage", "price_mad": 180.0, "currency": "MAD",
                 "last_updated": "", "in_stock": True, "scrape_timestamp": ""},
                {"site_name": "Autops", "site_url": "https://www.autops.ma",
                 "product_name": "Disques de frein avant", "product_brand": "Textar",
                 "product_category": "Freinage", "price_mad": 250.0, "currency": "MAD",
                 "last_updated": "", "in_stock": True, "scrape_timestamp": ""},
                {"site_name": "Cartec", "site_url": "https://www.cartec.ma",
                 "product_name": "Étrier de frein avant", "product_brand": "TRW",
                 "product_category": "Freinage", "price_mad": 320.0, "currency": "MAD",
                 "last_updated": "", "in_stock": True, "scrape_timestamp": ""}
            ],
            "groupe_motopropulseur_electronique": [
                {"site_name": "Autops", "site_url": "https://www.autops.ma",
                 "product_name": "Batterie automobile 60Ah", "product_brand": "Varta",
                 "product_category": "Électrique", "price_mad": 850.0, "currency": "MAD",
                 "last_updated": "", "in_stock": True, "scrape_timestamp": ""},
                {"site_name": "Cartec", "site_url": "https://www.cartec.ma",
                 "product_name": "Alternateur 12V 120A", "product_brand": "Delco Remy",
                 "product_category": "Moteur", "price_mad": 1200.0, "currency": "MAD",
                 "last_updated": "", "in_stock": True, "scrape_timestamp": ""},
                {"site_name": "Autops", "site_url": "https://www.autops.ma",
                 "product_name": "Bougies d'allumage (jeu de 4)", "product_brand": "NGK",
                 "product_category": "Allumage", "price_mad": 120.0, "currency": "MAD",
                 "last_updated": "", "in_stock": True, "scrape_timestamp": ""}
            ]
        }

        return fallback_prices.get(equipment_family, [
            {"site_name": "Estimé", "site_url": "",
             "product_name": "Pièce estimée", "product_brand": "-",
             "product_category": equipment_family, "price_mad": 200.0, "currency": "MAD",
             "last_updated": "", "in_stock": True, "scrape_timestamp": ""}
        ])

    def _initialize_cache(self):
        """Initialise le fichier de cache vide."""
        cache = {"refresh_date": datetime.now().isoformat(), "refresh_type": "initial", "queries": {}}
        with open(self.cache_file, "w", encoding="utf-8") as f:
            json.dump(cache, f, indent=2, ensure_ascii=False)

    def calculate_total_cost(self, parts: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        Calcule le coût total d'une liste de pièces.
        """
        total = sum(p.get("price_mad", 0) for p in parts)
        avg_price = total / len(parts) if parts else 0

        return {
            "total_mad": round(total, 2),
            "average_mad": round(avg_price, 2),
            "parts_count": len(parts)
        }

    def get_parts_by_category(self, equipment_family: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Retourne les pièces groupées par type pour une famille d'équipement.
        """
        parts = self.get_cached_prices("", equipment_family)

        grouped = {}
        for part in parts:
            category = part.get("product_category", "Autre")
            if category not in grouped:
                grouped[category] = []
            grouped[category].append(part)

        return grouped

    def format_price_display(self, price_mad: float) -> str:
        """Formate un prix en MAD pour l'affichage."""
        return f"{price_mad:,.2f} MAD"

    def format_currency(self, amount: float, currency: str = "MAD") -> str:
        """Formate un montant avec la devise."""
        if currency == "MAD":
            return f"{amount:,.2f} MAD"
        return f"{amount:,.2f} {currency}"


# Instance globale
pricing_service = PricingService()
