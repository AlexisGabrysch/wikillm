import streamlit as st
from src.metrics_database import RAGMetricsDatabase
import time
from streamlit_autorefresh import st_autorefresh
from src.db.utils import QuizDatabase


# Function to handle user logout
def logout():
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
    
    st.session_state.authenticated = False
    st.session_state.username = ""
    st.success("You have been logged out.")
    st.rerun()


@st.dialog("About WikiLLM", width="large")
def project_description_dialog():
    st.subheader("About WikiLLM")
    st.write(
        "WikiLLM est un projet interactif alliant quiz et cours. "
        "Il vous permet de tester vos connaissances via des quiz générés par l'IA, "
        "d'approfondir vos apprentissages grâce à des cours interactifs et de bénéficier d'explications détaillées."
    )
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        
        with st.container(border=True):
            st.header("Quiz Interactif")
            st.write("Générez et passez des quiz pour tester vos connaissances dans divers domaines du programme de troisieme.")
        
        with st.container(border=True):
            st.header("Cours Interactifs")
            st.write("Accédez à des cours structurés et complets pour approfondir tout le programme de troisieme.")
    with col2:    
        with st.container(border=True):
            st.header("Explications et Indices")
            st.write("Après chaque question, visualisez des explications détaillées et utilisez des indices pour mieux comprendre les réponses.")
        
        with st.container(border=True):
            st.header("Suivi de Progression")
            st.write("Consultez des métriques détaillées et suivez votre progression grâce à des tableaux de bord et des statistiques.")
    
    with st.container(border=True):
        st.header("Administration et Analyse")
        st.write("Les administrateurs disposent d'outils avancés pour analyser les performances et optimiser le contenu pédagogique.")
    
    st.markdown("---")
    st.markdown(
        """
        WikiLLM a été réalisé par [Alexis GABRYSCH](https://github.com/AlexisGabrysch), [Antoine ORUEZABALA](https://github.com/AntoineORUEZABALA), [Lucile PERBET](https://github.com/lucilecpp) et [Alexis DARDELET](https://github.com/AlexisDardelet).  
        Voir le repo sur [GitHub](https://github.com/AlexisGabrysch/wikillm).
        """,
        unsafe_allow_html=True
    )

@st.dialog("Metrics Database")
def metrics_database_dialog():
    # Retrieve metrics from the database
    metrics_db = RAGMetricsDatabase()
    avg_metrics = metrics_db.get_average_metrics()
    """    return {
            "avg_latency": row[0],
            "price_input_total": row[1],
            "price_output_total": row[2],
            "price_total": row[3],
            "gwp_total": row[4],
            "energy_usage_total": row[5]
            
        }
"""
    st.subheader("Metrics Database")
    st.write(f"Average Latency: {round(avg_metrics['avg_latency'] , 2)} seconds")
    st.write(f"Total Price Input: {round(avg_metrics['price_input_total'], 2)} €")
    st.write(f"Total Price Output: {round(avg_metrics['price_output_total'], 2)} €")
    st.write(f"Total Price: {round(avg_metrics['price_total'], 2)} €")
    st.write(f"Total GWP: {round(avg_metrics['gwp_total'], 2)} kgCO2e")
    st.write(f"Total Energy Usage: {round(avg_metrics['energy_usage_total'], 2)} kWh")
    st.write("")
    st.write("Ces données sont calculées sur l'ensemble des métriques enregistrées dans la base de données.")
 




# Function to display the navigation bar with authentication controls
def Navbar():
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
    
    with st.sidebar:
        st.markdown("## Navigation")
        st.page_link('app.py', label='Accueil', icon='🏠')
        st.page_link('pages/admin.py', label='Admin', icon='🔒')
        st.page_link('pages/brevet.py', label='Brevet Blanc', icon='🎓')

        st.markdown("---")  # Separator
        cols = st.columns(2)
        with cols[0]:
            if st.button("About WikiLLM"):
                project_description_dialog()
            
        with cols[1]:
            if st.button("Metrics Database"):
                metrics_database_dialog()
        st.markdown("---")  # Separator
        # Display user information and logout button if authenticated
        if st.session_state.get('authenticated'):
            st.write(f"**Logged in as:** {st.session_state.get('username')}")
            if st.button("Logout"):
                    logout()
            
        else:
            st.write("**Not logged in**")

 
