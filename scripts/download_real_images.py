"""
Télécharge de vraies photographies réelles libres de droits depuis Wikimedia Commons.
Permet d'avoir des cas 100% réels et concrets pour la démonstration.
"""

import os
import urllib.request

def download_real_photos():
    out_dir = os.path.join(os.path.dirname(__file__), "..", "data", "sample_images")
    os.makedirs(out_dir, exist_ok=True)

    images = {
        "vrai_voyant_moteur.jpg": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/cd/Check_engine_light.jpg/640px-Check_engine_light.jpg",
        "vraies_plaquettes_frein.jpg": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a2/Brake_pads.jpg/640px-Brake_pads.jpg"
    }

    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

    for filename, url in images.items():
        filepath = os.path.join(out_dir, filename)
        print(f"Téléchargement de {filename} depuis {url}...")
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=10) as response, open(filepath, 'wb') as out_file:
                out_file.write(response.read())
            print(f"-> Succès : {filename} ({os.path.getsize(filepath)} octets)")
        except Exception as e:
            print(f"-> Échec du téléchargement pour {filename} : {e}")

if __name__ == "__main__":
    download_real_photos()
