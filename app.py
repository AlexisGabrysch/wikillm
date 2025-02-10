import streamlit as st
import os

# print the current working directory
print(os.getcwd())

from pages.ressources.components import Navbar , display_quiz 
from src.db.utils import QuizDatabase ,CoursesDatabase
from src.rag import RAGPipeline
from dotenv import find_dotenv, load_dotenv
from streamlit_autorefresh import st_autorefresh
st.set_page_config(page_title="WikiLLM", page_icon="📚", layout="wide")

def main():
 
    st.title("❔ WikiLLM - Quiz et Cours interactifs 📚 ")
      # Centralize CSS styling here
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
    
           
    # Charger les variables d'environnement
    load_dotenv(find_dotenv())
    API_KEY = os.getenv("MISTRAL_API_KEY")

    if not API_KEY:
        st.warning("Veuillez ajouter votre clé API Mistral dans le fichier `.env`. Redémarrez l'application après avoir ajouté la clé.")
        return

    # Initialisation de la base de données et du pipeline RAG
    db_manager = QuizDatabase()
    db_courses = CoursesDatabase()
    db_rag = QuizDatabase()
    rag = RAGPipeline(
        generation_model="mistral-large-latest",
        max_tokens=900,
        temperature=0.5,
        top_n=1,
    )
    # Barre de navigation
    Navbar()

    # Initialize session state for authentication and completed courses
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
        st.session_state.username = ""
        st.session_state.user_id = None

    if "completed_courses" not in st.session_state:
        st.session_state.completed_courses = set()

    if "quiz_started" not in st.session_state:
        st.session_state.quiz_started = False

    if "quiz_data" not in st.session_state:
        st.session_state.quiz_data = []

    if "completed_quiz" not in st.session_state:
        st.session_state.completed_quiz = False

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
                    st.session_state.completed_courses = set(db_manager.get_completed_courses(user[0]))
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
            is_super_admin = st.checkbox("Super Admin")
            submitted = st.form_submit_button("Register")
            if submitted:
                success = db_manager.add_user(first_name, last_name, username, password, is_super_admin)
                if success:
                    st.success("Account created successfully! Please log in.")
                else:
                    st.error("Username already exists. Please choose a different one.")

    def display_subjects():
        st.subheader(f'Votre progression, {st.session_state.username}')
        categories = db_courses.get_matiere()
        if not categories:
            st.warning("Aucune matière disponible.")
            return
        with st.container(border=True):
            cols = st.columns(3)
            for i, category in enumerate(categories):
                with cols[i % 3]:
                    total_courses = len(db_rag.get_titles_by_category(category))
                    completed_courses = sum(
                        1 for course in db_rag.get_titles_by_category(category)
                        if course in st.session_state.get("completed_courses", set())
                    )
                    if st.button(f"{category} ({completed_courses}/{total_courses})"):
                        st.session_state.selected_subject = category
                        st.rerun()

    def display_courses():
        cols = st.columns([5, 1])
        with cols[0]:
            st.subheader(f"Choisissez un cours dans {st.session_state.selected_subject}")
        with cols[1]:
            if st.button(icon="↩️", label="Retour"):
                del st.session_state.selected_subject
                st.rerun()
        courses = db_courses.get_themes_by_matiere(st.session_state.selected_subject)
        if not courses:
            st.warning("Aucun cours disponible.")
            return
        cols = st.columns(2)
        for i, course in enumerate(courses):
            with cols[i % 2]:
                if st.button(course):
                    st.session_state.selected_course = course
                    # Reset quiz-related session state variables
                    st.session_state.quiz_data = []
                    st.session_state.current_question_index = 0
                    st.session_state.score = 0
                    st.session_state.completed_quiz = False
                    st.session_state.time_spent = []
                    st.session_state.answers = []
                    st.session_state.quiz_started = False
                    st.rerun()
                    

   
    def get_chapter_summary(rag_chap, chapter: str, course_text: str) -> str:
        """
        Récupère le résumé du chapitre depuis le cache de la session.
        Si le résumé n'est pas présent, il est généré via rag_chap.generate_summary()
        et stocké dans le cache.
        
        Args:
            rag_chap: Instance de RAGPipeline utilisée pour générer le résumé.
            chapter (str): Le nom du chapitre.
            course_text (str): Le contenu du cours pour le chapitre donné.
        
        Returns:
            str: Le résumé généré pour le chapitre.
        """
        # Initialisation du cache si nécessaire
        if "cached_summaries" not in st.session_state:
            st.session_state.cached_summaries = {}

        # Si le résumé pour ce chapitre n'est pas en cache, on le génère et on le stocke
        if chapter not in st.session_state.cached_summaries:
            summary = rag_chap.generate_summary(chapitre=chapter, txt=course_text)
            st.session_state.cached_summaries[chapter] = summary

        return st.session_state.cached_summaries[chapter]
    
    def load_course_content(course: str):
        """
        Charge et retourne le contenu du cours pour le cours sélectionné.
        Ce contenu est stocké dans st.session_state pour éviter des rechargements inutiles.
        """
        if "cached_course_content" not in st.session_state:
            st.session_state.cached_course_content = {}
        # Si le cours n'est pas encore en cache, on le charge
        if course not in st.session_state.cached_course_content:
            # Par exemple, on récupère tous les chapitres pour le cours
            chapters = db_courses.get_all_chapters_by_theme(theme=course)
            st.session_state.cached_course_content[course] = chapters
        return st.session_state.cached_course_content[course]
    
    def display_course_content():
        cols = st.columns([5, 1])
        with cols[0]:
            st.subheader(f"Chapitres de {st.session_state.selected_course}")
        with cols[1]:

            # Bouton retour : vide les informations liées au cours
            if st.button(icon="↩️", label="Retour"):
                if "selected_course" in st.session_state:
                    del st.session_state.selected_course
                st.rerun()

        st.header("Contenu du cours")
        # Chargement du contenu du cours avec cache
        chapters = load_course_content(st.session_state.selected_course)

        if chapters:
            # Création de l'instance du pipeline
            rag_chap = RAGPipeline(
                generation_model="ministral-8b-latest",
                max_tokens=850,
                temperature=0.7,
                top_n=1,
            )
            
            with st.spinner('Chargement des chapitres...'):
                for chapter in chapters:
                    with st.expander(f"📚 {chapter}", expanded=False):
                        with st.spinner('Chargement du contenu du cours...'):
                            # Récupération du texte du chapitre depuis la base de données
                            course_text = db_courses.get_courses_content_by_chapter(chapter)
                            # Récupère (et met en cache) le résumé généré pour ce chapitre
                            summary = get_chapter_summary(rag_chap, chapter, course_text)
                            st.markdown(summary)
        else:
            st.warning("Impossible de charger le contenu du cours.")
        # Appel de la fonction du quiz
        if st.button("Démarrer le quiz"):
            display_quiz(db_manager, rag)
        
       

    if not st.session_state.authenticated:
        auth_choice = st.radio("Authentication", ["Login", "Create Account"])
        if auth_choice == "Login":
            login()
        else:
            register()
    else:
        if "selected_subject" not in st.session_state:
            display_subjects()
        elif "selected_course" not in st.session_state:
            display_courses()
        else:
            display_course_content()

if __name__ == '__main__':
    main()