@st.dialog("Teste tes connaissances !", width="large")
def display_quiz(db_manager, rag):
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
                            # Initialisation du timer
            if "timer_active" not in st.session_state:
                st.session_state.timer_active = True

            # Pour le mode speed_test, afficher le timer et la barre de progression
            if st.session_state.mode == "speed_test" and st.session_state.timer_active:
                elapsed_time = time.time() - st.session_state.start_time
                remaining_time = max(30 - int(elapsed_time), 0)
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
                st_autorefresh(interval=20, key="timer_refresh_activation")

                for i, option in enumerate(options):
                    if st.button(option, key=f"option_{i}"):
                        st.session_state.timer_active = False  # Arrêter le timer
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
                if st.button("Afficher l'indice"):
                    st.session_state.show_hint = not st.session_state.show_hint
                    if st.session_state.answers:
                        st.session_state.answers[0]["hint_used"] = st.session_state.show_hint

                    
                if st.session_state.show_hint:
                    st.info(f"**Indice :** {question_data.get('hint', 'Aucun indice disponible.')}")
            else:
                st_autorefresh(interval=20, key="timer_refresh_reactivation")
                # L'utilisateur a répondu : affichez résultat, bonne réponse, explication, et indice
                last_answer = st.session_state.answers[-1]
                with st.container(border=True):
                    st.markdown(f"**Votre réponse :** {last_answer['answer']}")
                with st.container(border=True):
                    st.markdown(f"**Bonne réponse :** {correct_option}")
                if last_answer["correct"]:
                    st.success("Bonne réponse !")
                else:
                    st.error("Mauvaise réponse.")
                with st.container(border=True):
                    st.markdown(f"{question_data.get('explanation', 'Aucune explication disponible.')}")                    
                
                
                if st.button("Question suivante", key="next_question"):
                    st.session_state.current_question_index += 1
                    st.session_state.answer_given = False
                    st.session_state.show_hint = False
                    st.session_state.start_time = time.time()
                    st.session_state.timer_active = True
                    if st.session_state.current_question_index >= len(st.session_state.quiz_data):
                        st.session_state.completed_quiz = True
                        st.session_state.quiz_started = False
                        st.session_state.time_spent = [round(t, 2) for t in st.session_state.time_spent]
                        st.session_state.start_time = None
                        st.session_state.end_time = time.time()
                        st.session_state.completed_courses.add(selected_course)
                        st.success("Quiz terminé !")
                        
                if st.button("Terminer le quiz", key="finish_quiz"):
                    st.session_state.completed_quiz = True
                    st.session_state.quiz_started = False
                    st.session_state.time_spent = [round(t, 2) for t in st.session_state.time_spent]
                    st.session_state.start_time = None
                    st.session_state.end_time = time.time()
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
                with st.expander("Explication", expanded=False):
                    st.markdown(f"{q_data.get('explanation', 'Aucune explication disponible.')}")
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
        
def get_level(score: int) -> str:
    """
    Détermine le niveau basé sur le score.
    
    Args:
        score (int): Le score obtenu.
    
    Returns:
        str: Le niveau correspondant au score.
    """
    if score <= 7:
        return "En difficulté"
    elif score <= 13:
        return "Niveau Correct"
    else:
        return "Déjà Prêt pour le Brevet"
          
def display_brevet_blanc(rag, db_manager):
    st.title("🎓 Brevet Blanc")
    if not hasattr(rag, "subjects") or not rag.subjects:
        rag.fetch_subjects()
    # Initialize brevet state
    if "brevet_started" not in st.session_state:
        st.session_state.brevet_started = False
        st.session_state.brevet_data = None
        st.session_state.current_subject = None
        st.session_state.subject_results = {}
        st.session_state.current_question_index = 0
        st.session_state.answer_given = False
        st.session_state.score = 0
        st.session_state.time_spent = []
        st.session_state.answers = []
        st.session_state.start_time = time.time()

    if not st.session_state.brevet_started:
        if st.button("Commencer le Brevet Blanc"):
            st.session_state.brevet_data = rag.generate_brevet_quiz()
            st.session_state.brevet_started = True
            st.session_state.current_subject = rag.subjects[0]
            st.session_state.start_time = time.time()
            st.rerun()

    if st.session_state.brevet_started:
        current_subject = st.session_state.current_subject
        questions = st.session_state.brevet_data[current_subject]
        
        st.subheader(f"Section: {current_subject}")
        
        # Afficher la question courante
        if st.session_state.current_question_index < len(questions):
            question = questions[st.session_state.current_question_index]
            
            # Afficher le timer
            elapsed_time = time.time() - st.session_state.start_time
            remaining_time = 45 - int(elapsed_time)
            st.markdown(f"### Temps restant : {remaining_time} secondes")
            progress = min(int((elapsed_time / 45) * 100), 100)
            st.progress(progress)
            st_autorefresh(interval=1000, key="timer_refresh")

            st.markdown(f"### Question {st.session_state.current_question_index + 1}: {question['question_text']}")
            
            # Si le temps est écoulé
            if elapsed_time >= 45 and not st.session_state.answer_given:
                st.session_state.time_spent.append(45)
                st.session_state.answers.append({"correct": False})
                st.session_state.answer_given = True
                st.rerun()

            # Afficher les options si pas encore répondu
            if not st.session_state.answer_given:
                for i, option in enumerate(question['options']):
                    if st.button(option, key=f"option_{i}"):
                        answer_time = time.time() - st.session_state.start_time
                        st.session_state.time_spent.append(answer_time)
                        correct = (i == question['correct_index'])
                        if correct:
                            st.session_state.score += 1
                        st.session_state.answers.append({"correct": correct})
                        st.session_state.answer_given = True
                        st.session_state.start_time = time.time()  # Reset timer for next question
                        st.rerun()
            else:
                # Passer automatiquement à la question suivante 
                    st.session_state.current_question_index += 1
                    st.session_state.answer_given = False
                    st.session_state.start_time = time.time()
                    st.rerun()
        else:
            # Section terminée
            score = st.session_state.score
            st.session_state.subject_results[current_subject] = {
                "score": score,
                "level": get_level(score)
            }
            

            next_subject_index = rag.subjects.index(current_subject) + 1
            if next_subject_index < len(rag.subjects):
                st.session_state.current_subject = rag.subjects[next_subject_index]
                st.session_state.current_question_index = 0
                st.session_state.score = 0
                st.session_state.answers = []
                st.session_state.time_spent = []
                st.session_state.start_time = time.time()
                st.rerun()
            else:
                display_brevet_results(rag, db_manager)
                st.session_state.brevet_started = False      
        
        # Place this button in a container that is always rendered during the brevet.
        with st.container():
            if st.button("Terminer le brevet", key="finish_brevet_always"):
                st.session_state.brevet_started = False
                st.rerun()

