"""
Quick script to inspect database schema
"""
import sqlite3

conn = sqlite3.connect('db.sqlite3')
cursor = conn.cursor()

# List all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = cursor.fetchall()

print("All tables:")
for table in tables:
    print(f"  {table[0]}")

# Check if hotels_property exists
if ('hotels_property',) in tables:
    print("\nhotels_property columns:")
    cursor.execute("PRAGMA table_info(hotels_property)")
    columns = cursor.fetchall()
    for col in columns:
        print(f"  {col[1]:30} {col[2]:15}")
else:
    print("\nhotels_property table does NOT exist")

conn.close()
