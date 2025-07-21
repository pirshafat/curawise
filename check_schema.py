import sqlite3

conn = sqlite3.connect('careconnect.db')
cursor = conn.cursor()

# List all table names
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()

print("\n📦 Tables in Database:")
for t in tables:
    print("-", t[0])

# Show schema for each table
print("\n🧱 Table Schemas:\n")
for table in [t[0] for t in tables]:
    print(f"--- {table} ---")
    cursor.execute(f"PRAGMA table_info({table});")
    for column in cursor.fetchall():
        print(column)
    print()

conn.close()
