# FILE: src/quiz_database.py
import sqlite3
from datetime import datetime
from typing import List, Dict, Any, Optional
import hashlib

class CoursesDatabase:
    def __init__(self, db_path: str = "src/db/courses.db") -> None:
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.create_tables()

    def create_tables(self) -> None:
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS course_info (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                site TEXT,
                matiere TEXT,
                theme TEXT,
                chapitre TEXT,
                content TEXT,
                link TEXT
            )
        """)
        self.conn.commit()

    def insert_course(self, site: str, matiere: str, theme: str, chapitre: str, content: str, link: str) -> None:
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO course_info (site, matiere, theme, chapitre, content, link)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (site, matiere, theme, chapitre, content, link))
        self.conn.commit()

    def get_matiere(self) -> List[str]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT DISTINCT matiere FROM course_info")
        matieres = cursor.fetchall()
        return [matiere[0] for matiere in matieres]
    def get_themes_by_matiere(self, matiere: str) -> List[str]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT DISTINCT theme FROM course_info WHERE matiere = ?", (matiere,))
        themes = cursor.fetchall()
        return [theme[0] for theme in themes]
    
    def get_themes(self) -> List[str]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT DISTINCT theme FROM course_info")
        themes = cursor.fetchall()
        return [theme[0] for theme in themes]

    def get_contents_per_theme(self, theme: str) -> str:
        cursor = self.conn.cursor()
        cursor.execute("SELECT content FROM course_info WHERE theme = ?", (theme,))
        contents = cursor.fetchall()
        return " ".join(content[0] for content in contents)

    def get_contents_per_theme_as_dict(self, theme: str) -> Dict[str, str]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT chapitre, content FROM course_info WHERE theme = ?", (theme,))
        rows = cursor.fetchall()
        return {chapitre: content for chapitre, content in rows}

    def get_courses_content_by_chapter(self,  chapitre: str) -> str:
        cursor = self.conn.cursor()
        cursor.execute("SELECT content FROM course_info WHERE chapitre = ?", (chapitre,))
        contents = cursor.fetchall()
        return " ".join(content[0] for content in contents)
    
    def get_all_chapters_by_theme(self, theme: str) -> List[str]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT DISTINCT chapitre FROM course_info WHERE theme = ?", (theme,))
        chapters = cursor.fetchall()
        return [chapitre[0] for chapitre in chapters]
    
    def close(self) -> None:
        self.conn.close()
    

class QuizDatabase:
    def __init__(self, db_path: str = "src/db/quiz.db") -> None:
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.create_tables()
        self.insert_super_root()
     

    def create_tables(self) -> None:
        cursor = self.conn.cursor()
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
        # Updated questions table schema
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS questions (
                question_id INTEGER PRIMARY KEY AUTOINCREMENT,
                question_text TEXT NOT NULL,
                option1 TEXT NOT NULL,
                option2 TEXT NOT NULL,
                option3 TEXT NOT NULL,
                option4 TEXT NOT NULL,
                correct_index INTEGER NOT NULL,
                subject TEXT NOT NULL,
                chapter TEXT NOT NULL,
                hint TEXT,
                explanation TEXT
            )
        """)
        # Table for quizzes (can be generated per subject/theme)
     # Table quizzes
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS quizzes (
                quiz_id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject TEXT NOT NULL,
                chapter TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            );
        """)
      
     # Table answers
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS answers (
                answer_id INTEGER PRIMARY KEY AUTOINCREMENT,
                quiz_id INTEGER,
                user_id INTEGER,
                question_id INTEGER,
                selected_option INTEGER,
                is_correct BOOLEAN,
                answer_time FLOAT NOT NULL,
                hint_used BOOLEAN,
                FOREIGN KEY(quiz_id) REFERENCES quizzes(quiz_id),
                FOREIGN KEY(question_id) REFERENCES questions(question_id),
                FOREIGN KEY(user_id) REFERENCES users(user_id)
            );
        """)
        
                # Table completed_courses
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS completed_courses (
                user_id INTEGER,
                course_title TEXT,
                PRIMARY KEY (user_id, course_title),
                FOREIGN KEY(user_id) REFERENCES users(user_id)
            );
        """)
        
        # Assuming there exists a users table as described.
        self.conn.commit()
        
    def insert_super_root(self):
        cursor = self.conn.cursor()
        # Check if 'root' user already exists
        cursor.execute("SELECT user_id FROM users WHERE username = ?", ("rootuser",))
        if cursor.fetchone() is None:
            try:
                cursor.execute("""
                    INSERT INTO users (first_name, last_name, username, password_hash, super_user)
                    VALUES (?, ?, ?, ?, ?)
                """, ("admin", "admin", "rootuser", "rootpwd", 1))
                self.conn.commit()
            except sqlite3.IntegrityError:
                pass  # handle error if needed
        
    def insert_question(
        self,
        question_text: str,
        option1: str,
        option2: str,
        option3: str,
        option4: str,
        correct_index: int,
        subject: str,
        chapter: str,
        hint: str = "",
        explanation: str = ""
    ) -> int:
        """
        Inserts a new question into the questions table.
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO questions (
                question_text, option1, option2, option3, option4,
                correct_index, subject, chapter, hint, explanation
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            question_text, option1, option2, option3, option4,
            correct_index, subject, chapter, hint, explanation
        ))
        self.conn.commit()
        return cursor.lastrowid

    def get_questions_by_subject_and_chapter(self, subject: str, chapter: str) -> List[Dict[str, Any]]:
        """
        Returns all questions for the given subject and chapter.
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT question_id, question_text, option1, option2, option3, option4, correct_index, hint, explanation
            FROM questions
            WHERE subject = ? AND chapter = ?
        """, (subject, chapter))
        rows = cursor.fetchall()
        questions = []
        for row in rows:
            questions.append({
                "question_id": row[0],
                "question_text": row[1],
                "option1": row[2],
                "option2": row[3],
                "option3": row[4],
                "option4": row[5],
                "correct_index": row[6],
                "hint": row[7],
                "explanation": row[8]
            })
        return questions

    def get_or_create_quiz(self, subject: str, chapter: str) -> int:
        """
        Retourne l'ID du quiz existant pour le (subject, chapter) donné,
        ou crée un nouveau quiz partagé pour ce chapitre.
        """
        cursor = self.conn.execute(
            "SELECT quiz_id FROM quizzes WHERE subject = ? AND chapter = ?;",
            (subject, chapter)
        )
        row = cursor.fetchone()
        if row:
            return row[0]
        cursor = self.conn.execute(
            "INSERT INTO quizzes (subject, chapter) VALUES (?, ?);",
            (subject, chapter)
        )
        self.conn.commit()
        return cursor.lastrowid

    def insert_result(
        self,
        quiz_id: int,
        user_id: int,
        question_id: int,
        selected_option: int,
        is_correct: bool,
        answer_time: float,
        hint_used: bool
    ) -> None:
        """
        Enregistre la réponse d'un utilisateur pour une question du quiz.
        """
        self.conn.execute("""
            INSERT INTO answers (quiz_id, user_id, question_id, selected_option, is_correct, answer_time, hint_used)
            VALUES (?, ?, ?, ?, ?, ?, ?);
        """, (quiz_id, user_id, question_id, selected_option, is_correct, answer_time, hint_used))
        self.conn.commit()

    def get_user_results(self, user_id: int) -> List[Dict[str, Any]]:
        """
        Returns all quiz results for the given user.
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT quiz_id, subject, chapter, timestamp, speed_mode
            FROM quizzes
            WHERE user_id = ?
        """, (user_id,))
        rows = cursor.fetchall()
        results = []
        for row in rows:
            quiz_id = row[0]
            cursor.execute("""
                SELECT question_id, selected_option, is_correct, answer_time, indice
                FROM answers
                WHERE quiz_id = ?
            """, (quiz_id,))
            answers = cursor.fetchall()
            results.append({
                "quiz_id": quiz_id,
                "subject": row[1],
                "chapter": row[2],
                "timestamp": row[3],
                "speed_mode": row[4],
                "answers": answers
            })
        return results

    def close(self) -> None:
        self.conn.close()
        
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
            SELECT question_text, option1, option2, option3, option4, correct_index, subject, chapter, hint, explanation
            FROM questions
            WHERE question_id = ?;
        """, (question_id,))
        row = cursor.fetchone()
        if row is None:
            return {}
        return {
            "question_text": row[0],
            "option1": row[1],
            "option2": row[2],
            "option3": row[3],
            "option4": row[4],
            "correct_index": row[5],
            "subject": row[6],
            "chapter": row[7],
            "hint": row[8],
            "explanation": row[9]
        }
        
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
            SELECT quiz_id FROM quizzes
            JOIN users ON quizzes.user_id = users.user_id
            WHERE users.username = ?;
        """, (username,))
        results = cursor.fetchall()
        return len(results)
    
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
            List[Dict[str, Any]]: Liste de dictionnaires contenant 'timestamp' et 'success_rate'.
        """
        cursor = self.conn.execute("""
            SELECT 
                quizzes.timestamp,
                CAST(SUM(CASE WHEN answers.is_correct = 1 THEN 1 ELSE 0 END) AS FLOAT) / 
                COUNT(answers.answer_id) AS success_rate
            FROM answers
            JOIN quizzes ON answers.quiz_id = quizzes.quiz_id
            JOIN users ON answers.user_id = users.user_id
            WHERE users.username = ?
            GROUP BY quizzes.timestamp
            ORDER BY quizzes.timestamp;
        """, (username,))
        return [
            {
                "timestamp": row[0],
                "success_rate": round(row[1] * 100, 2)
            } for row in cursor.fetchall()
        ]
    
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
                CAST(SUM(CASE WHEN answers.is_correct = 1 THEN 1 ELSE 0 END) AS FLOAT) / 
                COUNT(answers.answer_id) AS 'Taux de Réussite (%)'
            FROM answers
            JOIN quizzes ON answers.quiz_id = quizzes.quiz_id
            JOIN users ON answers.user_id = users.user_id
            JOIN questions ON answers.question_id = questions.question_id
            WHERE users.username = ?
            GROUP BY questions.{topics}
            ORDER BY 'Taux de Réussite (%)' DESC;
        """, (username,))
        return [
            {
                topics: row[0],
                "Taux de Réussite (%)": round(row[1] * 100, 2)
            } for row in cursor.fetchall()
        ]
        

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
            LEFT JOIN answers ON users.user_id = answers.user_id
            LEFT JOIN quizzes ON answers.quiz_id = quizzes.quiz_id
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
        
        
    def add_completed_course(self, user_id: int, course_title: str) -> None:
        """
        Adds a completed course for a user.

        Args:
            user_id (int): The ID of the user.
            course_title (str): The title of the completed course.
        """
        self.conn.execute("""
            INSERT OR IGNORE INTO completed_courses (user_id, course_title)
            VALUES (?, ?);
        """, (user_id, course_title))
        self.conn.commit()

    def is_course_completed(self, user_id: int, course_title: str) -> bool:
        """
        Checks if a course is completed by a user.

        Args:
            user_id (int): The ID of the user.
            course_title (str): The title of the course.

        Returns:
            bool: True if the course is completed, False otherwise.
        """
        cursor = self.conn.execute("""
            SELECT 1 FROM completed_courses
            WHERE user_id = ? AND course_title = ?;
        """, (user_id, course_title))
        return cursor.fetchone() is not None

    def get_completed_courses(self, user_id: int) -> List[str]:
        """
        Retrieves the list of completed courses for a user.

        Args:
            user_id (int): The ID of the user.

        Returns:
            List[str]: A list of completed course titles.
        """
        cursor = self.conn.execute("""
            SELECT course_title FROM completed_courses
            WHERE user_id = ?;
        """, (user_id,))
        return [row[0] for row in cursor.fetchall()]
    
    def get_categories(self) -> List[str]:
        """
        Récupère les catégories des questions.

        Returns:
            List[str]: Liste des catégories.
        """
        cursor = self.conn.execute("SELECT DISTINCT subject FROM questions;")
        return [row[0] for row in cursor.fetchall()]

    def get_titles_by_category(self, category: str) -> List[str]:
        """
        Récupère les titres des questions pour une catégorie donnée.

        Args:
            category (str): La catégorie des questions.

        Returns:
            List[str]: Liste des titres.
        """
        cursor = self.conn.execute("""
            SELECT DISTINCT chapter FROM questions WHERE subject = ?;
        """, (category,))
        return [row[0] for row in cursor.fetchall()]
    def query_article(self) -> List[str]:
        """
        Récupère les articles des questions.

        Returns:
            List[str]: Liste des articles.
        """
        cursor = self.conn.execute("SELECT DISTINCT chapter FROM questions;")
        return [row[0] for row in cursor.fetchall()]
    
    def get_super_user(self, username: str) -> bool:
        """
        Vérifie si un utilisateur est un super utilisateur.

        Args:
            username (str): Nom d'utilisateur.

        Returns:
            bool: True si l'utilisateur est un super utilisateur, False sinon.
        """
        cursor = self.conn.execute("""
            SELECT super_user FROM users WHERE username = ?;
        """, (username,))
        return cursor.fetchone()[0] == 1