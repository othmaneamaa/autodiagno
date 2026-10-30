import sys
sys.path.insert(0, '.')

from src.auth.auth_service import auth_service

print("=== Test d'authentification ===")
print("Users loaded:", list(auth_service.users.keys()))

for username, user in auth_service.users.items():
    print(f"\n{username}:")
    print(f"  Full name: {user['full_name']}")
    print(f"  Role: {user['role']}")
    print(f"  Hash: {user['password_hash'][:60]}...")

print("\n=== Tests d'auth ===")

# Test 1: tech_martin avec Tech1234!
result = auth_service.authenticate('tech_martin', 'Tech1234!')
print(f"tech_martin / Tech1234! : {result}")

# Test 2: expert_dubois
result = auth_service.authenticate('expert_dubois', 'Expert1234!')
print(f"expert_dubois / Expert1234! : {result}")

# Test 3: mauvais mot de passe
result = auth_service.authenticate('tech_martin', 'WrongPassword!')
print(f"tech_martin / WrongPassword! : {result}")

# Test 4: mauvais username
result = auth_service.authenticate('wronguser', 'Tech1234!')
print(f"wronguser / Tech1234! : {result}")
