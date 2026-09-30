import random


class QuizGame:
    """Manage the quiz game."""

    def __init__(self, questions_list):
        self.questions = questions_list
        self.score = 0
        self.total_questions = len(questions_list)

    def start(self):
        """Start the quiz game."""
        print("Welcome to the Python Quiz!")

        answer = input("Are you ready to play? (yes/no): ")

        if answer.strip().lower() == "yes":
            self.play()
        else:
            print("Have a great day! Come back when you're ready to play.")

    def play(self):
        """Run the quiz game."""
        while self.questions:
            question = self.get_next_question()

            print("Q.)", question["question"])
            user_answer = input("Your answer: ")

            if self.check_answer(question, user_answer):
                print("Correct!")
                print(f"Current score: {self.score}")
            else:
                print("Incorrect!")
                print(f"Current score: {self.score}")

            print()
        self.show_result()

    def get_next_question(self):
        """Return a random question and remove it from the queue."""
        question = random.choice(self.questions)
        self.questions.remove(question)
        return question

    def check_answer(self, question, user_answer):
        """Check the user's answer and update the score."""
        if user_answer.strip().lower() == question["answer"].strip().lower():
            self.score += 1
            return True

        return False

    def calculate_marks(self):
        """Calculate the marks obtained in the quiz."""
        return (self.score / self.total_questions) * 100

    def show_result(self):
        """Display the final quiz result."""
        marks = self.calculate_marks()

        print("Thank you for playing this small quiz game!")
        print(f"You answered {self.score} questions correctly!")
        print(f"Marks obtained: {marks}")
        print("BYE!")


questions = [
    {
        "question": "What keyword is used to define a function in Python?",
        "answer": "def",
    },
    {
        "question": "What data type is used to store True or False?",
        "answer": "bool",
    },
    {
        "question": "Which symbol is used for comments in Python?",
        "answer": "#",
    },
    {
        "question": "What function is used to display output in Python?",
        "answer": "print",
    },
    {
        "question": "Which keyword is used to create a class in Python?",
        "answer": "class",
    },
]

# question = random.choice(questions)

# print(question["question"])
# print(question["answer"])

# questions.remove(question)

# print(len(questions))

game = QuizGame(questions)
# question = game.play()
# game.play()
game.start()
# print("Final Score:", game.calculate_marks())

# print(question["question"])
# print(question["answer"])
# print(len(game.questions))

# question = game.get_next_question()

# user_answer = input(f"{question['question']}\nYour answer: ")

# if game.check_answer(question, user_answer):
#     print("Correct!")
# else:
#     print("Incorrect!")

# print("Score:", game.score)
