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
