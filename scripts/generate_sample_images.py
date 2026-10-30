"""
Générateur d'images d'exemple réelles pour tester la fonctionnalité multimodale.
Crée 3 images techniques dans data/sample_images/ :
1. voyant_moteur_peugeot.png : Photo nette d'un combiné avec voyant moteur orange
2. plaquette_frein_usee.png : Photo d'une plaquette de frein avec cote critique 1.5mm
3. photo_floue_inconnue.png : Photo délibérément floue / sombre pour tester l'incertitude
"""

import os
from PIL import Image, ImageDraw, ImageFilter

def generate_samples():
    out_dir = os.path.join(os.path.dirname(__file__), "..", "data", "sample_images")
    os.makedirs(out_dir, exist_ok=True)

    # 1. Image 1 : Voyant moteur orange
    img1 = Image.new("RGB", (600, 400), color=(25, 28, 36))
    draw1 = ImageDraw.Draw(img1)
    # Cadre du combiné
    draw1.rectangle([30, 30, 570, 370], outline=(70, 75, 90), width=4)
    draw1.text((50, 50), "PEUGEOT 208 - COMBINÉ DIGITAL", fill=(180, 190, 210))
    draw1.text((50, 80), "VITESSE : 0 km/h | T° EAU : 90°C", fill=(130, 140, 160))

    # Dessin du voyant moteur (orange ambré standard #FF8C00)
    # Corps du moteur
    draw1.rectangle([230, 160, 370, 260], fill=(255, 140, 0), outline=(255, 180, 50), width=3)
    # Hélice / excroissance gauche
    draw1.rectangle([195, 185, 230, 235], fill=(255, 140, 0))
    # Bouchon haut
    draw1.rectangle([280, 135, 320, 160], fill=(255, 140, 0))
    # Éléments intérieurs
    draw1.ellipse([275, 190, 325, 230], outline=(25, 28, 36), width=4)

    draw1.text((215, 290), "TÉMOIN MIL ACTIF", fill=(255, 140, 0))
    img1.save(os.path.join(out_dir, "voyant_moteur_peugeot.png"))

    # 2. Image 2 : Plaquette de frein usée
    img2 = Image.new("RGB", (600, 400), color=(40, 40, 45))
    draw2 = ImageDraw.Draw(img2)
    draw2.text((50, 40), "ÉTRIER AVANT BOSCH - MESURE D'ÉPAISSEUR", fill=(220, 220, 220))

    # Disque de frein métallique
    draw2.rectangle([80, 100, 160, 340], fill=(160, 165, 175), outline=(200, 205, 215), width=2)
    draw2.text((90, 210), "DISQUE", fill=(30, 30, 30))

    # Support métallique de plaquette
    draw2.rectangle([200, 110, 260, 330], fill=(90, 95, 105), outline=(130, 135, 145), width=2)

    # Garniture résiduelle très mince (usure critique : 1.5 mm)
    draw2.rectangle([165, 120, 198, 320], fill=(180, 50, 40), outline=(220, 80, 70), width=2)
    draw2.text((280, 180), "◄ GARNITURE : 1.5 mm", fill=(255, 80, 80))
    draw2.text((280, 210), "(SEUIL MINIMAL LÉGAL : 2.0 mm)", fill=(255, 200, 80))
    draw2.text((280, 240), "ÉTAT : REMPLACEMENT IMPÉRATIF", fill=(255, 80, 80))

    img2.save(os.path.join(out_dir, "plaquette_frein_usee.png"))

    # 3. Image 3 : Photo floue et sombre (test d'incertitude)
    img3 = Image.new("RGB", (600, 400), color=(15, 15, 18))
    draw3 = ImageDraw.Draw(img3)
    # Éléments très vagues et floutés
    for i in range(10):
        draw3.ellipse([100 + i*30, 80 + i*20, 300 + i*20, 250 + i*10], fill=(45, 35, 30))
    # Application d'un fort flou gaussien
    img3 = img3.filter(ImageFilter.GaussianBlur(radius=22))
    img3.save(os.path.join(out_dir, "photo_floue_inconnue.png"))

    print(f"3 images générées avec succès dans : {out_dir}")

if __name__ == "__main__":
    generate_samples()
