from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import os
from datetime import datetime
from werkzeug.utils import secure_filename
import fitz  # PyMuPDF
from openai import OpenAI

app = Flask(__name__)
app.secret_key = "careconnect-secret"
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

client = OpenAI()

# Dummy users
users = {
    "doctor": "1234",
    "patient": "abcd",
    "admin": "adminpass"
}

# Home page
@app.route('/')
def index():
    return render_template('login.html')

# Login
@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']

    if username in users and users[username] == password:
        session['username'] = username
        role = username  # assume username == role
        if role == "doctor":
            return redirect(url_for('doctor_dashboard'))
        elif role == "patient":
            return redirect(url_for('dashboard'))
        elif role == "admin":
            conn = sqlite3.connect('careconnect.db')
            c = conn.cursor()
            c.execute("SELECT username, filename, symptoms, ai_reply, doctor_reply, timestamp FROM reports")
            reports = c.fetchall()
            conn.close()
            return render_template('admin_dashboard.html', reports=reports)

    return render_template('login.html', error="Login failed. Try again.")

# Patient dashboard
@app.route('/dashboard')
def dashboard():
    try:
        username = session.get('username')
        conn = sqlite3.connect('careconnect.db')
        cursor = conn.cursor()
        cursor.execute('SELECT filename, symptoms, ai_reply, doctor_reply, timestamp FROM reports WHERE username = ?', (username,))
        reports = cursor.fetchall()
        conn.close()
        return render_template('patient_dashboard.html', user=username, report_history=reports)
    except Exception as e:
        return f"Error loading dashboard: {e}"

# Doctor dashboard
@app.route('/doctor_dashboard')
def doctor_dashboard():
    try:
        conn = sqlite3.connect('careconnect.db')
        cursor = conn.cursor()
        cursor.execute('SELECT username, filename, symptoms, ai_reply, timestamp, id, doctor_reply FROM reports')
        reports = cursor.fetchall()
        conn.close()
        return render_template('doctor_dashboard.html', reports=reports)
    except Exception as e:
        return f"Error loading doctor dashboard: {e}"

# Submit patient report
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
            # Extract text from PDF
            doc = fitz.open(filepath)
            text = ""
            for page in doc:
                text += page.get_text()

            # AI prompt
            prompt = f"""A patient uploaded a lab report with the following data:\n\n{text}\n\nSymptoms: {symptoms}\n\nAnalyze and give a health suggestion."""
            
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

    # Save to DB
    conn = sqlite3.connect('careconnect.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO reports (username, filename, symptoms, ai_reply, timestamp, doctor_reply)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (username, filename, symptoms, ai_suggestion, datetime.now(), None))
    conn.commit()
    conn.close()

    return redirect(url_for('dashboard'))

# Doctor reply route
@app.route('/reply/<int:report_id>', methods=['POST'])
def doctor_reply(report_id):
    reply = request.form['reply']
    conn = sqlite3.connect('careconnect.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE reports SET doctor_reply = ? WHERE id = ?', (reply, report_id))
    conn.commit()
    conn.close()
    return redirect(url_for('doctor_dashboard'))

# Logout
@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))

# Ensure uploads folder exists
if __name__ == '__main__':
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    app.run(debug=True)











