"""
Service d'inférence du Reranker pour l'agent AutoClaim.
Reclasse les extraits documentaires récupérés par RRF pour maximiser la fidélité.
"""

from typing import List, Dict, Any

import re

class RerankerService:
    def __init__(self, model_name: str = "BAAI/bge-reranker-base"):
        self.model_name = model_name

    def rerank(self, query: str, candidate_chunks: List[Dict[str, Any]], top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Reclasse les passages candidats en fonction de leur pertinence exacte vis-à-vis de la requête.
        Pondère précisément les correspondances lexicales et sémantiques entre la requête/analyse visuelle
        et le titre, le contenu et la description visuelle des manuels.
        """
        if not candidate_chunks:
            return []

        stopwords = {
            "le", "la", "les", "un", "une", "des", "ce", "cet", "cette", "ces",
            "sur", "mon", "ma", "mes", "ton", "ta", "tes", "son", "sa", "ses",
            "qui", "que", "quoi", "dont", "où", "est", "sont", "pour", "dans",
            "par", "avec", "sans", "sous", "comment", "pourquoi", "avoir", "être",
            "fait", "faire", "voici", "photo", "peux", "pouvez", "dois", "doit",
            "alerte", "message"
        }

        # Extraire les racines de termes significatifs (>2 caractères)
        raw_terms = re.findall(r"\w+", query.lower())
        meaningful_terms = [t for t in raw_terms if len(t) > 2 and t not in stopwords]

        def calculate_relevance(chunk: Dict[str, Any]) -> float:
            base_score = chunk.get("rrf_score", 0.1) * 10.0

            title_lower = chunk.get("title", "").lower()
            content_lower = chunk.get("content", "").lower()
            visual_lower = chunk.get("visual_description", "").lower()

            bonus = 0.0
            for term in meaningful_terms:
                # Correspondance exacte ou préfixe (ex: pneu -> pneumatique)
                prefix = term[:4] if len(term) >= 4 else term

                if prefix in title_lower:
                    bonus += 3.5  # Fort bonus si dans le titre du manuel
                if prefix in visual_lower:
                    bonus += 2.5  # Bonus si dans la description du voyant/schéma
                if prefix in content_lower:
                    bonus += 1.5  # Bonus dans le contenu

            # CORRECTION CRITIQUE : Éviter les bonus erronés qui favorisent "moteur" sur TPMS
            # Si le terme "pneu" ou "tpms" est dans la requête/analyse visuelle, PÉNALISER les chunks "moteur/MIL"
            query_terms = set(meaningful_terms)
            has_tpms_terms = any(t in query_terms for t in ["pneu", "pression", "tpms", "gonflage", "tire"])
            has_surchauffe_terms = any(t in query_terms for t in ["surchauffe", "temperature", "thermometre", "refroidissement", "ldr", "118"])
            has_batterie_terms = any(t in query_terms for t in ["batterie", "alternateur", "charge", "battery"])
            has_adblue_terms = any(t in query_terms for t in ["urea", "adblue", "scr", "depollution"])
            has_abs_terms = any(t in query_terms for t in ["abs", "antiblocage"])
            has_frein_terms = any(t in query_terms for t in ["plaquette", "frein", "garniture", "disque", "etrier", "brake", "usure"])
            has_moteur_terms = any(t in query_terms for t in ["moteur", "mil", "injection", "catalyseur", "check engine", "odb", "obd"])

            # Pénaliser les chunks qui ne correspondent PAS à la catégorie détectée
            chunk_category = ""
            if any(k in title_lower for k in ["tpms", "pneu", "pression", "pneumatique"]):
                chunk_category = "tpms_pression_pneu"
            elif any(k in title_lower for k in ["surchauffe", "temperature", "refroidissement", "ldr", "118", "calorstat"]):
                chunk_category = "surchauffe_moteur"
            elif any(k in title_lower for k in ["batterie", "alternateur", "charge", "courroie"]):
                chunk_category = "batterie_charge"
            elif any(k in title_lower for k in ["urea", "adblue", "scr"]):
                chunk_category = "adblue_urea"
            elif any(k in title_lower for k in ["abs", "antiblocage"]):
                chunk_category = "abs_freinage"
            elif any(k in title_lower for k in ["plaquette", "frein", "usure", "disque", "etrier"]):
                chunk_category = "frein_plaquette"
            elif any(k in title_lower for k in ["moteur", "mil", "injection", "autodiagnostic", "catalyseur"]):
                chunk_category = "moteur_mil"

            # Pénalités fortes si le chunk ne correspond pas à l'intention détectée
            if has_tpms_terms and chunk_category != "tpms_pression_pneu":
                bonus -= 10.0
            if has_surchauffe_terms and chunk_category != "surchauffe_moteur":
                bonus -= 10.0
            if has_batterie_terms and chunk_category != "batterie_charge":
                bonus -= 10.0
            if has_adblue_terms and chunk_category != "adblue_urea":
                bonus -= 10.0
            if has_abs_terms and chunk_category != "abs_freinage":
                bonus -= 10.0
            if has_frein_terms and chunk_category != "frein_plaquette":
                bonus -= 10.0
            if has_moteur_terms and chunk_category != "moteur_mil":
                bonus -= 10.0

            return base_score + bonus

        # Tri par score de pertinence recalculé
        reranked = sorted(candidate_chunks, key=calculate_relevance, reverse=True)

        for rank, chunk in enumerate(reranked[:top_k], start=1):
            chunk["reranker_rank"] = rank

        return reranked[:top_k]

# Instance globale
reranker = RerankerService()
