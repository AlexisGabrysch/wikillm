# src/database.py
import sqlite3
from typing import List, Dict, Any
import hashlib

class DatabaseManagerbis:
    def __init__(self, db_path="./user_quiz.db"):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.create_tables()

    def create_tables(self):
        # Table utilisateurs
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                super_user BOOLEAN NOT NULL,
                group TEXT
            );
        """)

        # Table questions avec 'subject' (matière)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS questions (
                question_id INTEGER PRIMARY KEY AUTOINCREMENT,
                question_text TEXT NOT NULL,
                option1 TEXT NOT NULL,
                option2 TEXT NOT NULL,
                option3 TEXT NOT NULL,
                option4 TEXT NOT NULL,
                correct_index INTEGER NOT NULL,
                subject TEXT NOT NULL,
                chapter TEXT NOT NULL
            );
        """)

        # Table quizzes
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS quizzes (
                quiz_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                speed_mode BOOLEAN NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(user_id)
            );
        """)

        # Table answers
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS answers (
                answer_id INTEGER PRIMARY KEY AUTOINCREMENT,
                quiz_id INTEGER,
                question_id INTEGER,
                selected_option INTEGER,
                is_correct BOOLEAN,
                FOREIGN KEY(quiz_id) REFERENCES quizzes(quiz_id),
                FOREIGN KEY(question_id) REFERENCES questions(question_id)
            );
        """)

    def hash_password(self, password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()

    def add_user(self, first_name: str, last_name: str, username: str, password: str) -> bool:
        try:
            password_hash = self.hash_password(password)
            self.conn.execute("""
                INSERT INTO users (first_name, last_name, username, password_hash)
                VALUES (?, ?, ?, ?);
            """, (first_name, last_name, username, password_hash))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False  # Username already exists

    def verify_user(self, username: str, password: str) -> bool:
        """
        Vérifie si le nom d'utilisateur et le mot de passe correspondent.
        
        Args:
            username (str): Nom d'utilisateur.
            password (str): Mot de passe.

        Returns:
            bool: True si le nom d'utilisateur et le mot de passe correspondent, False sinon.
        """
        password_hash = self.hash_password(password)
        cursor = self.conn.execute("""
            SELECT * FROM users WHERE username = ? AND password_hash = ?;
        """, (username, password_hash))
        return cursor.fetchone() is not None

    def add_quiz(self, user_id: int) -> int:
        cursor = self.conn.execute("""
            INSERT INTO quizzes (user_id)
            VALUES (?);
        """, (user_id,))
        self.conn.commit()
        return cursor.lastrowid

    def add_answer(self, quiz_id: int, question_id: int, selected_option: int, is_correct: bool):
        self.conn.execute("""
            INSERT INTO answers (quiz_id, question_id, selected_option, is_correct)
            VALUES (?, ?, ?, ?, ?);
        """, (quiz_id, question_id, selected_option, is_correct))
        self.conn.commit()

    def get_question_by_id(self, question_id: int) -> Dict[str, Any]:
        cursor = self.conn.execute("""
            SELECT question_id, question_text, option1, option2, option3, option4, correct_index
            FROM questions
            WHERE question_id = ?;
        """, (question_id,))
        row = cursor.fetchone()
        if row:
            return {
                "question_id": row[0],
                "question_text": row[1],
                "options": [row[2], row[3], row[4], row[5]],
                "correct_index": row[6]
            }
        return {}

    def get_random_questions(self, num_questions: int, selected_topics: List[str]) -> List[Dict[str, Any]]:
        # Supposons que vous avez une colonne 'category' dans la table 'questions'
        placeholders = ','.join('?' for _ in selected_topics)
        query = f"""
            SELECT question_id, question_text, option1, option2, option3, option4, correct_index
            FROM questions
            WHERE category IN ({placeholders})
            ORDER BY RANDOM()
            LIMIT ?;
        """
        cursor = self.conn.execute(query, (*selected_topics, num_questions))
        rows = cursor.fetchall()
        questions = []
        for row in rows:
            questions.append({
                "question_id": row[0],
                "question_text": row[1],
                "options": [row[2], row[3], row[4], row[5]],
                "correct_index": row[6]
            })
        return questions

    def add_question(self, question_text: str, options: List[str], correct_index: int) -> int:
        """
        Ajoute une nouvelle question à la table 'questions' et retourne son ID.

        Args:
            question_text (str): Le texte de la question.
            options (List[str]): Liste des 4 options.
            correct_index (int): L'index (1-4) de la réponse correcte.

        Returns:
            int: L'ID de la question ajoutée.
        """
        if len(options) != 4:
            raise ValueError("Il doit y avoir exactement 4 options.")

        cursor = self.conn.execute("""
            INSERT INTO questions (question_text, option1, option2, option3, option4, correct_index)
            VALUES (?, ?, ?, ?, ?, ?);
        """, (question_text, options[0], options[1], options[2], options[3], correct_index))
        self.conn.commit()
        return cursor.lastrowid

    def get_topics(self) -> List[str]:
        """
        Récupère la liste des sujets disponibles à partir des questions.

        Returns:
            List[str]: Liste des sujets uniques.
        """
        cursor = self.conn.execute("SELECT DISTINCT category FROM questions;")
        rows = cursor.fetchall()
        topics = [row[0] for row in rows if row[0]]
        return topics

    def change_password(self, username: str, old_password: str, new_password: str) -> bool:
        """
        Change le mot de passe d'un utilisateur.

        Args:
            username (str): Nom d'utilisateur.
            old_password (str): Ancien mot de passe.
            new_password (str): Nouveau mot de passe.

        Returns:
            bool: True si le mot de passe a été changé avec succès, False sinon.
        """
        if not self.verify_user(username, old_password):
            return False

        password_hash = self.hash_password(new_password)
        self.conn.execute("""
            UPDATE users SET password_hash = ? WHERE username = ?;
        """, (password_hash, username))
        self.conn.commit()
        return True
    
    def change_username(self, username: str, new_username: str) -> bool:
        """
        Change the username of a user ensuring the new username is unique.

        Args:
            username (str): Current username.
            new_username (str): New desired username.

        Returns:
            bool: True if the username was changed successfully, False otherwise.
        """
        # Check if the new username already exists
        cursor = self.conn.execute("""
            SELECT 1 FROM users WHERE username = ?;
        """, (new_username,))
        if cursor.fetchone():
            return False  # New username already taken

        # Update the username
        self.conn.execute("""
            UPDATE users SET username = ? WHERE username = ?;
        """, (new_username, username))
        self.conn.commit()
        return True

    def get_super_user(self, username: str) -> bool:
        cursor = self.conn.execute("""
            SELECT super_user FROM users WHERE username = ?;
        """, (username,))
        result = cursor.fetchone()
        return bool(result[0]) if result else False
    
    def get_quiz_mode(self) -> str:
        cursor = self.conn.execute("""
            SELECT mode FROM quizzes;
        """)
        results = cursor.fetchall()
        return [row[0] for row in results] if results else []
    
    def get_timestamp(self) -> str:
        cursor = self.conn.execute("""
            SELECT DISTINCT timestamp FROM quizzes;
        """)
        results = cursor.fetchall()
        return [row[0] for row in results] if results else []
    
    def get_quizz_id(self) -> str:
        cursor = self.conn.execute("""
            SELECT COUNT(DISTINCT quizz_id) FROM quizzes;
        """)
        results = cursor.fetchall()
        return [row[0] for row in results] if results else []

    def get_taux_reussite_question(self, question_id: int) -> float:
        """
        Récupère le taux de réponses correctes pour une question donnée
        Args :
            question_id (int) : id de la question

        Returns :
            (float) : taux de réponses correctes
        """
        # Nombre de bonne réponses (result_correct)
        cursor_correct = conn.execute("""
            SELECT COUNT(*) 
            FROM answers 
            WHERE question_id = ? AND is_correct = 1
            """, (question_id,))
        result_correct = cursor_correct.fetchone()[0]
        
        # Nombre total de réponses (result_total)
        cursor_total = self.conn.execute("""
            SELECT COUNT(*)
            FROM answers
            WHERE question_id = ?
            """, (question_id,))
        result_total = cursor_total.fetchone()[0]
        return result_correct / result_total if result_total > 0 else 0.0
    
    def get_taux_reussite_subject(self, subject: str) -> float:
        cursor_total = self.conn.execute("""
            SELECT COUNT(*)
            FROM answers
            WHERE question_id IN (
                SELECT question_id
                FROM questions
                WHERE subject = ?)""",(subject,))
        result_total = cursor_total.fetchone()
        cursor_correct = self.conn.execute("""
            SELECT COUNT(*)
            FROM answers
            WHERE question_id IN (
                SELECT question_id
                FROM questions
                WHERE subject = ? AND is_correct = 1);""",(subject,))
        result_correct = cursor_correct.fetchone()
        return result_correct[0] / result_total[0] if result_total[0] > 0 else 0.0
    
 
