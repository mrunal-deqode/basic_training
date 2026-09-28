const questions = [
    {
        question: "Which language runs in a web browser?",
        options: ["Python", "JavaScript", "C++", "Java"],
        correctAnswerIndex: 1
    },
    {
        question: "What does HTML stand for?",
        options: [
            "Hyper Text Markup Language",
            "High Text Machine Language",
            "Hyperlinks Text Mark Language",
            "Home Tool Markup Language"
        ],
        correctAnswerIndex: 0
    },
    {
        question: "Which symbol is used for comments in JavaScript?",
        options: ["//", "<!-- -->", "#", "/* only */"],
        correctAnswerIndex: 0
    },
    {
        question: "Which method adds an element to the end of an array?",
        options: ["push()", "pop()", "shift()", "slice()"],
        correctAnswerIndex: 0
    },
    {
        question: "Which keyword creates a constant in JavaScript?",
        options: ["var", "let", "const", "constant"],
        correctAnswerIndex: 2
    },
    {
        question: "Which HTML tag is used for a paragraph?",
        options: ["<p>", "<h1>", "<div>", "<para>"],
        correctAnswerIndex: 0
    },
    {
        question: "Which CSS property changes text color?",
        options: ["font", "color", "text-color", "background"],
        correctAnswerIndex: 1
    },
    {
        question: "Which HTTP method is commonly used to retrieve data?",
        options: ["POST", "DELETE", "GET", "PATCH"],
        correctAnswerIndex: 2
    },
    {
        question: "What does CSS stand for?",
        options: [
            "Computer Style Sheets",
            "Cascading Style Sheets",
            "Creative Style System",
            "Colorful Style Sheets"
        ],
        correctAnswerIndex: 1
    },
    {
        question: "Which keyword is used to define a function in JavaScript?",
        options: ["function", "def", "func", "method"],
        correctAnswerIndex: 0
    }
];
// const questions = [];
const startButton = document.getElementById("start-btn");
const playAgainButton = document.getElementById("play-again-btn");

startButton.addEventListener("click", function () {
    game.start();

});

playAgainButton.addEventListener("click", function () {
    game.reset();
});

const game = {
    questions: questions,
    score: 0,
    lives: 3,
    currentQuestion: 0,
    currentQuestionIndex: null,
    usedQuestions: [],
    timer: null,
    timeLeft: 15,
    answerSelected: false,

    start() {
        console.log(this);
        console.log(this.score);

        document.getElementById("start-screen").style.display = "none";
        document.getElementById("game-screen").style.display = "block";

        this.loadQuestion();
    },

    loadQuestion() {
        try {
            this.answerSelected = false;
            if (!this.questions || this.questions.length === 0) {
                throw new Error("No questions available.");
            }
            const currentQuestion = this.questions.find(
                question =>
                    !question.question ||
                    !Array.isArray(question.options) ||
                    question.options.length !== 4 ||
                    typeof question.correctAnswerIndex !== "number"
            );

            if (currentQuestion) {
                throw new Error("Question data is malformed.");
            }

            let randomIndex;

            do {
                randomIndex = Math.floor(Math.random() * this.questions.length);
            } while (this.usedQuestions.includes(randomIndex));

            this.usedQuestions.push(randomIndex);
            this.currentQuestionIndex = randomIndex;

            const question = this.questions[randomIndex];

            console.log(question);
            document.getElementById("question").textContent = question.question;
            const answerButtons = document.querySelectorAll(".answer-btn");
            question.options.forEach(function (option, index) {
                answerButtons[index].textContent = option;
                answerButtons[index].disabled = false;

                answerButtons[index].classList.remove("correct");
                answerButtons[index].classList.remove("wrong");
            });
            answerButtons.forEach(function (button, index) {
                button.onclick = function () {
                    console.log("Selected option:", index);
                    game.checkAnswer(index, button);
                };
            });
            this.startTimer();
        } catch (error) {
            console.error(error);
            document.getElementById("question").textContent =
                "Sorry, something went wrong while loading the question.";

            const answerButtons = document.querySelectorAll(".answer-btn");

            answerButtons.forEach(function (button) {
                button.textContent = "";
                button.disabled = true;
            });
        }
    },

    checkAnswer(selectedIndex, button) {
        if (this.answerSelected) {
            return;
        }

        this.answerSelected = true;
        this.stopTimer();
        const question = this.questions[this.currentQuestionIndex];

        if (selectedIndex === question.correctAnswerIndex) {
            this.score++;
            button.classList.add("correct");
            document.getElementById("score").textContent = this.score;
            console.log("Correct!");
            console.log("Score:", this.score);
        } else {
            this.lives--;
            const livesElement = document.getElementById("lives");

            document.getElementById("lives").textContent = "❤️ ".repeat(this.lives).trim();

            livesElement.classList.remove("lose-life");

            void livesElement.offsetWidth;

            livesElement.classList.add("lose-life");
            // button.classList.add("wrong");
            if (button) {
                button.classList.add("wrong");
            }
            // document.getElementById("lives").textContent = this.lives;

            console.log("Wrong!");
            console.log("Lives:", this.lives);

            if (this.lives === 0) {
                this.gameOver();
                return;
            }
        }

        // this.nextQuestion();
        setTimeout(() => {
            this.nextQuestion();
        }, 500);
    },

    nextQuestion() {
        this.currentQuestion++;

        if (this.currentQuestion >= this.questions.length) {
            this.win();
            return;
        }

        this.loadQuestion();
    },

    gameOver() {
        this.stopTimer();
        document.getElementById("game-screen").style.display = "none";
        document.getElementById("end-screen").style.display = "block";

        document.getElementById("end-message").textContent = "You Loose!";
        document.getElementById("final-score").textContent = this.score;
    },

    win() {
        this.stopTimer();
        document.getElementById("game-screen").style.display = "none";
        document.getElementById("end-screen").style.display = "block";

        document.getElementById("end-message").textContent = "You Win!";
        document.getElementById("final-score").textContent = this.score;
    },

    reset() {
        this.answerSelected = false;
        this.score = 0;
        this.lives = 3;
        document.getElementById("lives").textContent = "❤️ ❤️ ❤️";
        this.currentQuestion = 0;
        this.usedQuestions = [];

        document.getElementById("score").textContent = this.score;
        document.getElementById("lives").textContent =
            "❤️ ".repeat(this.lives).trim();

        document.getElementById("end-screen").style.display = "none";
        document.getElementById("game-screen").style.display = "block";

        this.loadQuestion();
    },

    startTimer() {
        this.timeLeft = 15;
        document.getElementById("timer").classList.remove("warning");

        document.getElementById("timer").textContent = this.timeLeft;

        this.timer = setInterval(() => {
            this.timeLeft--;
            if (this.timeLeft <= 5) {
                document.getElementById("timer").classList.add("warning");
            }
            document.getElementById("timer").textContent = this.timeLeft;

            console.log("Time:", this.timeLeft);
            if (this.timeLeft === 0) {
                clearInterval(this.timer);
                this.checkAnswer(-1);
            }
        }, 1000);
    },

    stopTimer() {
        clearInterval(this.timer);
    }
};
