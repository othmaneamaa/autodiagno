"""
Générateur de données d'entraînement pour le reranker (Triplets durs).
Question, Passage Positif (pertinent), Passage Négatif difficile (distracteur).
"""

import json
import os
import random
from typing import List, Dict, Any

def generate_hard_triplets(count: int = 1000) -> List[Dict[str, Any]]:
    """Génère un jeu de triplets réalistes pour les deux familles d'équipements."""
    base_scenarios = [
        {
            "query": "Que signifie le voyant moteur orange fixe allumé sur mon combiné ?",
            "family": "groupe_motopropulseur_electronique",
            "pos": "Le témoin autodiagnostic moteur (voyant orange représentant un bloc moteur) s'allume brièvement au contact. S'il reste allumé fixe, cela indique un dysfonctionnement du système d'injection ou de dépollution.",
            "pos_doc": "MANUEL_ATELIER_PEUGEOT_208_V2",
            "pos_page": 42,
            "neg": "Le témoin d'anomalie de charge batterie (voyant rouge batterie) indique un défaut d'alternateur ou de courroie d'accessoire. Couper les consommateurs électriques.",
            "neg_doc": "MANUEL_ATELIER_PEUGEOT_208_V2",
            "neg_page": 44
        },
        {
            "query": "Quelle est l'épaisseur minimale légale pour des plaquettes de frein avant ?",
            "family": "systeme_freinage_liaisons_au_sol",
            "pos": "L'épaisseur minimale admissible de la garniture de plaquette de frein avant est de 2,0 mm (hors support métallique). En deçà, un remplacement immédiat est impératif.",
            "pos_doc": "GUIDE_TECHNIQUE_FREINAGE_BOSCH_2023",
            "pos_page": 18,
            "neg": "L'épaisseur minimale de la piste de disque de frein ventilé avant après rectification est de 20,0 mm. Remplacer les disques par paire si la cote minimale est atteinte.",
            "neg_doc": "GUIDE_TECHNIQUE_FREINAGE_BOSCH_2023",
            "neg_page": 20
        },
        {
            "query": "Voyant UREA clignotant avec message service, que faire ?",
            "family": "groupe_motopropulseur_electronique",
            "pos": "Le voyant UREA fixe accompagné du témoin Service indique une autonomie en liquide AdBlue inférieure à 2400 km. Si le voyant clignote, l'autonomie restante est inférieure à 600 km.",
            "pos_doc": "MANUEL_CITROEN_C3_BLUEHDI",
            "pos_page": 65,
            "neg": "Le voyant de niveau mini carburant s'allume lorsque la réserve atteint environ 5 litres sur réservoir essence. Faire le plein rapidement.",
            "neg_doc": "MANUEL_CITROEN_C3_BLUEHDI",
            "neg_page": 32
        },
        {
            "query": "Témoin rouge cercle avec point d'exclamation au centre sur tableau de bord",
            "family": "systeme_freinage_liaisons_au_sol",
            "pos": "Le témoin rouge composé d'un cercle avec point d'exclamation entre parenthèses ((!)) indique une baisse critique du niveau de liquide de frein dans le bocal ou une défaillance du répartiteur.",
            "pos_doc": "GUIDE_TECHNIQUE_FREINAGE_BOSCH_2023",
            "pos_page": 24,
            "neg": "Le voyant ABS (cercle avec inscription ABS) indique une défaillance du système antiblocage des roues. Le freinage conventionnel reste opérationnel.",
            "neg_doc": "GUIDE_TECHNIQUE_FREINAGE_BOSCH_2023",
            "neg_page": 25
        }
    ]

    triplets = []
    for i in range(count):
        scenario = random.choice(base_scenarios)
        triplets.append({
            "id": f"trip_{i+1:04d}",
            "query": scenario["query"],
            "equipment_family": scenario["family"],
            "positive": {
                "text": scenario["pos"],
                "doc_id": scenario["pos_doc"],
                "page": scenario["pos_page"]
            },
            "hard_negative": {
                "text": scenario["neg"],
                "doc_id": scenario["neg_doc"],
                "page": scenario["neg_page"]
            }
        })

    return triplets

if __name__ == "__main__":
    out_dir = os.path.join(os.path.dirname(__file__), "..", "..", "data", "reranker_dataset")
    os.makedirs(out_dir, exist_ok=True)
    dataset = generate_hard_triplets(1200)

    # Séparation train (70%), val (15%), test (15%)
    n_train = int(len(dataset) * 0.70)
    n_val = int(len(dataset) * 0.15)

    train_data = dataset[:n_train]
    val_data = dataset[n_train:n_train+n_val]
    test_data = dataset[n_train+n_val:]

    with open(os.path.join(out_dir, "train.json"), "w", encoding="utf-8") as f:
        json.dump(train_data, f, indent=2, ensure_ascii=False)
    with open(os.path.join(out_dir, "val.json"), "w", encoding="utf-8") as f:
        json.dump(val_data, f, indent=2, ensure_ascii=False)
    with open(os.path.join(out_dir, "test.json"), "w", encoding="utf-8") as f:
        json.dump(test_data, f, indent=2, ensure_ascii=False)

    print(f"Dataset généré : {len(train_data)} train, {len(val_data)} val, {len(test_data)} test.")
