from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import os
from datetime import datetime
from textblob import TextBlob
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "careconnect-secret"
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Dummy users for demonstration
users = {
    "doctor": "1234",
    "patient": "abcd",
    "admin": "adminpass"
}

@app.route('/')
def index():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']

    if username in users and users[username] == password:
        session['username'] = username
        role = username  # using username as role
        if role == "doctor":
            return redirect(url_for('doctor_dashboard'))
        elif role == "patient":
            return redirect(url_for('dashboard'))
        elif role == "admin":
            # Admin dashboard logic
            conn = sqlite3.connect('careconnect.db')
            c = conn.cursor()
            c.execute("SELECT username, filename, symptoms, ai_suggestion, doctor_reply, timestamp FROM reports")
            reports = c.fetchall()
            conn.close()
            return render_template('admin_dashboard.html', reports=reports)

    return render_template('login.html', error="Login failed. Try again.")

@app.route('/dashboard')
def dashboard():
    try:
        conn = sqlite3.connect('careconnect.db')
        cursor = conn.cursor()
        username = session.get('username')
        cursor.execute('SELECT filename, symptoms, ai_suggestion, doctor_reply, timestamp FROM reports WHERE username = ?', (username,))
        reports = cursor.fetchall()
        conn.close()
        return render_template('patient_dashboard.html', user=username, report_history=reports)
    except Exception as e:
        return f"Error loading dashboard: {e}"

@app.route('/doctor_dashboard')
def doctor_dashboard():
    try:
        conn = sqlite3.connect('careconnect.db')
        cursor = conn.cursor()
        cursor.execute('SELECT username, filename, symptoms, ai_suggestion, doctor_reply, timestamp FROM reports')
        reports = cursor.fetchall()
        conn.close()
        return render_template('doctor_dashboard.html', reports=reports)
    except Exception as e:
        return f"Error loading doctor dashboard: {e}"

@app.route('/submit', methods=['POST'])
def submit():
    username = session.get('username')
    symptoms = request.form['symptoms']
    file = request.files['file']
    filename = None

    if file:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

    # AI Suggestion using TextBlob
    blob = TextBlob(symptoms)
    ai_suggestion = "You may have an infection. Stay hydrated and monitor your temperature." if 'fever' in symptoms.lower() else "No immediate concern found."

    # Save to database
    conn = sqlite3.connect('careconnect.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO reports (username, filename, symptoms, ai_reply, timestamp, doctor_reply)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (username, filename, symptoms, ai_suggestion, datetime.now(), None))
    conn.commit()
    conn.close()

    return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    app.run(debug=True)







