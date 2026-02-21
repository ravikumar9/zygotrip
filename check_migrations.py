import sqlite3
conn = sqlite3.connect('db.sqlite3')
cursor = conn.cursor()
cursor.execute("SELECT app, name FROM django_migrations WHERE app='hotels' OR app='apps.hotels'")
for row in cursor.fetchall():
    print(f"{row[0]}: {row[1]}")
conn.close()