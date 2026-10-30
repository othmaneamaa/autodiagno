import base64
import hashlib
import os
import json

def hash_password(password):
    salt = base64.b64encode(os.urandom(16)).decode('utf-8')
    dk = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
    return f'{salt}${dk.hex()}'

users = {
    'tech_martin': {
        'username': 'tech_martin',
        'full_name': 'Jean Martin (Technicien Diagnostic)',
        'password_hash': hash_password('Tech1234!'),
        'role': 'technicien',
        'authorized_groups': ['groupe_standard'],
        'department': 'Atelier Mécanique & Diagnostic Rapide',
        'created_at': '2026-01-15'
    },
    'expert_dubois': {
        'username': 'expert_dubois',
        'full_name': 'Sophie Dubois (Expert Sinistres & Devis)',
        'password_hash': hash_password('Expert1234!'),
        'role': 'expert_valideur',
        'authorized_groups': ['groupe_standard', 'groupe_expert'],
        'department': 'Pôle Expertise & Garantie Constructeur',
        'created_at': '2026-01-10'
    },
    'flotte_durand': {
        'username': 'flotte_durand',
        'full_name': 'Marc Durand (Gestionnaire de Flotte)',
        'password_hash': hash_password('Flotte1234!'),
        'role': 'gestionnaire_flotte',
        'authorized_groups': ['groupe_standard'],
        'department': 'Supervision Parc Véhicules & Contrats',
        'created_at': '2026-01-20'
    },
    'admin_master': {
        'username': 'admin_master',
        'full_name': 'Alexandre Laurent (Directeur Technique & Admin)',
        'password_hash': hash_password('Admin1234!'),
        'role': 'admin',
        'authorized_groups': ['groupe_standard', 'groupe_expert', 'admin'],
        'department': 'Direction Technique & Systèmes d\'Information',
        'created_at': '2026-01-01'
    }
}

db_path = os.path.join(os.path.dirname(__file__), 'data', 'synthetic', 'users_database.json')
with open(db_path, 'w', encoding='utf-8') as f:
    json.dump(users, f, indent=2, ensure_ascii=False)

print('Users database created with correct hashes!')
for u, v in users.items():
    print(f'  {u}: {v["password_hash"][:60]}...')