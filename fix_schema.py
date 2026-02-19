"""
Manually update database schema to match models
This fixes the migration state mismatch
"""
import sqlite3
import traceback

conn = sqlite3.connect('db.sqlite3')
cursor = conn.cursor()

print("Starting schema update...")

# Add new FK columns
try:
    cursor.execute("ALTER TABLE hotels_property ADD COLUMN city_id INTEGER")
    conn.commit()
    print("✓ Added city_id column")
except Exception as e:
    print(f"city_id error: {e}")
    traceback.print_exc()

try:
    cursor.execute("ALTER TABLE hotels_property ADD COLUMN locality_id INTEGER")
    conn.commit()
    print("✓ Added locality_id column")
except Exception as e:
    print(f"locality_id error: {e}")
    traceback.print_exc()

# Add intelligence signal columns
new_columns = [
    ("review_count", "INTEGER DEFAULT 0"),
    ("popularity_score", "INTEGER DEFAULT 0"),
    ("bookings_today", "INTEGER DEFAULT 0"),
    ("bookings_this_week", "INTEGER DEFAULT 0"),
    ("is_trending", "INTEGER DEFAULT 0"),
    ("has_free_cancellation", "INTEGER DEFAULT 1"),
    ("cancellation_hours", "INTEGER DEFAULT 24"),
    ("city_text", "VARCHAR(80)"),
]

for col_name, col_type in new_columns:
    try:
        cursor.execute(f"ALTER TABLE hotels_property ADD COLUMN {col_name} {col_type}")
        conn.commit()
        print(f"✓ Added {col_name} column")
    except Exception as e:
        print(f"{col_name} error: {e}")

# Copy old city data to city_text
try:
    cursor.execute("UPDATE hotels_property SET city_text = city")
    conn.commit()
    rows = cursor.rowcount
    print(f"✓ Copied city data to city_text ({rows} rows)")
except Exception as e:
    print(f"city copy error: {e}")
    traceback.print_exc()

conn.close()

print("\n✅ Schema update complete")
