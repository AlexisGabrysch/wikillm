import streamlit as st
from pages.ressources.components import Navbar
from src.db.utils import QuizDatabase ,CoursesDatabase
from src.rag import RAGPipeline
from dotenv import find_dotenv, load_dotenv
import os
import time
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="WikiLLM", page_icon="📚", layout="wide")

def main():
 
    st.title("❔ WikiLLM - Quiz et Cours interactifs 📚 ")
   
           
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
        st.subheader(f"Choisissez un cours dans {st.session_state.selected_subject}")
        if st.button("Retour", key="back-button"):
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
                    
    @st.dialog("🎉 Teste tes connaissances !", width="large")
    def display_quiz(db_manager):
        """
        Crée et gère un quiz avec toutes les questions de la base de données
        liées au thème (matière+chapitre) sélectionné dans st.session_state.
        Pour chaque question, le temps de réponse est calculé et le résultat est inséré en BDD.
        L'explication de la réponse et l'indice (optionnel) sont affichés.
        """
        
        selected_subject = st.session_state.get("selected_subject", "")
        selected_course = st.session_state.get("selected_course", "")
        st.header(f"Quiz - {selected_subject} - {selected_course}")
        
        all_questions = db_manager.get_questions_by_subject_and_chapter(
            subject=selected_subject, chapter=selected_course
        )
        
        if not all_questions:
            st.warning("Aucune question disponible pour ce thème.")
            # Si aucune question n'existe, on peut générer et sauvegarder un quiz
            quizz = rag.generate_quizz_questions(selected_course, nbr_questions=10)
            rag.save_questions(quizz, subject=selected_subject, chapter=selected_course)
            return

        # Récupération (ou création) du quiz en BDD
        quiz_id = db_manager.get_or_create_quiz(selected_subject, selected_course)
        
        # Initialiser l'état du quiz
        if "quiz_data" not in st.session_state:
            st.session_state.quiz_data = all_questions
        if "current_question_index" not in st.session_state:
            st.session_state.current_question_index = 0
        if "score" not in st.session_state:
            st.session_state.score = 0
        if "completed_quiz" not in st.session_state:
            st.session_state.completed_quiz = False
        if "time_spent" not in st.session_state:
            st.session_state.time_spent = []
        if "answers" not in st.session_state:
            st.session_state.answers = []
        if "quiz_started" not in st.session_state:
            st.session_state.quiz_started = False
        if "answer_given" not in st.session_state:
            st.session_state.answer_given = False
        if "show_hint" not in st.session_state:
            st.session_state.show_hint = False

        # Choix du mode quiz
        if not st.session_state.quiz_started:
            mode = st.radio("Choisissez le mode de quiz :", ("speed_test", "chill"))
            if st.button("Commencer le quiz"):
                st.session_state.quiz_data = all_questions
                st.session_state.current_question_index = 0
                st.session_state.score = 0
                st.session_state.completed_quiz = False
                st.session_state.time_spent = []
                st.session_state.answers = []
                st.session_state.mode = mode
                st.session_state.quiz_started = True
                st.session_state.answer_given = False
                st.session_state.show_hint = False
                st.session_state.start_time = time.time()

        if st.session_state.quiz_started and not st.session_state.completed_quiz:
            # S'il reste des questions
            if st.session_state.current_question_index < len(st.session_state.quiz_data):
                question_data = st.session_state.quiz_data[st.session_state.current_question_index]
                question = question_data["question_text"]
                options = [
                    question_data["option1"],
                    question_data["option2"],
                    question_data["option3"],
                    question_data["option4"],
                ]
                correct_index = question_data["correct_index"]
                correct_option = options[correct_index]
                
                st.markdown(f"### Question {st.session_state.current_question_index + 1} : {question}")
                
                # Pour le mode speed_test, afficher le timer et la barre de progression
                if st.session_state.mode == "speed_test":
                    elapsed_time = time.time() - st.session_state.start_time
                    remaining_time = 30 - int(elapsed_time)
                    st.markdown(f"### Temps restant : {remaining_time} secondes")
                    progress = min(int((elapsed_time / 30) * 100), 100)
                    st.progress(progress)
                    st_autorefresh(interval=1000, key="timer_refresh")
                    
                    # Si le temps est écoulé et qu'aucune réponse n'a été donnée
                    if elapsed_time >= 30 and not st.session_state.answer_given:
                        st.session_state.time_spent.append(30)
                        db_manager.insert_result(
                            quiz_id=quiz_id,
                            user_id=st.session_state.user_id,
                            question_id=question_data["question_id"],
                            selected_option=None,
                            is_correct=False,
                            answer_time=30,
                            hint_used=False
                        )
                        st.session_state.answers.append({
                            "question": question,
                            "answer": None,
                            "correct": False,
                            "hint_used": False
                        })
                        st.session_state.answer_given = True

                # Affichage des options si aucune réponse n'a encore été soumise
                if not st.session_state.answer_given:
                    st_autorefresh(interval=100, key="timer_refresh_activation")

                    for i, option in enumerate(options):
                        if st.button(option, key=f"option_{i}"):
                            answer_time = time.time() - st.session_state.start_time
                            st.session_state.time_spent.append(answer_time)
                            correct = (i == correct_index)
                            if correct:
                                st.session_state.score += 1
                            db_manager.insert_result(
                                quiz_id=quiz_id,
                                user_id=st.session_state.user_id,
                                question_id=question_data["question_id"],
                                selected_option=i + 1,
                                is_correct=correct,
                                answer_time=answer_time,
                                hint_used=st.session_state.show_hint
                            )
                            st.session_state.answers.append({
                                "question": question,
                                "answer": option,
                                "correct": correct,
                                "hint_used": st.session_state.show_hint
                            })
                            st.session_state.answer_given = True
                            st.session_state.show_hint = False  # Réinitialiser l'affichage de l'indice
                            # Bouton pour afficher/masquer l'indice
                    if st.button("Afficher l'indice", key=f'button_hint_{i}'):
                        st.session_state.show_hint = not st.session_state.show_hint
                        st.session_state.answers[-1]["hint_used"] = st.session_state.show_hint
                    if st.session_state.show_hint:
                        st.info(f"**Indice :** {question_data.get('hint', 'Aucun indice disponible.')}")
                else:
                    st_autorefresh(interval=100, key="timer_refresh_reactivation")
                    # L'utilisateur a répondu : affichez résultat, bonne réponse, explication, et indice
                    last_answer = st.session_state.answers[-1]
                    st.markdown(f"**Votre réponse :** {last_answer['answer']}")
                    st.markdown(f"**Bonne réponse :** {correct_option}")
                    if last_answer["correct"]:
                        st.success("Bonne réponse !")
                    else:
                        st.error("Mauvaise réponse.")
                    st.markdown(f"**Explication :** {question_data.get('explanation', 'Aucune explication disponible.')}")
                    
                    
                    
                    if st.button("Question suivante", key="next_question"):
                        st.session_state.current_question_index += 1
                        st.session_state.answer_given = False
                        st.session_state.show_hint = False
                        st.session_state.start_time = time.time()
                        if st.session_state.current_question_index >= len(st.session_state.quiz_data):
                            st.session_state.completed_quiz = True
                            st.session_state.quiz_started = False
                            st.session_state.time_spent = [round(t, 2) for t in st.session_state.time_spent]
                            st.session_state.start_time = None
                            st.session_state.end_time = time.time()
                            st.session_state.completed_courses.add(selected_course)
                            st.success("Quiz terminé !")
                        
        # In the display_quiz function, update the final recap block to add the completed course if at least 50% correct.
        # Affichage du récapitulatif final si le quiz est terminé
        if st.session_state.completed_quiz:
            st.header("Récapitulatif du Quiz")
            total_questions = len(st.session_state.quiz_data)
            st.markdown(f"### Score final : {st.session_state.score} / {total_questions}")
            st.write("**Détails des questions :**")
            for i, q_data in enumerate(st.session_state.quiz_data):
                question = q_data["question_text"]
                correct_index = q_data["correct_index"]
                correct_option = [
                    q_data["option1"],
                    q_data["option2"],
                    q_data["option3"],
                    q_data["option4"],
                ][correct_index]
                st.write(f"Question {i + 1}: {question}")
                if i < len(st.session_state.time_spent):
                    st.write(f"Temps passé : {st.session_state.time_spent[i]:.2f} secondes")
                else:
                    st.write("Temps passé : N/A")
                if i < len(st.session_state.answers):
                    answer = st.session_state.answers[i]
                    st.write(f"Votre réponse : {answer['answer']}")
                    st.write(f"Bonne réponse : {correct_option}")
                    st.write(f"Correct : {'Oui' if answer['correct'] else 'Non'}")
                    st.markdown(f"**Explication :** {q_data.get('explanation', 'Aucune explication disponible.')}")
                    if answer.get("hint_used", False):
                        st.info(f"**Indice utilisé :** {q_data.get('hint', 'Aucun indice disponible.')}")
            
            # Mise à jour de la table des cours complétés si le score est au moins de 50%
            if total_questions > 0 and st.session_state.score >= total_questions * 0.5:
                db_manager.add_completed_course(user_id=st.session_state.user_id, course_title=selected_course)
                st.success("Félicitations ! Vous avez validé ce chapitre et il a été ajouté à vos cours complétés.")
            else:
                st.warning("Vous n'avez pas validé ce chapitre. Réessayez pour obtenir au moins 50% de bonnes réponses.")
            
            # Réinitialiser l'état pour permettre de refaire un quiz
            st.session_state.quiz_started = False
                        
            
    def get_elapsed_time():
        return time.time() - st.session_state.start_time
    
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
        st.subheader(f"Cours : {st.session_state.selected_course}")

        # Bouton retour : vide les informations liées au cours
        if st.button("Retour", key="back-button" ):
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
            display_quiz(db_manager)
       

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