def display_brevet_results(rag, db_manager):
    st.header("📊 Résultats du Brevet Blanc")
    
    results = st.session_state.subject_results
    classifications = {subj: data["level"] for subj, data in results.items()}
    recommendations = rag.get_brevet_recommendations(classifications)
    
    for subject, data in results.items():
        with st.expander(f"📚 {subject}"):
            st.write(f"Score: {data['score']}/20")
            st.write(f"Niveau: {data['level']}")
    
    st.write("### Recommandation Globale")
    for rec in recommendations["global"]:
        st.write(f"• {rec}")
    
    # Sauvegarder les résultats
    db_manager.save_brevet_result(st.session_state.user_id, results)

@st.dialog("Paramètres Utilisateur", width="medium")
def user_settings_dialog():
    st.subheader("Paramètres Utilisateur")
    current_username = st.session_state.get("username", "User")
    st.write(f"Pseudo actuel : **{current_username}**")
    
    with st.form("change_username_form"):
        new_username = st.text_input("Nouveau pseudo", placeholder="Entrez le nouveau pseudo")
        if st.form_submit_button("Changer le pseudo"):
            db = QuizDatabase()
            success = db.change_username(current_username, new_username)
            if success:
                st.success("Pseudo modifié!")
                st.session_state.username = new_username
            else:
                st.error("Pseudo deja utilisé. Veuillez en choisir un autre.")
                time.sleep(3)
            st.rerun()
            
    
    st.markdown("---")
    
    with st.form("change_password_form"):
        old_password = st.text_input("Ancien mot de passe", type="password")
        new_password = st.text_input("Nouveau mot de passe", type="password")
        if st.form_submit_button("Changer le mot de passe"):
            db = QuizDatabase()
            success = db.change_password(current_username, old_password, new_password)
            if success:
                st.success("Mot de passe modifié!")
            else:
                st.error("Échec du changement de mot de passe.")
            st.rerun()

def Navbar():
    st.markdown(
        """
        <style>
        /* Style pour le bouton utilisateur rond */
        button[data-baseweb="button"][id="user_settings_btn"] {
            border-radius: 50%;
            width: 40px;
            height: 40px;
            padding: 0;
            background-color: #0073e6;
            color: white;
            font-weight: bold;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
    
    with st.sidebar:
        # Bouton rond en haut à gauche avec l'initiale de l'utilisateur
        if st.session_state.get('authenticated'):
            initial = st.session_state.get("username", "User")[0].upper()
            if st.button(initial, key="user_settings_btn", help="Paramètres Utilisateur"):
                user_settings_dialog()
        
        st.markdown("## Navigation")
        st.page_link('app.py', label='Accueil', icon='🏠')
        st.page_link('pages/admin.py', label='Admin', icon='🔒')
        st.page_link('pages/brevet.py', label='Brevet Blanc', icon='🎓')
        st.page_link('pages/kahootquiz.py', label='Kahoot', icon='🧠')
        st.markdown("---")
        
        cols = st.columns(2)
        with cols[0]:
            if st.button("About WikiLLM"):
                project_description_dialog()
        with cols[1]:
            if st.button("Metrics Database"):
                metrics_database_dialog()
        st.markdown("---")
        
        if st.session_state.get('authenticated'):
            st.write(f"**Logged in as:** {st.session_state.get('username')}")
            if st.button("Logout"):
                logout()
        else:
            st.write("**Not logged in**")
            
            
