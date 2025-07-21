import sqlite3

# Connect to SQLite database
conn = sqlite3.connect('curawise.db')
cursor = conn.cursor()

# Create Patients Table
cursor.execute('''
CREATE TABLE IF NOT EXISTS patients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    email TEXT UNIQUE,
    password TEXT
)
''')

# Create Doctors Table
cursor.execute('''
CREATE TABLE IF NOT EXISTS doctors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    email TEXT UNIQUE,
    password TEXT,
    specialization TEXT,
    status TEXT DEFAULT 'approved'
)
''')

# Create Cases Table
cursor.execute('''
CREATE TABLE IF NOT EXISTS cases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_email TEXT,
    doctor_email TEXT,
    report_text TEXT,
    ai_suggestion TEXT,
    specialization TEXT,
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    prescription_filename TEXT
)
''')

# Insert Patients
patients = [
    ("Sania", "sania@gmail.com", "saniapass"),
    ("Shazia", "shazia@gmail.com", "shaziapass")
]

for p in patients:
    cursor.execute("INSERT OR IGNORE INTO patients (name, email, password) VALUES (?, ?, ?)", p)

# Insert Doctors
doctors = [
    ("Numariq", "numariq@gmail.com", "numariqpass", "general physician", "approved"),
    ("Atfar", "atfar@gmail.com", "atfarpass", "dermatologist", "approved")
]

for d in doctors:
    cursor.execute("INSERT OR IGNORE INTO doctors (name, email, password, specialization, status) VALUES (?, ?, ?, ?, ?)", d)

# Confirm and close
conn.commit()
conn.close()

print("✅ Database initialized with Sania, Shazia, Numariq, and Atfar.")
