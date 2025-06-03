import sqlite3

conn = sqlite3.connect("database.db")
cursor = conn.cursor()

try:
    cursor.execute("ALTER TABLE položka ADD COLUMN user TEXT")
    print("succes")
except sqlite3.OperationalError as e:
    print(f"chyba: {e}")

conn.commit()
conn.close()