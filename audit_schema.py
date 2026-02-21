import sqlite3
import os

db_path = 'db.sqlite3'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get list of all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()

print("DATABASE SCHEMA CHECK")
print("=" * 60)
print(f"Total tables: {len(tables)}")
print()

# Critical tables for auth and search
critical_tables = [
    'accounts_user',
    'accounts_role', 
    'accounts_userrole',
    'hotels_property',
    'core_city',
    'core_locality'
]

print("CRITICAL TABLES CHECK:")
existing_tables = [t[0] for t in tables]
for table in critical_tables:
    status = "EXISTS" if table in existing_tables else "MISSING"
    print(f"  {table}: {status}")

# Check key columns for auth
print()
print("AUTH SCHEMA CHECK:")
cursor.execute("PRAGMA table_info(accounts_user);")
auth_cols = cursor.fetchall()
auth_col_names = [col[1] for col in auth_cols]
print(f"  accounts_user columns: {len(auth_col_names)}")
print(f"    - email: {'YES' if 'email' in auth_col_names else 'NO'}")
print(f"    - full_name: {'YES' if 'full_name' in auth_col_names else 'NO'}")
print(f"    - username: {'NO' if 'username' not in auth_col_names else 'YES (WRONG!)'}")
print(f"    - first_name: {'NO' if 'first_name' not in auth_col_names else 'YES (WRONG!)'}")

# Check hotels_property schema
print()
print("HOTELS SCHEMA CHECK:")
cursor.execute("PRAGMA table_info(hotels_property);")
hotels_cols = cursor.fetchall()
hotels_col_names = [col[1] for col in hotels_cols]
print(f"  hotels_property columns: {len(hotels_col_names)}")
required_hotel_cols = ['id', 'name', 'city_id', 'locality_id', 'rating', 'review_count']
for col in required_hotel_cols:
    print(f"    - {col}: {'YES' if col in hotels_col_names else 'NO'}")

conn.close()