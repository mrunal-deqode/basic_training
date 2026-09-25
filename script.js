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

    start() {
        console.log(this);
        console.log(this.score);

        document.getElementById("start-screen").style.display = "none";
        document.getElementById("game-screen").style.display = "block";

        this.loadQuestion();
    },

    loadQuestion() {
        const question = this.questions[this.currentQuestion];

        console.log(question);
        document.getElementById("question").textContent = question.question;
        const answerButtons = document.querySelectorAll(".answer-btn");
        question.options.forEach(function (option, index) {
            answerButtons[index].textContent = option;
        });
        answerButtons.forEach(function (button, index) {
            button.onclick = function () {
                console.log("Selected option:", index);
                game.checkAnswer(index);
            };
        });
    },

    checkAnswer(selectedIndex) {
        const question = this.questions[this.currentQuestion];

        if (selectedIndex === question.correctAnswerIndex) {
            this.score++;
            document.getElementById("score").textContent = this.score;
            console.log("Correct!");
            console.log("Score:", this.score);
        } else {
            this.lives--;

            document.getElementById("lives").textContent = this.lives;

            console.log("Wrong!");
            console.log("Lives:", this.lives);

            if (this.lives === 0) {
                this.gameOver();
                return;
            }
        }

        this.nextQuestion();
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
        document.getElementById("game-screen").style.display = "none";
        document.getElementById("end-screen").style.display = "block";

        document.getElementById("end-message").textContent = "Game Over";
        document.getElementById("final-score").textContent = this.score;
    },

    win() {
        document.getElementById("game-screen").style.display = "none";
        document.getElementById("end-screen").style.display = "block";

        document.getElementById("end-message").textContent = "You Win!";
        document.getElementById("final-score").textContent = this.score;
    },

    reset() {
        this.score = 0;
        this.lives = 3;
        this.currentQuestion = 0;

        document.getElementById("score").textContent = this.score;
        document.getElementById("lives").textContent = this.lives;

        document.getElementById("end-screen").style.display = "none";
        document.getElementById("game-screen").style.display = "block";

        this.loadQuestion();
    }
};
