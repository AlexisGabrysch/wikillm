# src/populate_data.py

from databasebis import DatabaseManagerbis
import hashlib
import random
from datetime import datetime
import os

def add_simulated_users(db: DatabaseManagerbis):

    users = [
        {"first_name": "Alice", "last_name": "Smith", "username": "alice", "password": "password123", "super_user": 0},
        {"first_name": "Bob", "last_name": "Johnson", "username": "bob", "password": "securepass", "super_user": 0},
        {"first_name": "Charlie", "last_name": "Lee", "username": "charlie", "password": "charliepwd", "super_user": 0},
        {"first_name": "John", "last_name": "Doe", "username": "joe", "password": "joepwd", "super_user": 0},
        {"first_name": "root", "last_name": "root", "username": "root", "password": "rootpwd", "super_user": 1}
    ]
    for user in users:
        success = db.add_user(user["first_name"], user["last_name"], user["username"], user["password"], user["super_user"])
        if not success:
            print(f"Username {user['username']} already exists.")



def add_simulated_questions(db: DatabaseManagerbis):
    questions = [
        {
            "question_text": "What is the capital of France?",
            "option1": "Berlin",
            "option2": "London",
            "option3": "Paris",
            "option4": "Madrid",
            "correct_index": 3,
            "subject": "Géographie",
            "chapter": "capitale"
        },
        {
            "question_text": "What is 2 + 2?",
            "option1": "3",
            "option2": "4",
            "option3": "5",
            "option4": "22",
            "correct_index": 2,
            "subject": "Math",
            "chapter": "addition"
        },
        
         {
            "question_text": "What is the largest planet in our solar system?",
            "option1": "Earth",
            "option2": "Jupiter",
            "option3": "Mars",
            "option4": "Venus",
            "correct_index": 2,
            "subject": "science",
            "chapter": "planet"
    },
{
            "question_text": "What is 4 * 4?",
            "option1": "8",
            "option2": "16",
            "option3": "7",
            "option4": "-8",
            "correct_index": 2,
            "subject": "Math",
            "chapter": "Multiplication"
        },

        {
            "question_text": "What is 2 + 5?",
            "option1": "7",
            "option2": "10",
            "option3": "4",
            "option4": "-1",
            "correct_index": 1,
            "subject": "Math",
            "chapter": "addition"
        },
    ]
    for question in questions:
        db.add_question(
            question["question_text"],
            [question["option1"], question["option2"], question["option3"], question["option4"]],
            question["correct_index"],
            question["subject"],
            question["chapter"]
        )


def add_simulated_quizzes(db: DatabaseManagerbis):
    questions = db.conn.execute("SELECT question_id, correct_index FROM questions;").fetchall()
    cursor = db.conn.execute("""
        SELECT user_id, username FROM users;
    """)
    users= [{"user_id": row[0], "username": row[1]} for row in cursor.fetchall()]
    
    for user in users:
        # Pour pas ajouter de quizz pour root
        if user['username'] == 'root':
            continue
        
        cursor = db.conn.execute("""
            INSERT INTO quizzes (user_id, timestamp, speed_mode)
            VALUES (?, ?, 0);
        """, (user['user_id'], datetime.now()))
        quiz_id = cursor.lastrowid  # Use lastrowid instead of fetchone()[0]
        
        selected_questions = random.sample(questions, k=min(2, len(questions)))
        for q in selected_questions:
            answer_time = random.uniform(0.01, 20) 
            indice = random.randint(0, 1)  
            selected_option = random.randint(1, 4)
            is_correct = selected_option == q[1]
            db.conn.execute("""
                INSERT INTO answers (quiz_id, question_id, selected_option, is_correct, answer_time, indice)
                VALUES (?, ?, ?, ?, ?, ?);
            """, (quiz_id, q[0], selected_option, is_correct, answer_time, indice))
    


def main():
    # Use absolute path to ensure consistency
    base_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(base_dir, "..", "user_quiz.db")
    db = DatabaseManagerbis(db_path=db_path)
    add_simulated_users(db)
    add_simulated_questions(db)
    add_simulated_quizzes(db)
    db.conn.commit()  # Commit the transactions
    print("Simulated data has been added to the database.")

if __name__ == "__main__":
    main()