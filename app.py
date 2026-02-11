from flask import Flask, render_template, request, redirect, url_for, session
import PyPDF2
import os
import sqlite3

app = Flask(__name__)
app.secret_key = "quiz_secret_key"

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

DB = "database.db"

# ---------- DATABASE SETUP ----------

def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS questions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        question TEXT,
        subject TEXT,
        topic TEXT,
        subtopic TEXT
    )
    """)

    conn.commit()
    conn.close()

init_db()

# ---------- PDF PROCESSING ----------

def extract_text(filepath):
    text = ""
    reader = PyPDF2.PdfReader(filepath)
    for page in reader.pages:
        text += page.extract_text() + "\n"
    return text

def parse_questions(text):
    parts = text.split("Q.")
    questions = []

    for p in parts[1:]:
        questions.append(p.strip())

    return questions


# ---------- ROUTES ----------

@app.route('/')
def home():
    return render_template("upload.html")


@app.route('/upload', methods=['POST'])
def upload():
    file = request.files['pdf']

    path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(path)

    text = extract_text(path)
    questions = parse_questions(text)

    session["questions"] = questions

    return redirect(url_for("settings"))


@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if request.method == 'POST':
        session["time"] = int(request.form['time'])
        return redirect(url_for("quiz"))

    return render_template("settings.html")


@app.route('/quiz')
def quiz():
    questions = session.get("questions", [])

    return render_template("quiz.html",
                           questions=questions,
                           total=len(questions),
                           time=session.get("time", 60))


# ---------- SAVE QUESTION TO BANK ----------

@app.route('/save', methods=['POST'])
def save():

    q = request.form['question']
    subject = request.form['subject']
    topic = request.form['topic']
    subtopic = request.form['subtopic']

    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("""
    INSERT INTO questions (question, subject, topic, subtopic)
    VALUES (?, ?, ?, ?)
    """, (q, subject, topic, subtopic))

    conn.commit()
    conn.close()

    return "saved"


# ---------- VIEW BANK ----------

@app.route('/bank')
def bank():

    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("SELECT * FROM questions")
    data = c.fetchall()

    conn.close()

    return render_template("bank.html", data=data)


if __name__ == '__main__':
    app.run(debug=True)

