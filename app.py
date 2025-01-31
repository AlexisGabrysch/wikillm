import asyncio
import streamlit as st
from pages.ressources.components import Navbar, logout
from src.databasebis import DatabaseManagerbis
from src.database import DatabaseManager
from src.rag import RAGPipeline
from dotenv import find_dotenv, load_dotenv
import os
import random
import time
from streamlit_autorefresh import st_autorefresh


st.set_page_config(page_title="WikiLLM", page_icon="📚", layout="wide")

def main():
    # Charger les variables d'environnement
    load_dotenv(find_dotenv())
    API_KEY = os.getenv("MISTRAL_API_KEY")

    if not API_KEY:
        st.warning("Veuillez ajouter votre clé API Mistral dans le fichier `.env`. Redémarrez l'application après avoir ajouté la clé.")
        return

    # Initialisation de la base de données et du pipeline RAG
    db_manager = DatabaseManagerbis(db_path="./user_quiz.db")
    db_rag = DatabaseManager(db_path="./chromadb_data")
    rag = RAGPipeline(
        generation_model="mistral-large-latest",
        role_prompt="Tu es un assistant pédagogique pour le programme de lycée français.",
        db_path="./chromadb_data",
        max_tokens=300,
        temperature=0.9,
        top_n=1,
    )

    st.markdown(
        """
        <style>
        div.stButton > button {
            width: 100%;
            padding: 10px;
            font-size: 16px;
        }
        .button-row {
            margin-bottom: 10px;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    # Barre de navigation
    Navbar()

    st.title("WikiLLM - Quiz et Chat avec l'IA")

    # Initialize session state for authentication
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
        st.session_state.username = ""
        st.session_state.user_id = None

    def login():
        with st.form("login_form"):
            st.subheader("Login")
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login")
            if submitted:
                user = db_manager.conn.execute("""
                    SELECT user_id FROM users WHERE username = ? AND password_hash = ?;
                """, (username, db_manager.hash_password(password))).fetchone()
                if user:
                    st.session_state.authenticated = True
                    st.session_state.user_id = user[0]
                    st.session_state.username = username
                    st.success("Logged in successfully!")
                    st.rerun()
                else:
                    st.error("Invalid username or password.")

    def register():
        with st.form("register_form"):
            st.subheader("Create Account")
            first_name = st.text_input("First Name")
            last_name = st.text_input("Last Name")
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Register")
            if submitted:
                success = db_manager.add_user(first_name, last_name, username, password)
                if success:
                    st.success("Account created successfully! Please log in.")
                else:
                    st.error("Username already exists. Please choose a different one.")

    if not st.session_state.authenticated:
        auth_choice = st.radio("Authentication", ["Login", "Create Account"])
        if auth_choice == "Login":
            login()
        else:
            register()
    else:
    

        # Initialisation des variables de session
        if "quiz_data" not in st.session_state:
            st.session_state.quiz_data = []
        if "current_question_index" not in st.session_state:
            st.session_state.current_question_index = 0
        if "score" not in st.session_state:
            st.session_state.score = 0
        if "completed_quiz" not in st.session_state:
            st.session_state.completed_quiz = False
        if "start_time" not in st.session_state:
            st.session_state.start_time = time.time()
        if "time_spent" not in st.session_state:
            st.session_state.time_spent = []
        if "mode" not in st.session_state:
            st.session_state.mode = "speed_test"
        if "num_questions" not in st.session_state:
            st.session_state.num_questions = 10
        if "quiz_started" not in st.session_state:
            st.session_state.quiz_started = False

        # Fonction pour calculer le temps écoulé
        def get_elapsed_time():
            return time.time() - st.session_state.start_time

        # Section Quiz
        st.header("Quiz")

        # Charger les sujets
        topics = db_rag.get_topics()

        if not topics:
            st.warning("Aucun sujet disponible. Veuillez ajouter des documents à la base de données.")
            return

        # Sélection des sujets
        selected_topics = st.multiselect("Choisissez un ou plusieurs sujets :", topics, disabled=st.session_state.quiz_started)

        # Sélection du nombre de questions
        num_questions = st.number_input("Nombre de questions :", min_value=1, max_value=50, value=10, step=1, disabled=st.session_state.quiz_started)

        # Sélection du mode de quiz
        mode = st.radio("Choisissez le mode de quiz :", ("speed_test", "chill"), disabled=st.session_state.quiz_started)
        start_quizz_button = st.button("Commencer le quiz", key="start_quizz_button", disabled=st.session_state.quiz_started)
        if start_quizz_button:
            if not selected_topics:
                st.error("Veuillez sélectionner au moins un sujet pour commencer le quiz.")
            else:
                st.session_state.quiz_data = []
                st.session_state.current_question_index = 0
                st.session_state.score = 0
                st.session_state.completed_quiz = False
                st.session_state.time_spent = []  # Réinitialiser le temps passé
                st.session_state.answers = []  # Réinitialiser les réponses
                st.session_state.mode = mode
                st.session_state.num_questions = num_questions
                st.session_state.quiz_started = True

                # Générer les questions pour le quiz
                for _ in range(num_questions):
                    topic = random.choice(selected_topics)
                    quiz_data = rag.generate_quiz_question(topic)
                    if quiz_data["correct_index"] != -1:
                        st.session_state.quiz_data.append(quiz_data)

                if not st.session_state.quiz_data:
                    st.error("Aucune question n'a pu être générée. Veuillez réessayer.")
                else:
                    st.session_state.start_time = time.time()  # Initialiser le timer après la génération des questions
                    st.rerun()  # Rafraîchir la page pour afficher la première question

        # Gestion du quiz
        if st.session_state.quiz_data and not st.session_state.completed_quiz:
            
            question_data = st.session_state.quiz_data[st.session_state.current_question_index]
            question = question_data["question"]
            options = question_data["options"]
            correct_index = question_data["correct_index"]

            st.markdown(f"### Question {st.session_state.current_question_index + 1} : {question}")

            if st.session_state.mode == "speed_test":
                # Affichage du timer en temps réel avec une barre de progression
                elapsed_time = get_elapsed_time()
                remaining_time = 30 - int(elapsed_time)
                st.markdown(f"### Temps restant : {remaining_time} secondes")
                progress = min(int((elapsed_time / 30) * 100), 100)
                st.progress(progress)

                # Rafraîchir la page toutes les secondes
                st_autorefresh(interval=1000, key="timer_refresh")

                # Vérifier si le temps est écoulé
                if elapsed_time >= 30:
                    st.session_state.time_spent.append(30)
                    st.session_state.answers.append({"question": question, "answer": None, "correct": False})

                    if st.session_state.current_question_index + 1 < len(st.session_state.quiz_data):
                        st.session_state.current_question_index += 1
                        st.session_state.start_time = time.time()  # Réinitialiser le timer pour la prochaine question
                    else:
                        st.session_state.completed_quiz = True
                    st.rerun()

            # Affichage des options
            for i, option in enumerate(options):
                if st.button(option, key=f"option_{i}"):
                    elapsed_time = get_elapsed_time()
                    st.session_state.time_spent.append(elapsed_time)
                    correct = i == correct_index
                    st.session_state.answers.append({"question": question, "answer": option, "correct": correct})
                    if correct:
                        st.session_state.score += 1

                    if st.session_state.current_question_index + 1 < len(st.session_state.quiz_data):
                        st.session_state.current_question_index += 1
                        st.session_state.start_time = time.time()  # Réinitialiser le timer pour la prochaine question
                    else:
                        st.session_state.completed_quiz = True
                    st.rerun()

            if st.session_state.mode == "chill":
                # Afficher l'explication et l'option pour générer un indice
                if st.session_state.answers:
                    last_answer = st.session_state.answers[-1]
                    if last_answer["correct"]:
                        st.success("Bonne réponse !")
                    else:
                        st.error("Mauvaise réponse.")
                    st.markdown(f"**Explication :** {question_data.get('explanation', 'Aucune explication disponible.')}")

                if st.button("Obtenir un indice"):
                    hint = rag.generate_hint(question, [question_data.get('context', '')])
                    st.info(f"Indice : {hint}")

                # Bouton pour passer à la question suivante
                if st.button("Question suivante"):
                    if st.session_state.current_question_index + 1 < len(st.session_state.quiz_data):
                        st.session_state.current_question_index += 1
                        st.session_state.start_time = time.time()  # Réinitialiser le timer pour la prochaine question
                    else:
                        st.session_state.completed_quiz = True
                    st.rerun()

            # Bouton pour terminer le quiz
            if st.button("Terminer le quiz"):
                st.session_state.completed_quiz = True
                st.rerun()

        if st.session_state.completed_quiz:
            st.header("Récapitulatif du Quiz")
            st.markdown(f"### Score final : {st.session_state.score} / {len(st.session_state.quiz_data)}")

            st.write("**Détails des questions :**")
            for i, question_data in enumerate(st.session_state.quiz_data):
                question = question_data["question"]
                correct_index = question_data["correct_index"]
                st.write(f"Question {i + 1}: {question}")
                if i < len(st.session_state.time_spent):
                    st.write(f"Temps passé : {st.session_state.time_spent[i]} secondes")
                else:
                    st.write("Temps passé : N/A")
                if i < len(st.session_state.answers):
                    answer = st.session_state.answers[i]
                    st.write(f"Votre réponse : {answer['answer']}")
                    st.write(f"Correct : {'Oui' if answer['correct'] else 'Non'}")
                    if st.session_state.mode == "chill":
                        st.markdown(f"**Explication :** {question_data.get('explanation', 'Aucune explication disponible.')}")
            if st.session_state.quiz_started:
                st.session_state.quiz_started = False
                st.rerun()
        
        
        
    if not API_KEY:
        st.warning("Veuillez ajouter votre clé API Mistral dans le fichier `.env`. Redémarrez l'application après avoir ajouté la clé.")

if __name__ == '__main__':
    main()