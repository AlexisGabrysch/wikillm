# src/populate_data.py

from databasebis import DatabaseManager
import hashlib
import random
from datetime import datetime
import os

def add_simulated_users(db: DatabaseManager):
    users = [
        {"first_name": "Alice", "last_name": "Smith", "username": "alice", "password": "password123"},
        {"first_name": "Bob", "last_name": "Johnson", "username": "bob", "password": "securepass"},
        {"first_name": "Charlie", "last_name": "Lee", "username": "charlie", "password": "charliepwd"},
    ]
    for user in users:
        success = db.add_user(user["first_name"], user["last_name"], user["username"], user["password"])
        if not success:
            print(f"Username {user['username']} already exists.")

def add_simulated_questions(db: DatabaseManager):
    questions = [
        {
            "question_text": "What is the capital of France?",
            "option1": "Berlin",
            "option2": "London",
            "option3": "Paris",
            "option4": "Madrid",
            "correct_index": 3
        },
        {
            "question_text": "What is 2 + 2?",
            "option1": "3",
            "option2": "4",
            "option3": "5",
            "option4": "22",
            "correct_index": 2
        },
        # Add more questions as needed
    ]
    for q in questions:
        db.conn.execute("""
            INSERT INTO questions (question_text, option1, option2, option3, option4, correct_index)
            VALUES (?, ?, ?, ?, ?, ?);
        """, (q["question_text"], q["option1"], q["option2"], q["option3"], q["option4"], q["correct_index"]))

def add_simulated_quizzes(db: DatabaseManager):
    users = db.conn.execute("SELECT user_id FROM users;").fetchall()
    questions = db.conn.execute("SELECT question_id, correct_index FROM questions;").fetchall()
    
    for user in users:
        cursor = db.conn.execute("""
            INSERT INTO quizzes (user_id, timestamp)
            VALUES (?, ?);
        """, (user[0], datetime.now()))
        quiz_id = cursor.lastrowid  # Use lastrowid instead of fetchone()[0]
        
        selected_questions = random.sample(questions, k=min(2, len(questions)))
        for q in selected_questions:
            selected_option = random.randint(1, 4)
            is_correct = selected_option == q[1]
            db.conn.execute("""
                INSERT INTO answers (quiz_id, question_id, selected_option, is_correct)
                VALUES (?, ?, ?, ?);
            """, (quiz_id, q[0], selected_option, is_correct))

def main():
    # Use absolute path to ensure consistency
    base_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(base_dir, "..", "user_quiz.db")
    db = DatabaseManager(db_path=db_path)
    add_simulated_users(db)
    add_simulated_questions(db)
    add_simulated_quizzes(db)
    db.conn.commit()  # Commit the transactions
    print("Simulated data has been added to the database.")

if __name__ == "__main__":
    main()