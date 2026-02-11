from flask import Flask, render_template, request, redirect, url_for, session
import PyPDF2
import os

app = Flask(__name__)
app.secret_key = "quiz_secret_key"

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

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


@app.route('/submit', methods=['POST'])
def submit():
    questions = session.get("questions", [])
    total = len(questions)

    answers = request.form.getlist("answer")

    correct = 0
    wrong = 0

    for a in answers:
        if a == "correct":
            correct += 1
        elif a == "wrong":
            wrong += 1

    score = correct * 2 - wrong * 0.66

    return render_template("result.html",
                           total=total,
                           correct=correct,
                           wrong=wrong,
                           score=round(score, 2))


if __name__ == '__main__':
    app.run(debug=True)
