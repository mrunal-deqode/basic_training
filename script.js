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

startButton.addEventListener("click", function () {
    game.start();

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
            };
        });
    }
};
