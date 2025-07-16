import sqlite3

conn = sqlite3.connect('careconnect.db')
cursor = conn.cursor()

try:
    cursor.execute("ALTER TABLE reports ADD COLUMN prescription_filename TEXT")
    conn.commit()
    print("✅ Column 'prescription_filename' added successfully.")
except sqlite3.OperationalError as e:
    if "duplicate column name" in str(e):
        print("⚠️ Column 'prescription_filename' already exists.")
    else:
        print("❌ Error:", e)
finally:
    conn.close()
