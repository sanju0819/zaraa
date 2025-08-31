import random

QUOTES = [
    "Believe in yourself!",
    "Every day is a new opportunity.",
    "Mythology teaches us courage.",
]

def random_quote():
    return random.choice(QUOTES)

QUIZ = {
    "What is 2+2?": "4",
    "Who is Arjuna?": "A warrior in Mahabharata"
}

def ask_quiz():
    question = random.choice(list(QUIZ.keys()))
    return question, QUIZ[question]
