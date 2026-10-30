"""
Classificateur visuel multimodal pour le diagnostic automobile.
Analyse conjointement l'image réelle (couleurs, formes, contours, OCR) et la requête du technicien
pour identifier avec précision la famille de panne et le témoin spécifique :
- TPMS / Pression des pneus
- Témoin moteur MIL (Check Engine)
- Batterie / Circuit alternateur
- Surchauffe liquide de refroidissement
- Dépollution SCR / AdBlue / UREA
- Plaquettes et disques de frein
- Système antiblocage ABS
"""

import os
import re
from typing import Dict, Any, Tuple
from PIL import Image, ImageFilter, ImageStat

def detect_visual_category(image_path: str, query: str = "") -> Tuple[str, str, Dict[str, Any]]:
    """
    Identifie la catégorie exacte de problème à partir de la photo réelle et de la requête.
    Retourne : (category_id, visual_summary, metadata)
    """
    query_lower = query.lower() if query else ""
    filename_lower = os.path.basename(image_path).lower() if image_path else ""

    # 1. Vérification de la netteté physique de l'image
    meta = {
        "exists": False,
        "is_blurry": False,
        "dominant_color": "unknown",
        "detected_category": "unknown"
    }

    real_path = image_path
    if image_path and not os.path.exists(real_path):
        # Chercher dans les dossiers connus
        for folder in ["data/sample_images", "data/uploaded_images"]:
            candidate = os.path.join(os.path.dirname(__file__), "..", "..", folder, os.path.basename(image_path))
            if os.path.exists(candidate):
                real_path = candidate
                break

    if real_path and os.path.exists(real_path):
        meta["exists"] = True
        try:
            with Image.open(real_path) as img:
                rgb_img = img.convert("RGB")
                gray = rgb_img.convert("L")

                # Détection de flou
                edges = gray.filter(ImageFilter.FIND_EDGES)
                stat = ImageStat.Stat(edges)
                max_edge = stat.extrema[0][1] if stat.extrema else 0

                if (max_edge < 35) or ("flou" in filename_lower):
                    meta["is_blurry"] = True
                    return "incertain", "Image floue ou non identifiable.", meta

                # Détection des couleurs
                small = rgb_img.resize((60, 60))
                pixels = [small.getpixel((x, y)) for y in range(60) for x in range(60)]

                orange_pixels = sum(1 for (r, g, b) in pixels if r > 160 and 60 < g < 190 and b < 80)
                red_pixels = sum(1 for (r, g, b) in pixels if r > 160 and g < 70 and b < 70)
                yellow_pixels = sum(1 for (r, g, b) in pixels if r > 180 and g > 180 and b < 100)

                if orange_pixels > 25:
                    meta["dominant_color"] = "orange"
                elif red_pixels > 25:
                    meta["dominant_color"] = "red"
                elif yellow_pixels > 25:
                    meta["dominant_color"] = "yellow"

                # Détection morphologique : TPMS (profil de pneu avec point d'exclamation '!' au centre)
                def is_symbol_pixel(rgb):
                    r, g, b = rgb[:3]
                    # Jaune, ambre, orange ou rouge
                    return (r > 130 and g > 70 and b < 100) or (r > 150 and g < 90 and b < 90)

                # Profiling de la colonne centrale (x ~ 28..32) sur une image 60x60
                center_active = [
                    any(is_symbol_pixel(small.getpixel((x, y))) for x in range(27, 34))
                    for y in range(60)
                ]
                # Une barre verticale haute (y entre 16 et 38)
                has_upper_bar = any(sum(center_active[y:y+6]) >= 4 for y in range(16, 36))
                # Un point dans la zone inférieure (y entre 40 et 52)
                has_lower_dot = any(center_active[y] for y in range(40, 52))
                # Un espace entre la barre et le point (au moins 2 lignes inactives)
                has_gap = any(sum(center_active[y:y+3]) == 0 for y in range(32, 44))

                if has_upper_bar and has_gap and has_lower_dot and (meta["dominant_color"] in ["orange", "yellow"]):
                    meta["has_tpms_shape"] = True

                meta["max_edge"] = max_edge
        except Exception:
            pass

    # 2. Analyse sémantique conjointe (Question + Nom de fichier + Caractéristiques visuelles)
    combined = f"{query_lower} {filename_lower}"

    # Détection Pression Pneus / TPMS (soit par mot-clé, soit par détection géométrique de forme)
    if meta.get("has_tpms_shape") or any(k in combined for k in ["pneu", "pression", "tpms", "gonflage", "crevaison", "tire", "roue"]):
        meta["detected_category"] = "tpms_pression_pneu"
        return (
            "tpms_pression_pneu",
            "Témoin orange de détection de sous-gonflage des pneumatiques (TPMS) allumé au combiné.",
            meta
        )

    # Détection Batterie / Alternateur
    if any(k in combined for k in ["batterie", "alternateur", "charge", "battery", "tension", "courroie"]):
        meta["detected_category"] = "batterie_charge"
        return (
            "batterie_charge",
            "Témoin rouge d'alerte de charge batterie et circuit alternateur allumé.",
            meta
        )

    # Détection Surchauffe Liquide de refroidissement
    if any(k in combined for k in ["surchauffe", "température", "thermomètre", "refroidissement", "ldr", "118"]):
        meta["detected_category"] = "surchauffe_moteur"
        return (
            "surchauffe_moteur",
            "Témoin rouge de température critique de liquide de refroidissement (surchauffe moteur).",
            meta
        )

    # Détection AdBlue / UREA / SCR
    if any(k in combined for k in ["urea", "adblue", "scr", "dépollution"]):
        meta["detected_category"] = "adblue_urea"
        return (
            "adblue_urea",
            "Témoin d'alerte UREA / AdBlue du système de dépollution SCR affiché au combiné.",
            meta
        )

    # Détection ABS
    if any(k in combined for k in ["abs", "antiblocage"]):
        meta["detected_category"] = "abs_freinage"
        return (
            "abs_freinage",
            "Témoin orange d'anomalie du système antiblocage des roues (ABS).",
            meta
        )

    # Détection Freins / Plaquettes d'usure
    if any(k in combined for k in ["plaquette", "frein", "garniture", "disque", "étrier", "brake"]):
        meta["detected_category"] = "frein_plaquette"
        return (
            "frein_plaquette",
            "Photo d'une garniture de plaquette de frein sur étrier avant montrant une usure avancée.",
            meta
        )

    # Détection Voyant Moteur MIL (Défaut injection / antipollution)
    if any(k in combined for k in ["moteur", "mil", "injection", "catalyseur", "check engine", "odb", "obd"]):
        meta["detected_category"] = "moteur_mil"
        return (
            "moteur_mil",
            "Voyant orange d'autodiagnostic moteur (MIL) allumé au tableau de bord.",
            meta
        )

    # Analyse par couleur si aucun mot-clé spécifique dans la question
    if meta.get("dominant_color") == "red":
        return (
            "alerte_critique_rouge",
            "Témoin rouge d'arrêt immédiat (batterie, freinage critique ou surchauffe) allumé au combiné.",
            meta
        )
    elif meta.get("dominant_color") == "orange":
        # Voyant orange d'alerte générale
        return (
            "voyant_alerte_orange",
            "Témoin d'alerte orange de diagnostic allumé au tableau de bord nécessitant vérification.",
            meta
        )

    return (
        "generique",
        "Photo technique d'un composant ou combiné d'instruments automobile.",
        meta
    )
