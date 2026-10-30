import os
db_path = os.path.join(os.path.dirname(__file__), "data", "synthetic", "users_database.json")
if os.path.exists(db_path):
    os.remove(db_path)
    print(f"Deleted: {db_path}")
else:
    print("File not found")