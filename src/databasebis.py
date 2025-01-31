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
                super_user BOOLEAN NOT NULL
                
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
                answer_time FLOAT NOT NULL,
                indice BOOLEAN,
                FOREIGN KEY(quiz_id) REFERENCES quizzes(quiz_id),
                FOREIGN KEY(question_id) REFERENCES questions(question_id)
            );
        """)

    def hash_password(self, password: str) -> str:
        """
        Encode un mot de passe en SHA-256.

        Args:
            password (str): Mot de passe à encoder.
        
        Returns:    
            str: Mot de passe encodé.
        """
        return hashlib.sha256(password.encode()).hexdigest()

    def add_user(self, first_name: str, last_name: str, username: str, password: str, super_user: bool) -> bool:
        """
        Ajoute un nouvel utilisateur à la table 'users'.

        Args:
            first_name (str): Prénom.
            last_name (str): Nom de famille.
            username (str): Nom d'utilisateur.
            password (str): Mot de passe.
            super_user (bool): True si l'utilisateur est un super utilisateur, False sinon.
            
        
        Returns:    
            bool: True si l'utilisateur a été ajouté avec succès, False sinon.
        """
        
        try:
            password_hash = self.hash_password(password)
            self.conn.execute("""
                INSERT INTO users (first_name, last_name, username, password_hash, super_user)
                VALUES (?, ?, ?, ?, ?);
            """, (first_name, last_name, username, password_hash, super_user))
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

    def add_quiz(self, user_id: int, speed_mode: bool) -> int:
        """
        Ajoute un nouveau quiz à la table 'quizzes' et retourne son ID.

        Args:
            user_id (int): ID de l'utilisateur.
            speed_mode (bool): True si le mode rapide est activé, False sinon.

        Returns:
            int: ID du quiz ajouté.
        """
        cursor = self.conn.execute("""
            INSERT INTO quizzes (user_id, speed_mode)
            VALUES (?, ?);
        """, (user_id, speed_mode))
        self.conn.commit()
        return cursor.lastrowid

    def add_answer(self, quiz_id: int, question_id: int, selected_option: int, is_correct: bool, answer_time: float, indice: bool) -> None:
        """
        Ajoute une nouvelle réponse à la table 'answers'.

        Args:
            quiz_id (int): ID du quiz.
            question_id (int): ID de la question.
            selected_option (int): Index de l'option sélectionnée (1-4).
            is_correct (bool): True si la réponse est correcte, False sinon.
            answer_time (float) : Le temps passé pour répondre à la question
            indice (bool) : Si un indice a été utilisé (1 pour utilisé sinon 0)


        """
        self.conn.execute("""
            INSERT INTO answers (quiz_id, question_id, selected_option, is_correct, answer_time, indice)
            VALUES (?, ?, ?, ?, ?, ?);
        """, (quiz_id, question_id, selected_option, is_correct, answer_time, indice))
        self.conn.commit()

    def get_chapters_by_subject(self, subject: str) -> List[str]:
        cursor = self.conn.execute("""
            SELECT DISTINCT chapter FROM questions WHERE subject = ?;
        """, (subject,))
        return [row[0] for row in cursor.fetchall()]
    
    def get_average_answer_time(self, correct: bool = None) -> float:
            """
            Calcule le temps moyen de réponse.

            Args:
                correct (bool, optional): 
                    - True pour les bonnes réponses,
                    - False pour les mauvaises réponses,
                    - None pour toutes les réponses.
            
            Returns:
                float: Temps moyen de réponse en secondes.
            """
            if correct is True:
                condition = "WHERE is_correct = 1"
            elif correct is False:
                condition = "WHERE is_correct = 0"
            else:
                condition = ""
            
            query = f"""
                SELECT AVG(answer_time) FROM answers
                {condition};
            """
            cursor = self.conn.execute(query)
            result = cursor.fetchone()[0]
            return round(result, 2) if result is not None else 0.0

    def get_question_by_id(self, question_id: int) -> Dict[str, Any]:
        """
        Récupère une question à partir de son ID.

        Args:
            question_id (int): ID de la question.

        Returns:
            Dict[str, Any]: Dictionnaire contenant les détails de la question.
        """
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
        """
        Génère un certain nombre de questions aléatoires pour les sujets sélectionnés.

        Args:
            num_questions (int): Nombre de questions à générer.
            selected_topics (List[str]): Liste des sujets sélectionnés.

        Returns:
            List[Dict[str, Any]]: Liste de dictionnaires contenant les détails des questions.

        """

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

    def add_question(self, question_text: str, options: List[str], correct_index: int, subject: str, chapter: float) -> int:
        """
        Ajoute une nouvelle question à la table 'questions' et retourne son ID.

        Args:
            question_text (str): Le texte de la question.
            options (List[str]): Liste des 4 options.
            correct_index (int): L'index (1-4) de la réponse correcte.
            subject (str) : La matière ('histoire', 'maths', etc)
            chapter (str) : Le chapitre ('2nd guerre mondiale', 'BRICS', etc)

        Returns:
            int: L'ID de la question ajoutée.
        """
        if len(options) != 4:
            raise ValueError("Il doit y avoir exactement 4 options.")

        cursor = self.conn.execute("""
            INSERT INTO questions (question_text, option1, option2, option3, option4, correct_index, subject, chapter)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """, (question_text, options[0], options[1], options[2], options[3], correct_index, subject, chapter))
        self.conn.commit()
        return cursor.lastrowid

    def get_global_success_rate(self) -> float:
        """
        Calcule le taux de réussite global.

        Returns:
            float: Taux de réussite global en pourcentage.
        """
        cursor = self.conn.execute("""
            SELECT 
                CAST(SUM(CASE WHEN is_correct = 1 THEN 1 ELSE 0 END) AS FLOAT) / 
                COUNT(*) AS success_rate
            FROM answers;
        """)
        row = cursor.fetchone()
        return round(row[0], 2) if row and row[0] is not None else 0.0

    def get_subjects(self) -> List[str]:
        """
        Récupère la liste des matières disponibles à partir des questions.

        Returns:
            List[str]: Liste des sujets uniques.
        """
        cursor = self.conn.execute("SELECT DISTINCT subject FROM questions;")
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
        """
        Retrouve si un utilisateur est un super user.

        Args:
            username (str): Nom d'utilisateur.

        Returns:
            bool: True si l'utilisateur est un super user, False sinon.
        """
        cursor = self.conn.execute("""
            SELECT super_user FROM users WHERE username = ?;
        """, (username,))
        result = cursor.fetchone()
        return bool(result[0]) if result else False
    
    def get_average_success_rate_by_mode(self) -> List[Dict[str, Any]]:
        """
        Calcule le taux de réussite moyen pour chaque mode de quizz.

        Returns:
            List[Dict[str, Any]]: Liste de dictionnaires contenant 'mode' et 'average_success_rate'.
        """
        cursor = self.conn.execute("""
            SELECT 
                CASE 
                    WHEN speed_mode = 1 THEN 'Speed' 
                    ELSE 'Normal' 
                END as mode,
                CAST(SUM(CASE WHEN answers.is_correct = 1 THEN 1 ELSE 0 END) AS FLOAT) / 
                COUNT(answers.answer_id) *100 AS average_success_rate
            FROM quizzes
            JOIN answers ON quizzes.quiz_id = answers.quiz_id
            GROUP BY speed_mode;
        """)
        return [
            {
                "mode": row[0],
                "average_success_rate": round(row[1], 2) if row[1] is not None else 0.0
            } for row in cursor.fetchall()
        ]
    
    def get_timestamp(self) -> str:
        """
        Retourne les timestamps de chaque quiz.

        Returns:
            List[str]: Liste des timestamps
        """
        cursor = self.conn.execute("""
            SELECT DISTINCT timestamp FROM quizzes;
        """)
        results = cursor.fetchall()
        return [row[0] for row in results] if results else []
    
    def get_quizz_id(self, username: str) -> int:
        """
        Compte le nombre de quizz réalisé pour un utilisateur donné.

        Args:
            username (str): Nom d'utilisateur.

        Returns:
            int: ID du quizz.
        """

        cursor = self.conn.execute("""
            SELECT COUNT(*)
            FROM quizzes
            JOIN users ON quizzes.user_id = users.user_id
            WHERE users.username = ?;
        """, (username,))
        count = cursor.fetchone()[0]
        return count

    def get_taux_reussite_question(self, question_id: int) -> float:
        """
        Récupère le taux de réponses correctes pour une question donnée
        Args :
            question_id (int) : id de la question

        Returns :
            (float) : taux de réponses correctes
        """
        # Nombre de bonnes réponses (result_correct)
        cursor_correct = self.conn.execute("""
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

    def get_metrics_question(self, question_id: int) -> Dict[str, Any]:
        """
        Récupère les statistiques pour une question donnée.
        
        Args:
            question_id (int): ID de la question.
        
        Returns:
            Dict[str, Any]: Dictionnaire contenant le taux de réussite, le nombre d'apparitions, le temps de réponse moyen, le nombre d'indices demandés et la bonne réponse.
        """
        cursor = self.conn.execute("""
            SELECT 
                COUNT(*) as total_attempts,
                SUM(CASE WHEN is_correct = 1 THEN 1 ELSE 0 END) as correct_attempts,
                AVG(answer_time) as avg_answer_time,
                SUM(CASE WHEN indice = 1 THEN 1 ELSE 0 END) as total_hints
            FROM answers
            WHERE question_id = ?;
        """, (question_id,))
        
        result = cursor.fetchone()
        total_attempts = result[0]
        correct_attempts = result[1] if result[1] is not None else 0
        avg_answer_time = result[2] if result[2] is not None else 0.0
        total_hints = result[3] if result[3] is not None else 0
        
        success_rate = correct_attempts / total_attempts if total_attempts > 0 else 0.0
        
        # Récupérer la bonne réponse
        cursor = self.conn.execute("""
            SELECT correct_index, option1, option2, option3, option4
            FROM questions
            WHERE question_id = ?;
        """, (question_id,))
        
        question_data = cursor.fetchone()
        correct_index = question_data[0]
        correct_answer = question_data[correct_index]
        
        return {
            "success_rate": success_rate,
            "total_attempts": total_attempts,
            "avg_answer_time": avg_answer_time,
            "total_hints": total_hints,
            "correct_answer": correct_answer
        }
    
    def get_taux_reussite_subject(self, subject: str) -> float:
        """
        Récupère le taux de réponses correctes pour une matière
        Args :
            subject (str) : nom de la matière

        Returns :
            (float) : taux de réponses correctes
        """
        # Nombre de bonnes réponses (result_correct))
        cursor_total = self.conn.execute("""
            SELECT COUNT(*)
            FROM answers
            WHERE question_id IN (
                SELECT question_id
                FROM questions
                WHERE subject = ?)""",(subject,))
        result_total = cursor_total.fetchone()[0]
        
        # Nombre total de réponses (result_total)
        cursor_correct = self.conn.execute("""
            SELECT COUNT(*)
            FROM answers
            WHERE question_id IN (
                SELECT question_id
                FROM questions
                WHERE subject = ? AND is_correct = 1);""",(subject,))
    
        result_correct = cursor_correct.fetchone()[0]
        return result_correct / result_total if result_total > 0 else 0.0

    def get_taux_reussite_chapter(self, chapter: str) -> float:
        """
        Récupère le taux de réponses correctes pour un chapitre
        Args :
            chapter (str) : nom de la matière
        Returns :
            (float) : taux de réponses correctes
        """
        # Nombre de bonnes réponses (result_correct)
        cursor_total = self.conn.execute("""
            SELECT COUNT(*)
            FROM answers
            WHERE question_id IN (
                SELECT question_id
                FROM questions
                WHERE chapter = ?)""",(chapter,))
        result_total = cursor_total.fetchone()[0]
        # Nombre total de réponses (result_total)
        cursor_correct = self.conn.execute("""
            SELECT COUNT(*)
            FROM answers
            WHERE question_id IN (
                SELECT question_id
                FROM questions
                WHERE chapter = ? AND is_correct = 1);""",(chapter,))
        result_correct = cursor_correct.fetchone()[0]
        return result_correct / result_total if result_total > 0 else 0.0


    def get_taux_reussite_user(self, username: str) -> float:
        """
        Calcule le taux de réussite pour un élève donné.

        Args:
            username (str): Nom d'utilisateur de l'élève.

        Returns:
            float: Taux de réussite (entre 0.0 et 1.0).
        """
        cursor = self.conn.execute("""
            SELECT COUNT(*) as total, 
                   SUM(CASE WHEN answers.is_correct = 1 THEN 1 ELSE 0 END) as correct
            FROM answers
            JOIN quizzes ON answers.quiz_id = quizzes.quiz_id
            JOIN users ON quizzes.user_id = users.user_id
            WHERE users.username = ?;
        """, (username,))
        result = cursor.fetchone()
        total = result[0]
        correct = result[1] if result[1] is not None else 0
        return correct / total if total > 0 else 0.0
    
    
    def get_taux_reussite_user_over_time(self, username: str) -> List[Dict[str, Any]]:
        """
        Calcule le taux de réussite au fil du temps pour un utilisateur donné.

        Args:
            username (str): Nom d'utilisateur.

        Returns:
            List[Dict[str, Any]]: Liste de dictionnaires contenant la période et le taux de réussite.
        """
        cursor = self.conn.execute("""
            SELECT 
                strftime('%Y-%m-%d', quizzes.timestamp) AS periode,
                COUNT(answers.answer_id) AS total_reponses,
                SUM(CASE WHEN answers.is_correct = 1 THEN 1 ELSE 0 END) AS reponses_correctes
            FROM answers
            JOIN quizzes ON answers.quiz_id = quizzes.quiz_id
            JOIN users ON quizzes.user_id = users.user_id
            WHERE users.username = ?
            GROUP BY periode
            ORDER BY periode;
        """, (username,))
        
        results = cursor.fetchall()
        taux_reussite_temps = []
        
        for row in results:
            periode, total, correct = row
            taux = (correct / total) * 100 if total > 0 else 0.0
            taux_reussite_temps.append({
                "Période": periode,
                "Taux de Réussite (%)": round(taux, 2)
            })
        
        return taux_reussite_temps
    
    
    def get_taux_reussite_topics_user(self, username: str, topics: str ) -> List[Dict[str, Any]]:
        """
        Calcule le taux de réussite par subject ou par chapter pour un utilisateur donné.

        Args:
            username (str): Nom d'utilisateur
            topics (str): 'subject' ou 'chapter'

        Returns:
            List[Dict[str, Any]]: Liste de dictionnaires contenant le sujet et le taux de réussite.
        """
        cursor = self.conn.execute(f"""
            SELECT 
                questions.{topics},
                COUNT(answers.answer_id) AS total_reponses,
                SUM(CASE WHEN answers.is_correct = 1 THEN 1 ELSE 0 END) AS reponses_correctes
            FROM answers
            JOIN quizzes ON answers.quiz_id = quizzes.quiz_id
            JOIN users ON quizzes.user_id = users.user_id
            JOIN questions ON answers.question_id = questions.question_id
            WHERE users.username = ?
            GROUP BY questions.subject
            ORDER BY questions.subject;
        """, (username,))
        
        results = cursor.fetchall()
        taux_reussite_topics = []
        
        for row in results:
            subject, total, correct = row
            taux = (correct / total) * 100 if total > 0 else 0.0
            taux_reussite_topics.append({
                "Sujet": subject,
                "Taux de Réussite (%)": round(taux, 2)
            })
        
        return taux_reussite_topics


    def get_total_users(self) -> int:
        cursor = self.conn.execute("SELECT COUNT(*) FROM users;")
        return cursor.fetchone()[0]

    def get_total_questions(self) -> int:
        cursor = self.conn.execute("SELECT COUNT(*) FROM questions;")
        return cursor.fetchone()[0]

    def get_total_quizzes(self) -> int:
        cursor = self.conn.execute("SELECT COUNT(*) FROM quizzes;")
        return cursor.fetchone()[0]
    
    def get_quiz_count_by_mode(self, mode: int) -> int:
        """
        Retourne le nombre de quizz selon le mode spécifié.

        Args:
            mode (int): Le mode du quizz ( 1 pour speed ou 0 pour normal).

        Returns:
            int: Nombre de quizz pour le mode spécifié.
        """
        if mode == 1: # 1 pour le mode rapide
            speed_mode = 1
        else :
            speed_mode = 0
        
        
        cursor = self.conn.execute("""
            SELECT COUNT(*) FROM quizzes WHERE speed_mode = ?;
        """, (speed_mode,))
        return cursor.fetchone()[0]

    def get_questions_metrics(self) -> List[Dict[str, Any]]:
        cursor = self.conn.execute("""
            SELECT question_text, 
                    AVG(CASE WHEN is_correct = 1 THEN 1.0 ELSE 0.0 END) as correct_rate
            FROM questions
            JOIN answers ON questions.question_id = answers.question_id
            GROUP BY questions.question_id;
        """)
        return [{"question_text": row[0], "correct_rate": row[1]} for row in cursor.fetchall()]


    def get_users_data(self) -> List[Dict[str, Any]]:
        cursor = self.conn.execute("""
            SELECT username, COUNT(quizzes.quiz_id) as quiz_count
            FROM users
            JOIN quizzes ON users.user_id = quizzes.user_id
            GROUP BY users.user_id;
        """)
        return [{"username": row[0], "quiz_count": row[1]} for row in cursor.fetchall()]

    def get_usernames(self) -> List[str]:
        """
        Récupère la liste des noms d'utilisateurs.

        Returns:
            List[str]: Liste des noms d'utilisateurs.
        """
        cursor = self.conn.execute("""
            SELECT username FROM users WHERE username != 'root';
        """)
        return [row[0] for row in cursor.fetchall()]

    def get_user_success_rates(self) -> List[Dict[str, Any]]:
        """
        Calcule le taux de réussite pour chaque utilisateur.

        Returns:
            List[Dict[str, Any]]: Liste de dictionnaires contenant 'username' et 'success_rate'.
        """
        cursor = self.conn.execute("""
            SELECT users.username,
                   CAST(SUM(CASE WHEN answers.is_correct = 1 THEN 1 ELSE 0 END) AS FLOAT) / 
                   COUNT(answers.answer_id) AS success_rate
            FROM users
            LEFT JOIN quizzes ON users.user_id = quizzes.user_id
            LEFT JOIN answers ON quizzes.quiz_id = answers.quiz_id
            GROUP BY users.user_id;
        """)
        return [{"username": row[0], "success_rate": round(row[1] * 100, 2)} for row in cursor.fetchall()]

    def get_leaderboard(self) -> List[Dict[str, Any]]:
        cursor = self.conn.execute("""
            SELECT users.username, COUNT(DISTINCT quizzes.quiz_id) as total_quizzes,
                   CAST(SUM(CASE WHEN answers.is_correct = 1 THEN 1 ELSE 0 END) AS FLOAT) / 
                   COUNT(answers.answer_id) AS success_rate
            FROM users
            JOIN quizzes ON users.user_id = quizzes.user_id
            JOIN answers ON quizzes.quiz_id = answers.quiz_id
            GROUP BY users.user_id
            ORDER BY total_quizzes DESC
            LIMIT 10;
        """)
        return [
            {
                "username": row[0],
                "total_quizzes": row[1],
                "success_rate": round(row[2] * 100, 2)
            } for row in cursor.fetchall()
        ]

    
    def get_users_metrics(self) -> List[Dict[str, Any]]:
        """
        Récupère les métriques des utilisateurs.

        Returns:
            List[Dict[str, Any]]: Liste de dictionnaires contenant les métriques des utilisateurs.
        """
        cursor = self.conn.execute("""
            SELECT 
                users.username,
                COUNT(DISTINCT quizzes.quiz_id) as total_quizzes,
                AVG(CASE WHEN answers.is_correct = 1 THEN 1.0 ELSE 0.0 END) * 100 as success_rate,
                AVG(answers.answer_time) as avg_answer_time
            FROM users
            LEFT JOIN quizzes ON users.user_id = quizzes.user_id
            LEFT JOIN answers ON quizzes.quiz_id = answers.quiz_id
            WHERE users.username != 'root'
            GROUP BY users.user_id;
        """)
        return [
            {
                "username": row[0],
                "success_rate": round(row[2], 2) if row[2] is not None else 0.0,
                "total_quizzes": row[1],
                "avg_answer_time": round(row[3], 2) if row[3] is not None else 0.0
            } for row in cursor.fetchall()
        ]
    
    def get_users_metrics_by_subject(self, subject: str) -> List[Dict[str, Any]]:
        """
        Récupère les métriques des utilisateurs pour un sujet donné.
    
        Args:
            subject (str): Le sujet pour lequel récupérer les métriques.
    
        Returns:
            List[Dict[str, Any]]: Liste de dictionnaires contenant les métriques des utilisateurs.
        """
        cursor = self.conn.execute("""
            SELECT 
                users.username,
                COUNT(DISTINCT quizzes.quiz_id) as total_quizzes,
                AVG(CASE WHEN answers.is_correct = 1 THEN 1.0 ELSE 0.0 END) * 100 as success_rate,
                AVG(answers.answer_time) as avg_answer_time
            FROM users
            LEFT JOIN quizzes ON users.user_id = quizzes.user_id
            LEFT JOIN answers ON quizzes.quiz_id = answers.quiz_id
            LEFT JOIN questions ON answers.question_id = questions.question_id
            WHERE questions.subject = ? AND users.username != 'root'
            GROUP BY users.user_id;
        """, (subject,))
        return [
            {
                "username": row[0],
                "success_rate": round(row[2], 2) if row[2] is not None else 0.0,
                "total_quizzes": row[1],
                "avg_answer_time": round(row[3], 2) if row[3] is not None else 0.0
            } for row in cursor.fetchall()
        ]
    
    def get_users_metrics_by_chapter(self, chapter: str) -> List[Dict[str, Any]]:
        """
        Récupère les métriques des utilisateurs pour un chapitre donné.
    
        Args:
            chapter (str): Le chapitre pour lequel récupérer les métriques.
    
        Returns:
            List[Dict[str, Any]]: Liste de dictionnaires contenant les métriques des utilisateurs.
        """
        cursor = self.conn.execute("""
            SELECT 
                users.username,
                COUNT(DISTINCT quizzes.quiz_id) as total_quizzes,
                AVG(CASE WHEN answers.is_correct = 1 THEN 1.0 ELSE 0.0 END) * 100 as success_rate,
                AVG(answers.answer_time) as avg_answer_time
            FROM users
            LEFT JOIN quizzes ON users.user_id = quizzes.user_id
            LEFT JOIN answers ON quizzes.quiz_id = answers.quiz_id
            LEFT JOIN questions ON answers.question_id = questions.question_id
            WHERE questions.chapter = ? AND users.username != 'root'
            GROUP BY users.user_id;
        """, (chapter,))
        return [
            {
                "username": row[0],
                "success_rate": round(row[2], 2) if row[2] is not None else 0.0,
                "total_quizzes": row[1],
                "avg_answer_time": round(row[3], 2) if row[3] is not None else 0.0
            } for row in cursor.fetchall()
        ]
 
