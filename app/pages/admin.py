# pages/admin.py

import streamlit as st
from pages.ressources.components import Navbar
from src.db.utils import QuizDatabase, CoursesDatabase
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import textwrap

def main():
    Navbar()

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
    # Vérif de l'authentification de l'utilisateur
    if not st.session_state.get('authenticated'):
        st.warning("You must be logged in to access the admin dashboard.")
        return

    db = QuizDatabase()
    username = st.session_state.get('username')
    super_user = db.get_super_user(username)

    # Afficher l'interface d'administration en fonction du rôle de l'utilisateur
    if super_user == 1:

        st.header("📊 Dashboard Administrateur 📊")

            
        # Metrique 
        st.subheader("Métriques générales")
        
        # Custom CSS for metrics
        st.markdown("""
            <style>
            .metric-container {
                font-size: 20px;
                color: #4CAF50;
                background-color: #f9f9f9;
                padding: 10px;
                border-radius: 5px;
                text-align: center;
                margin-bottom: 10px;
            }
            .metric-label {
                font-size: 16px;
                color: #333;
            }
            .metric-value {
                font-size: 24px;
                font-weight: bold;
                color: #000;
            }
            </style>
        """, unsafe_allow_html=True)
        
        total_users = db.get_total_users()
        total_questions = db.get_total_questions()
        average_answer_time_global = db.get_average_answer_time(None)
        average_answer_time_correct = db.get_average_answer_time(True)
        average_answer_time_incorrect = db.get_average_answer_time(False)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"""
                <div class="metric-container">
                    <div class="metric-label">Nombre total d'utilisateurs</div>
                    <div class="metric-value">{total_users}</div>
                </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
                <div class="metric-container">
                    <div class="metric-label">Nombre total de questions posées</div>
                    <div class="metric-value">{total_questions}</div>
                </div>
            """, unsafe_allow_html=True)
        
        col3, col4, col5 = st.columns(3)
        
        with col3:
            st.markdown(f"""
                <div class="metric-container">
                    <div class="metric-label">Temps moyen de réponse global (en s)</div>
                    <div class="metric-value">{average_answer_time_global}</div>
                </div>
            """, unsafe_allow_html=True)
        
        with col4:
            st.markdown(f"""
                <div class="metric-container">
                    <div class="metric-label">Temps moyen de réponse pour les bonnes réponses (en s)</div>
                    <div class="metric-value">{average_answer_time_correct}</div>
                </div>
            """, unsafe_allow_html=True)
        
        with col5:
            st.markdown(f"""
                <div class="metric-container">
                    <div class="metric-label">Temps moyen de réponse pour les mauvaises réponses (en s)</div>
                    <div class="metric-value">{average_answer_time_incorrect}</div>
                </div>
            """, unsafe_allow_html=True)
    
        st.header("Comparatif sur les matières et les chapitres")
        
        # Récupérer les différents subjects
        subjects = db.get_subjects()
        
        # Ajouter une option par défaut
        subjects.insert(0, "Toutes les matières")
        
        # Sélectionner une matière
        selected_subject = st.selectbox("Choisir une matière", subjects)

        # Calcul du taux de réussite par subject
        taux_reussite_subject = [
                {"topics": subject, "success_rate": db.get_taux_reussite_subject(subject)}
                for subject in subjects
            ]
        if selected_subject == "Toutes les matières": 
             
            # Calcul du taux de réussite global
            global_success_rate = db.get_global_success_rate()
            
        else : 
            cursor = db.conn.execute("""
            SELECT DISTINCT chapter
            FROM questions
            WHERE subject = ?;
            """, (selected_subject,))
            chap_dict =  [row[0] for row in cursor.fetchall()]

            # Calcul du taux de réussite par chapitre pour la matière sélectionnée
            taux_reussite_chap = [
                {"topics": chapter, "success_rate": db.get_taux_reussite_chapter(chapter)}
                for chapter in chap_dict
            ]

            # Récupérer le success_rate correspondant à selected_subject
            global_success_rate = next(
            (item['success_rate'] for item in taux_reussite_subject if item['topics'] == selected_subject), 
            None
        )
            taux_reussite_subject = taux_reussite_chap
           
        # Afficher le taux de réussite par sujet
        if taux_reussite_subject:
            
            taux_reussite_subject = [item for item in taux_reussite_subject if item['topics'] != "Toutes les matières"]
            df_subject_success = pd.DataFrame(taux_reussite_subject, columns=['topics', 'success_rate'])

            fig_subject_success = px.bar(
                df_subject_success.sort_values(by='success_rate', ascending=False),
                x='topics',
                y='success_rate',
                labels={'topics': 'Sujet', 'success_rate': 'Taux de Réussite (%)'},
                title='Taux de Réussite Moyen par Sujet',
                text='success_rate'
            )
            # Ajout de la ligne de taux de réussite global
            fig_subject_success.add_hline(y=global_success_rate, 
                                          line_dash='dot', 
                                          line_color='red', 
                                          annotation_text=f"Taux de Réussite Global: {global_success_rate:.2f}%", 
                                          annotation_position='top left',
                                          annotation_font_color='black')
            fig_subject_success.update_traces(texttemplate='%{text:.2f}%')
            fig_subject_success.update_layout(uniformtext_minsize=8, uniformtext_mode='hide')
            fig_subject_success.update_yaxes(range=[0, 1])
            fig_subject_success.update_xaxes(tickmode='array', tickvals=df_subject_success['topics'], ticktext=[f'<br>'.join(textwrap.wrap(label, width=25)) for label in df_subject_success['topics']])

            st.plotly_chart(fig_subject_success)
        else:
            st.write("Aucune donnée disponible pour le taux de réussite par sujet.")
        
        st.subheader("Analyse générale des questions")

        col1, col2 = st.columns(2)
        
        with col1:
            # Select Subject
            subjects = db.get_subjects()
            selected_subject_gen = st.selectbox("Choisir une matière", subjects)
        
        with col2:
            # Select Chapter based on subject
            chapters = db.get_chapters_by_subject(selected_subject_gen)
            selected_chapter = st.selectbox("Choisir un chapitre", chapters)

        # Récupérer toutes les questions
        questions = db.conn.execute("""
            SELECT DISTINCT questions.question_id, questions.question_text
            FROM questions
            JOIN answers ON questions.question_id = answers.question_id
            WHERE questions.chapter = ?;
            """, (selected_chapter,)).fetchall()
       

        # Récupérer les taux de réussite pour toutes les questions
        questions_success_rates = [
            {
                "question_id": q[0],
                "question_text": q[1],
                "success_rate": db.get_taux_reussite_question(q[0])
            }
            for q in questions
        ]

        # Trier les questions par taux de réussite décroissant
        questions_success_rates = sorted(questions_success_rates, key=lambda x: x["success_rate"], reverse=False)

        # Extraire les données pour le graphique
        question_texts = [q["question_text"] for q in questions_success_rates]
        success_rates = [q["success_rate"] * 100 for q in questions_success_rates]

        global_success_rate = db.get_global_success_rate() * 100
        
        # Graphique des taux de réussite par question
        if success_rates:
            fig_question = px.bar(
                x=success_rates,
                y=question_texts,
                orientation='h',
                labels={'x': 'Taux de Réussite (%)', 'y': 'Questions'},
                title="Taux de Réussite par question"
            )

            fig_question.update_layout(
                xaxis=dict(range=[0, 100], showgrid=True), 
                yaxis=dict(
                    tickmode='array',
                    tickvals=list(range(len(question_texts))),
                    # ticktext=[textwrap.shorten(q, width=200, placeholder="...") for q in question_texts]
                    ticktext=[f'<br>'.join(textwrap.wrap(q, width=150)) for q in question_texts]

                ),
                template="plotly_white",
                height=600,
                margin=dict(l=200, r=20, t=50, b=20)
            )

            st.plotly_chart(fig_question)
        else:
            st.warning(f"Aucune donnée disponible pour le cours de {selected_chapter} pour la matière {selected_subject_gen}")

        ################# Métrique sur une question #################
        st.subheader("Métrique sur une question")
        

        # Récupérer toutes les questions
        questions = db.conn.execute(f"""
            SELECT DISTINCT questions.question_id, questions.question_text, correct_index
            FROM questions
            JOIN answers ON questions.question_id = answers.question_id
           WHERE questions.chapter = ?;
        """, (selected_chapter,)).fetchall()
        question_options = {q[0]: q for q in questions}
        
        # Sélectionner une question
        question_ids = [q[0] for q in questions]
        selected_question_id = st.selectbox("Choisissez votre question :", options=question_ids, format_func=lambda x: question_options[x][1])
        
        if selected_question_id:
            # Obtenir l'index correct
            correct_index = question_options[selected_question_id][2]
            correct_index += 1    # Pour faire matcher les index    

            # Récupérer les statistiques de la question
            stats = db.get_metrics_question(selected_question_id)
            
               
            # Display metrics in a single line
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.markdown(f"""
                    <div class="metric-container">
                        <div class="metric-label">Taux de réussite</div>
                        <div class="metric-value">{stats['success_rate'] * 100:.2f}%</div>
                    </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"""
                    <div class="metric-container">
                        <div class="metric-label">Nombre d'apparitions</div>
                        <div class="metric-value">{stats['total_attempts']}</div>
                    </div>
                """, unsafe_allow_html=True)
            
            with col3:
                st.markdown(f"""
                    <div class="metric-container">
                        <div class="metric-label">Temps de réponse moyen</div>
                        <div class="metric-value">{stats['avg_answer_time']:.2f} secondes</div>
                    </div>
                """, unsafe_allow_html=True)
            
            with col4:
                st.markdown(f"""
                    <div class="metric-container">
                        <div class="metric-label">Nombre d'indices demandés</div>
                        <div class="metric-value">{stats['total_hints']}</div>
                    </div>
                """, unsafe_allow_html=True)
            
        
            st.markdown(f"""
                <div class="metric-container">
                    <div class="metric-label">Réponse attendue</div>
                    <div class="metric-value">{stats['correct_answer']}</div>
                </div>
            """, unsafe_allow_html=True)
            
            # Récupérer toutes les réponses pour la question sélectionnée
            answers = db.conn.execute("""
                SELECT selected_option, COUNT(*) as count
                FROM answers
                WHERE question_id = ?
                GROUP BY selected_option;
            """, (selected_question_id,)).fetchall()

            # Initialiser les comptages pour toutes les options
            option_counts = {1:0, 2:0, 3:0, 4:0}
            for answer in answers:
                option = answer[0]
                count = answer[1]
                if option is not None:
                    option_counts[option] = count
            
            # Obtenir les textes des options
            options = db.conn.execute("""
                SELECT option1, option2, option3, option4 FROM questions WHERE question_id = ?;
            """, (selected_question_id,)).fetchall()[0]
            
            labels = [options[i-1] for i in range(1,5)]
            counts = [option_counts[i] for i in range(1,5)]
            
            # Définir les couleurs
            colors = ['red' if i != correct_index else 'green' for i in range(1,5)]
            
            # Créer le graphique à barres
            fig = go.Figure(data=[
                go.Bar(
                    x=labels,
                    y=counts,
                    marker_color=colors
                )
            ])
            wrapped_labels = [f'<br>'.join(textwrap.wrap(label, width=50)) for label in labels]

            fig.update_layout(
                title="Distribution des Réponses",
                xaxis_title="Options",
                yaxis_title="Nombre de Sélections",
                template="plotly_white"
            )
            fig.update_xaxes(tickmode='array', tickvals=labels, ticktext=wrapped_labels)
            
            st.plotly_chart(fig)

        # Users Metrics
        st.header("Leaderboard")
        
        # Récupérer les subjects
        subjects = db.get_subjects()
        col1, col2 = st.columns(2)

        with col1:
            # Ajouter des options de filtre
            selected_subject_filter = st.selectbox("Filtrer par matière", ["Tous les sujets"] + subjects)

            # Récupérer les chapitres en fonction du sujet sélectionné
            if selected_subject_filter != "Tous les sujets":
                chapters = db.get_chapters_by_subject(selected_subject_filter)
            else:
                chapters = db.conn.execute("SELECT DISTINCT chapter FROM questions;").fetchall()
                chapters = [chapter[0] for chapter in chapters]

        with col2:
            selected_chapter_filter = st.selectbox("Filtrer par chapitre", ["Tous les chapitres"] + chapters)

        # Récupérer les métriques des utilisateurs en fonction du filtre
        if selected_subject_filter != "Tous les sujets":
            users_metrics = db.get_users_metrics_by_subject(selected_subject_filter)
        
        elif selected_chapter_filter != "Tous les chapitres":
            users_metrics = db.get_users_metrics_by_chapter(selected_chapter_filter)
        else:
            users_metrics = db.get_users_metrics()
        
        # Convertir les données en DataFrame pour une manipulation plus facile
        df_users_metrics = pd.DataFrame(users_metrics)
        
        # Vérifier si le DataFrame contient des données
        if not df_users_metrics.empty:

            # Renommer les colonnes
            df_users_metrics = df_users_metrics.rename(columns={
                "username": "Nom d'utilisateur",
                "success_rate": "Taux de Réussite (%)",
                "total_quizzes": "Nombre Total de Quizzes",
                "avg_answer_time": "Temps de Réponse Moyen (s) par question"
            })

            # Afficher les données dans un tableau
            st.dataframe(df_users_metrics.sort_values(by="Taux de Réussite (%)", ascending=False), use_container_width=True)
        else:
            st.warning("Aucune donnée disponible pour ces filtres actuellement")

        ########################## Clean Database ##########################
        st.header("Database Management")
        if st.button("Clear Database"):
            try:
                db.clean_database()
                st.success("Database has been cleared successfully.")
                st.rerun()
            except Exception as e:
                st.error(f"An error occurred while clearing the database: {e}")


        
############################################################################################################
    # Si pas super_user alors afficher l'interface de l'utilisateur normal
    else : 
        st.title(f"Bienvenue {username} sur votre Tableau de bords")
 
        users = db.conn.execute(
            "SELECT username FROM users WHERE username = ?;",
            (username,)).fetchall()
        if users:
            user = users[0]
            complet_lessons = db.count_completed_courses_by_user(user[0])
            taux_reussite = db.get_taux_reussite_user(user[0])
    
           # Afficher le nombre de restaurants et de commentaires
            cols1, cols2 = st.columns([1, 1])

            with cols1:
                st.write("")
                st.write("")
                st.markdown(
                    f"""
                    <div style="background-color: #F0F2F6; padding: 20px; border-radius: 15px; text-align: center; width: 100%; margin: auto;">
                        <h2 style="color: #333; font-family: 'Arial', sans-serif; font-weight: 500; font-size: 22px;">
                            Votre taux de réussite au global est de <br> <span style="color: #007BFF; font-weight: bold;">{round(taux_reussite * 100, 2)}%</span>
                        </h2>
                    </div>
                    """,
                    unsafe_allow_html=True,
                    
                    
    )
                st.write("")
                st.write("")
                st.write("")
                st.write("")
                st.write("")

            
                st.markdown(
                    f"""
                    <div style="background-color: #F0F2F6; padding: 20px; border-radius: 15px; text-align: center; width: 100%; margin: auto;">
                        <h2 style="color: #333; font-family: 'Arial', sans-serif; font-weight: 500; font-size: 22px;">
                            Vous avez complété <br> <span style="color: #007BFF; font-weight: bold;">{complet_lessons}</span> cours
                        </h2>
                    </div>
                    """,
                    unsafe_allow_html=True,
    )      
    
            with cols2:
                user = None
                if users :
                    user = users[0]
                    taux_reussite_subject = db.get_taux_reussite_topics_user(user[0], 'subject')
                    if taux_reussite_subject:
                        df_subject = pd.DataFrame(taux_reussite_subject)
                        fig_subject = px.bar(df_subject.sort_values(by="Taux de Réussite (%)", ascending=True), x="Taux de Réussite (%)", y="subject",
                                            title="Taux de Réussite par Sujet",
                                            color="Taux de Réussite (%)",
                                            color_continuous_scale=['#ADD8E6', '#00008B'], 
                                            orientation='h')
                        fig_subject.update_layout(xaxis_title="Taux de Réussite (%)",
                                                yaxis_title="Sujet",
                                                template="plotly_white",
                                                xaxis=dict(range=[0, 100], showgrid=True)
                                                )
                        st.plotly_chart(fig_subject)
                    else:
                        st.info("Aucune donnée de quizz par matière disponible pour cet utilisateur.")
                    
            # Récupérer le taux de réussite par chapitre
            taux_reussite_topics = db.get_taux_reussite_topics_user(user[0], 'chapter')
            
            if taux_reussite_topics:
                # Initialiser les listes pour chaque catégorie
                chapitres_maitrisés = []
                chapitres_en_cours = []
                chapitres_a_revoir = []
            
                # Catégoriser les chapitres en fonction du taux de réussite
                for chapitre in taux_reussite_topics:
                    taux = chapitre["Taux de Réussite (%)"]
                    if taux >= 80:
                        chapitres_maitrisés.append(chapitre["chapter"])
                    elif 31 <= taux <= 79:
                        chapitres_en_cours.append(chapitre["chapter"])
                    else:
                        chapitres_a_revoir.append(chapitre["chapter"])
            
                # Déterminer la longueur maximale des listes
                max_len = max(len(chapitres_maitrisés), len(chapitres_en_cours), len(chapitres_a_revoir))
            
                # Remplir les listes plus courtes avec des chaînes vides pour aligner les colonnes
                chapitres_maitrisés += [''] * (max_len - len(chapitres_maitrisés))
                chapitres_en_cours += [''] * (max_len - len(chapitres_en_cours))
                chapitres_a_revoir += [''] * (max_len - len(chapitres_a_revoir))
            
                # Créer un DataFrame avec les trois catégories
                df_categorized = pd.DataFrame({
                    "Chapitres maîtrisés (≥ 80%)": chapitres_maitrisés,
                    "Chapitres en cours de maîtrise (31% - 79%)": chapitres_en_cours,
                    "Chapitres à revoir (< 30%)": chapitres_a_revoir
                })
            
                st.subheader("Tableau des Chapitres par Niveau de Maîtrise")
                st.table(df_categorized)
            else:
                st.info("Aucune donnée de quizz par chapitre disponible pour cet utilisateur.")
            
        if user is None:
                st.warning("Aucun utilisateur trouvé. Veuillez ajouter des utilisateurs à la base de données.")
                return

if __name__ == '__main__':
    main()