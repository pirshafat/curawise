from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory
import sqlite3
import os
from datetime import datetime
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import fitz  # PyMuPDF
from openai import OpenAI
from dotenv import load_dotenv
from flask_talisman import Talisman

load_dotenv()

app = Flask(__name__)
Talisman(app, content_security_policy=None)
app.secret_key = "careconnect-secret"
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@app.route('/')
def index():
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']
        hashed_pw = generate_password_hash(password)

        conn = sqlite3.connect('careconnect.db')
        cursor = conn.cursor()
        try:
            cursor.execute('INSERT INTO users (username, password, role) VALUES (?, ?, ?)', (username, hashed_pw, role))
            conn.commit()
            flash("✅ Registered successfully. Please login.")
            return redirect(url_for('index'))
        except sqlite3.IntegrityError:
            return render_template('register.html', error="❌ Username already exists.")
        finally:
            conn.close()
    return render_template('register.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']

    conn = sqlite3.connect('careconnect.db')
    cursor = conn.cursor()
    cursor.execute('SELECT password, role FROM users WHERE username = ?', (username,))
    result = cursor.fetchone()
    conn.close()

    if result and check_password_hash(result[0], password):
        session['username'] = username
        session['role'] = result[1]
        return redirect(url_for('doctor_dashboard' if result[1] == 'doctor' else 'dashboard'))

    return render_template('login.html', error="Login failed. Try again.")

@app.route('/dashboard')
def dashboard():
    username = session.get('username')
    conn = sqlite3.connect('careconnect.db')
    cursor = conn.cursor()
    cursor.execute('SELECT filename, symptoms, ai_reply, doctor_reply, timestamp, prescription_filename FROM reports WHERE username = ?', (username,))
    reports = cursor.fetchall()
    conn.close()
    return render_template('patient_dashboard.html', user=username, report_history=reports)

@app.route('/doctor_dashboard')
def doctor_dashboard():
    conn = sqlite3.connect('careconnect.db')
    cursor = conn.cursor()
    cursor.execute('SELECT username, filename, symptoms, ai_reply, timestamp, id, doctor_reply, prescription_filename FROM reports')
    reports = cursor.fetchall()
    conn.close()
    return render_template('doctor_dashboard.html', reports=reports)

@app.route('/submit', methods=['POST'])
def submit():
    username = session.get('username')
    symptoms = request.form['symptoms']
    file = request.files['file']
    filename = None
    ai_suggestion = "AI Error: No response"

    if file:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        try:
            doc = fitz.open(filepath)
            text = "".join([page.get_text() for page in doc])
            prompt = f"A patient uploaded a lab report:\n\n{text}\n\nSymptoms: {symptoms}\n\nProvide medical analysis and health suggestions."

            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful medical assistant."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=300
            )
            ai_suggestion = response.choices[0].message.content.strip()

        except Exception as e:
            ai_suggestion = f"AI Error: {str(e)}"

    conn = sqlite3.connect('careconnect.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO reports (username, filename, symptoms, ai_reply, timestamp, doctor_reply, prescription_filename)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (username, filename, symptoms, ai_suggestion, datetime.now(), None, None))
    conn.commit()
    conn.close()

    return redirect(url_for('dashboard'))

@app.route('/reply/<int:report_id>', methods=['POST'])
def doctor_reply(report_id):
    reply = request.form['reply']
    conn = sqlite3.connect('careconnect.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE reports SET doctor_reply = ? WHERE id = ?', (reply, report_id))
    conn.commit()
    conn.close()
    return redirect(url_for('doctor_dashboard'))

@app.route('/upload_prescription/<int:report_id>', methods=['POST'])
def upload_prescription(report_id):
    file = request.files.get('prescription')
    if file:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        conn = sqlite3.connect('careconnect.db')
        cursor = conn.cursor()
        cursor.execute('UPDATE reports SET prescription_filename = ? WHERE id = ?', (filename, report_id))
        conn.commit()
        conn.close()
    return redirect(url_for('doctor_dashboard'))

@app.route('/download/<path:filename>')  # <- Path support for subdirs or long names
def download_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    app.run(debug=True)













