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

    lines = text.split("\n")
    questions = []

    buffer = ""

    for line in lines:
        line = line.strip()

        if not line:
            continue

        # detect new question start (numbers like 1), 2), 3)
        if line[0].isdigit() and (")" in line[:4]):
            if buffer:
                questions.append(buffer)
            buffer = line
        else:
            buffer += " " + line

    if buffer:
        questions.append(buffer)

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

    questions = session.get("questions")

    if not questions:
        return "<h3>No questions loaded. Please upload a PDF first.</h3><a href='/'>Go Home</a>"

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
    

# ----------- PRACTICE MODE -----------

@app.route('/practice', methods=['GET', 'POST'])
def practice():

    conn = sqlite3.connect(DB)
    c = conn.cursor()

    if request.method == 'POST':

        subject = request.form['subject']
        topic = request.form['topic']
        subtopic = request.form['subtopic']
        time = int(request.form['time'])

        query = "SELECT question FROM questions WHERE 1=1"
        params = []

        if subject:
            query += " AND subject=?"
            params.append(subject)

        if topic:
            query += " AND topic=?"
            params.append(topic)

        if subtopic:
            query += " AND subtopic=?"
            params.append(subtopic)

        c.execute(query, params)
        data = c.fetchall()

        questions = [d[0] for d in data]

        session["questions"] = questions
        session["time"] = time

        return redirect(url_for("quiz"))

    c.execute("SELECT DISTINCT subject FROM questions")
    subjects = c.fetchall()

    c.execute("SELECT DISTINCT topic FROM questions")
    topics = c.fetchall()

    c.execute("SELECT DISTINCT subtopic FROM questions")
    subtopics = c.fetchall()

    conn.close()

    return render_template("practice.html",
                           subjects=subjects,
                           topics=topics,
                           subtopics=subtopics)

if __name__ == '__main__':
    import os
port = int(os.environ.get("PORT", 5000))
app.run(host="0.0.0.0", port=port)


