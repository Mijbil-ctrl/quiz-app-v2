var answers = {};

function selectAnswer(qno, option) {
    answers[qno] = option;
}

function show(n) {
    let qs = document.getElementsByClassName("question");

    for (let i = 0; i < qs.length; i++) {
        qs[i].style.display = "none";
    }

    document.getElementById("q" + n).style.display = "block";
}

function next(n, total) {
    if (n < total) show(n + 1);
}

function prev(n) {
    if (n > 1) show(n - 1);
}

function jump(n) {
    show(n);
}

function startTimer(min) {
    let time = min * 60;

    setInterval(function () {
        let m = Math.floor(time / 60);
        let s = time % 60;

        document.getElementById("timer").innerHTML =
            "Time Left: " + m + ":" + s;

        time--;

        if (time <= 0) {
            alert("Time Over!");
            document.forms[0].submit();
        }

    }, 1000);
}
function saveQuestion(i) {

    let question = document.getElementById("text" + i).innerText;
    let subject = document.getElementById("subject" + i).value;
    let topic = document.getElementById("topic" + i).value;
    let subtopic = document.getElementById("subtopic" + i).value;

    fetch("/save", {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: `question=${question}&subject=${subject}&topic=${topic}&subtopic=${subtopic}`
    });

    alert("Saved to Question Bank!");
}
function submitQuiz() {

    let answers = {};

    let total = document.querySelectorAll(".question").length;

    for (let i = 1; i <= total; i++) {

        let selected = document.querySelector(`input[name="q${i}"]:checked`);

        if (selected) {
            answers[i] = selected.parentElement.innerText.trim();
        }
    }

    fetch("/submit", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ answers: answers })
    })
    .then(res => res.json())
    .then(data => {

        alert(
            "Score: " + data.score +
            "\nCorrect: " + data.correct +
            "\nWrong: " + data.wrong +
            "\nUnattempted: " + data.unattempted
        );

        reviewMode(data);
    });
}
function reviewMode(resultData) {

    fetch("current_quiz.json")
    .then(res => res.json())
    .then(questions => {

        questions.forEach((q, index) => {

            let qno = index + 1;

            let correct = q.correct;

            let selected = document.querySelector(`input[name="q${qno}"]:checked`);

            let options = document.querySelectorAll(`#q${qno} .options label`);

            options.forEach(opt => {

                let text = opt.innerText.trim();

                // Highlight correct answer
                if (text.startsWith(correct)) {
                    opt.classList.add("correct");
                }

                // Highlight wrong selection
                if (selected && opt.contains(selected) && text.charAt(0) !== correct) {
                    opt.classList.add("wrong");
                }
            });

            // Color navigation
            if (selected) {
                if (selected.parentElement.innerText.trim().startsWith(correct)) {
                    document.getElementById("nav" + qno).classList.add("correct");
                } else {
                    document.getElementById("nav" + qno).classList.add("wrong");
                }
            }
        });
    });
}

function markAttempted(qno) {
    document.getElementById("nav" + qno).classList.add("attempted");
}
