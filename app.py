# app.py
from flask import Flask, render_template, request, redirect, url_for
import os
import sqlite3
from werkzeug.utils import secure_filename
from datetime import datetime

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['DATABASE'] = 'careconnect.db'

# Dummy login (no real auth for now)
users = {"doctor": "1234", "patient": "abcd"}

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# ----------------------------
# Database Setup
# ----------------------------
def init_db():
    with sqlite3.connect(app.config['DATABASE']) as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS reports (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT,
                        filename TEXT,
                        symptoms TEXT,
                        ai_reply TEXT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                    )''')
        conn.commit()

# ----------------------------
# Fake AI Response Generator
# ----------------------------
def generate_fake_ai_reply(symptoms):
    reply = ""
    s = symptoms.lower()

    if "fever" in s:
        reply += "You may have an infection. Stay hydrated and monitor your temperature.\n"
    if "headache" in s:
        reply += "Consider resting in a dark room and drinking water.\n"
    if reply == "":
        reply = "Thank you for submitting your symptoms. A doctor will review them shortly."

    return reply.strip()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if users.get(username) == password:
            if username == "doctor":
                return redirect(url_for('doctor_dashboard'))
            else:
                return redirect(url_for('patient_dashboard'))
        else:
            return "Login failed. Try again."
    return render_template('login.html')

@app.route('/dashboard/patient', methods=['GET', 'POST'])
def patient_dashboard():
    ai_reply = None
    filename = None
    symptoms = None
    user = "patient"

    if request.method == 'POST':
        file = request.files['file']
        symptoms = request.form['symptoms']
        if file:
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            ai_reply = generate_fake_ai_reply(symptoms)

            # Save to DB
            with sqlite3.connect(app.config['DATABASE']) as conn:
                c = conn.cursor()
                c.execute("INSERT INTO reports (username, filename, symptoms, ai_reply) VALUES (?, ?, ?, ?)",
                          (user, filename, symptoms, ai_reply))
                conn.commit()

    return render_template('dashboard.html', user=user, filename=filename, symptoms=symptoms, ai_reply=ai_reply)

@app.route('/dashboard/doctor')
def doctor_dashboard():
    with sqlite3.connect(app.config['DATABASE']) as conn:
        c = conn.cursor()
        c.execute("SELECT username, filename, symptoms, ai_reply, timestamp FROM reports ORDER BY timestamp DESC")
        reports = c.fetchall()
    return render_template('doctor_dashboard.html', reports=reports)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
