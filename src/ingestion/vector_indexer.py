"""
Moteur de recherche RAG multimodal avec Reciprocal Rank Fusion (RRF).
Implémente le filtrage de permissions (RBAC) et la fusion texte/image.
"""

import os
import json
import math
import re
from typing import List, Dict, Any, Optional

CORPUS_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "corpus", "corpus_documents.json")

class MultimodalVectorIndexer:
    def __init__(self, corpus_path: str = CORPUS_PATH):
        self.corpus_path = os.path.abspath(corpus_path)
        self.chunks = self._load_corpus()

    def _load_corpus(self) -> List[Dict[str, Any]]:
        if os.path.exists(self.corpus_path):
            with open(self.corpus_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return []

    def _text_score(self, query: str, content: str) -> float:
        """Calcul de similarité textuelle lexicale / BM25 avec reconnaissance de racines françaises."""
        terms = re.findall(r"\w+", query.lower())
        if not terms:
            return 0.0
        content_lower = content.lower()
        score = 0.0
        for term in terms:
            if len(term) < 3:
                continue
            count = content_lower.count(term)
            if count > 0:
                score += 2.0 + math.log(1.0 + count)
            else:
                # Test de préfixe pour le français (ex: pneu / pneumatique, surchauffe / surchauffé)
                prefix = term[:4] if len(term) >= 4 else term
                prefix_count = content_lower.count(prefix)
                if prefix_count > 0:
                    score += 1.2 + math.log(1.0 + prefix_count)
        return score

    def _visual_score(self, visual_query: str, visual_desc: str) -> float:
        """Calcul de similarité sur les descriptions visuelles et schémas."""
        if not visual_query or not visual_desc:
            return 0.0
        return self._text_score(visual_query, visual_desc)

    def search_multimodal(
        self,
        query: str,
        visual_query: str = "",
        user_groups: Optional[List[str]] = None,
        top_k: int = 5,
        rrf_k: int = 60
    ) -> List[Dict[str, Any]]:
        """
        Recherche multimodale avec :
        1. Filtrage préalable par permissions RBAC.
        2. Recherche textuelle et recherche visuelle.
        3. Reciprocal Rank Fusion (RRF).
        """
        if user_groups is None:
            user_groups = ["groupe_standard"]

        # Rechargement dynamique du corpus à chaque recherche
        self.chunks = self._load_corpus()

        # Étape 1 : Filtrage par permissions
        eligible_chunks = [
            chunk for chunk in self.chunks
            if any(grp in user_groups for grp in chunk.get("authorized_groups", []))
        ]

        if not eligible_chunks:
            return []

        # Étape 2 : Ranking textuel
        ranked_by_text = sorted(
            eligible_chunks,
            key=lambda c: self._text_score(query, f"{c.get('title', '')} {c.get('content', '')}"),
            reverse=True
        )

        # Étape 3 : Ranking visuel
        ranked_by_visual = sorted(
            eligible_chunks,
            key=lambda c: self._visual_score(visual_query or query, c.get("visual_description", "")),
            reverse=True
        )

        # Étape 4 : Reciprocal Rank Fusion (RRF)
        # RRF_Score = sum(1 / (k + rank))
        rrf_scores: Dict[str, float] = {}
        chunk_map: Dict[str, Dict[str, Any]] = {}

        for rank, chunk in enumerate(ranked_by_text):
            uid = f"{chunk['document_id']}#p{chunk['page']}#{chunk['element_id']}"
            chunk_map[uid] = chunk
            rrf_scores[uid] = rrf_scores.get(uid, 0.0) + (1.0 / (rrf_k + rank + 1))

        for rank, chunk in enumerate(ranked_by_visual):
            uid = f"{chunk['document_id']}#p{chunk['page']}#{chunk['element_id']}"
            chunk_map[uid] = chunk
            rrf_scores[uid] = rrf_scores.get(uid, 0.0) + (1.0 / (rrf_k + rank + 1))

        # Tri final par score RRF
        sorted_uids = sorted(rrf_scores.items(), key=lambda item: item[1], reverse=True)
        results = []
        for uid, score in sorted_uids[:top_k]:
            item = dict(chunk_map[uid])
            item["rrf_score"] = round(score, 5)
            results.append(item)

        return results

# Instance globale
indexer = MultimodalVectorIndexer()
