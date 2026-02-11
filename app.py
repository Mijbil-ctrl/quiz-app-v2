from flask import Flask, render_template, request, redirect, url_for, session
import PyPDF2
import os
import sqlite3

app = Flask(__name__)
import re

def parse_forum_solution(text):

    answers = {}

    pattern = r'Q\.(\d+)\)[\s\S]*?Ans\)\s*([A-Da-d])'

    matches = re.findall(pattern, text)

    for qno, ans in matches:
        answers[int(qno)] = ans.upper()

    return answers

app.secret_key = os.environ.get("SECRET_KEY", "super_secret_key_12345")
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"



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


import re


def parse_questions(text):

    questions = []

    # Split using real question markers like Q.1), Q.2) etc
    parts = re.split(r'Q\.\d+\)', text)

    for part in parts[1:]:   # ignore everything before first question
        lines = part.strip().split("\n")

        question_text = ""
        options = []

        for line in lines:
            line = line.strip()

            # REMOVE UNWANTED JUNK LINES
            if any(x in line for x in [
                "100% 75% 50% 0%",
                "Forum Learning Centre",
                "helpdesk@",
                "Page",
                "SFG",
                "admissions@",
                "forumias.com"
            ]):
                continue

            # Detect options (a), (b), (c), (d)
            if re.match(r'^[a-d]\)', line.lower()):
                option_clean = line[2:].strip()

                # ignore empty or garbage options
                if option_clean and len(option_clean) < 200:
                    options.append(option_clean)

            # Stop collecting if next question begins
            elif re.match(r'^Q\.\d+\)', line):
                break

            else:
                question_text += " " + line

        # FINAL CLEANUP OF QUESTION TEXT
        question_text = question_text.strip()

        # Remove extra unwanted patterns from question
        question_text = re.sub(r'100%\s*75%\s*50%\s*0%', '', question_text)
        question_text = re.sub(r'Forum.*', '', question_text)
        question_text = re.sub(r'Page\s*\d+.*', '', question_text)
        question_text = re.sub(r'\s+', ' ', question_text)

        # Only accept if real MCQ detected
        if question_text and len(options) >= 2:
            questions.append({
                "question": question_text,
                "options": options
            })

    return questions


# ---------- ROUTES ----------

@app.route('/')
def home():
    return render_template("upload.html")



import json



@app.route("/upload", methods=["POST"])
def upload():

    qp = request.files.get("question_pdf")
    sol = request.files.get("solution_pdf")

    if not qp or not sol:
        return "Both Question Paper and Solution PDFs are required"

    qp_path = os.path.join(UPLOAD_FOLDER, qp.filename)
    sol_path = os.path.join(UPLOAD_FOLDER, sol.filename)

    qp.save(qp_path)
    sol.save(sol_path)

    qp_text = extract_text(qp_path)
    sol_text = extract_text(sol_path)

    questions = parse_questions(qp_text)
    answers = parse_forum_solution(sol_text)

    print("Questions:", len(questions))
    print("Answers Found:", len(answers))

    for i, q in enumerate(questions):
        qno = i + 1
        q["correct"] = answers.get(qno)

   import json

    with open("current_quiz.json", "w", encoding="utf-8") as f:
        json.dump(questions, f)
    
    session["quiz_loaded"] = True


    return redirect(url_for("settings"))



@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if request.method == 'POST':
        session["time"] = int(request.form['time'])
        return redirect(url_for("quiz"))

    return render_template("settings.html")




@app.route('/quiz')
def quiz():

    try:
        # Check if a quiz has been uploaded
        if not session.get("quiz_loaded"):
            return "<h3>No questions loaded. Please upload a PDF first.</h3><a href='/'>Go Home</a>"

        # Load questions from server file instead of session
        if not os.path.exists("current_quiz.json"):
            return "<h3>Quiz file missing. Please upload again.</h3><a href='/'>Go Home</a>"

        with open("current_quiz.json", "r", encoding="utf-8") as f:
            questions = json.load(f)

        return render_template(
            "quiz.html",
            questions=questions,
            total=len(questions),
            time=session.get("time", 60)
        )

    except Exception as e:
        return f"<h3>Error in quiz page:</h3><pre>{str(e)}</pre>"





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
import re

def parse_forum_solution(text):

    answers = {}

    pattern = r'Q\.(\d+)\)[\s\S]*?Ans\)\s*([A-Da-d])'

    matches = re.findall(pattern, text)

    for qno, ans in matches:
        answers[int(qno)] = ans.upper()

    return answers
@app.route("/submit", methods=["POST"])
def submit():

    user_answers = request.json["answers"]
    with open("current_quiz.json", "r", encoding="utf-8") as f:
    questions = json.load(f)


    score = 0
    correct = 0
    wrong = 0
    unattempted = 0

    for i, q in enumerate(questions):

        qno = str(i+1)
        correct_ans = q.get("correct")

        user_ans = user_answers.get(qno)

        if not user_ans:
            unattempted += 1

        elif user_ans == correct_ans:
            score += 2
            correct += 1

        else:
            score -= 0.66
            wrong += 1

    result = {
        "score": round(score, 2),
        "correct": correct,
        "wrong": wrong,
        "unattempted": unattempted,
        "total": len(questions)
    }

    return result


