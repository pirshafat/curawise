import sqlite3

# Connect to the database
conn = sqlite3.connect('careconnect.db')
cursor = conn.cursor()

# Create users table if it doesn't exist
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL,
        role TEXT NOT NULL
    )
''')

# Seed some users
users = [
    ('admin', 'admin123', 'admin'),
    ('doctor', '1234', 'doctor'),
    ('patient', 'abcd', 'patient')
]

# Insert users, ignoring duplicates
for username, password, role in users:
    try:
        cursor.execute('INSERT INTO users (username, password, role) VALUES (?, ?, ?)', (username, password, role))
    except sqlite3.IntegrityError:
        pass  # Ignore if user already exists

conn.commit()
conn.close()

print("✅ Users seeded successfully!")

