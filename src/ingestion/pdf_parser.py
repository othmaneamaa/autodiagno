"""
Extracteur de documents PDF via PyMuPDF (fitz).
Découpe les manuels techniques en passages textuels, tables et métadonnées
(document_id, page, element_id, equipment_family, authorized_groups).
Conforme à la Section 4.1 du document MAINTIDOC.
"""

import os
import json
from typing import List, Dict, Any, Optional

try:
    import pymupdf as fitz
except ImportError:
    try:
        import fitz
    except ImportError:
        fitz = None

class PDFManualParser:
    def __init__(self, output_dir: str = "./data/extracted_chunks"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def extract_pdf(
        self,
        pdf_path: str,
        document_id: str,
        equipment_family: str,
        authorized_groups: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Extrait le texte et les éléments visuels d'un fichier PDF page par page.
        """
        if not fitz:
            raise RuntimeError("PyMuPDF n'est pas installé dans l'environnement.")

        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"Fichier PDF introuvable : {pdf_path}")

        if authorized_groups is None:
            authorized_groups = ["groupe_standard"]

        doc = fitz.open(pdf_path)
        chunks = []

        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text("text").strip()

            if not text:
                continue

            # Découpage par paragraphes
            paragraphs = [p.strip() for p in text.split("\n\n") if len(p.strip()) > 30]

            for idx, p in enumerate(paragraphs):
                chunk = {
                    "document_id": document_id,
                    "version": "1.0",
                    "page": page_num + 1,
                    "element_id": f"p{page_num+1}_elem_{idx+1}",
                    "equipment_family": equipment_family,
                    "authorized_groups": authorized_groups,
                    "title": f"{document_id} - Page {page_num + 1}",
                    "content": p,
                    "visual_description": f"Extrait documentaire de la page {page_num + 1}"
                }
                chunks.append(chunk)

        doc.close()
        return chunks

    def save_chunks(self, chunks: List[Dict[str, Any]], filename: str = "extracted_corpus.json"):
        out_path = os.path.join(self.output_dir, filename)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(chunks, f, indent=2, ensure_ascii=False)
        return out_path

parser = PDFManualParser()
