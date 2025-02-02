# pages/admin.py

import streamlit as st
from pages.ressources.components import Navbar
from src.db.utils import QuizDatabase , CoursesDatabase
import os
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from src.metrics_database import RAGMetricsDatabase
def main():
    Navbar()

    # Assurez-vous que l'utilisateur est authentifié
    if not st.session_state.get('authenticated'):
        st.warning("You must be logged in to access the admin dashboard.")
        return

    db = QuizDatabase()
    rag_metrics_db = RAGMetricsDatabase()
    username = st.session_state.get('username')
    super_user = db.get_super_user(username)

    # Afficher l'interface d'administration en fonction du rôle de l'utilisateur
    if super_user == 1:

        st.header("Super User Dashboard")
        # affichage des métriques
        st.subheader("Metrics Overview")
        metrics = rag_metrics_db.get_all_metrics()
        if metrics:
            df_metrics = pd.DataFrame(metrics)
            st.dataframe(df_metrics)
        else:
            st.warning("No metrics available at the moment.")
            
        # Metrique 
        st.subheader("Vue globale des métriques")
        total_users = db.get_total_users()
        total_questions = db.get_total_questions()
        total_quizzes = db.get_total_quizzes()
        total_mode_speed = db.get_quiz_count_by_mode(1)
        total_mode_normal = db.get_quiz_count_by_mode(0)
        rate_mode_quizz = db.get_average_success_rate_by_mode()
        st.metric("Nombre total d'utilisateurs", total_users)
        st.metric("Nombre total de questions", total_questions)
        st.metric("Nombre total de quizz effectués", total_quizzes)
        st.metric("Nombre de quizz effectué en mode speed", total_mode_speed)
        st.metric("Nombre total de quizz effectué en mode normal", total_mode_normal)
        st.metric("Taux de réussite pour le mode normal (%)", next((item['average_success_rate'] for item in rate_mode_quizz if item['mode'] == 'Normal'), None))
        st.metric("Taux de réussite pour le mode speed (%)", next((item['average_success_rate'] for item in rate_mode_quizz if item['mode'] == 'Speed'), None))
        st.metric("Temps moyen de réponse global", db.get_average_answer_time(None))
        st.metric("Temps moyen de réponse  pour les bonnes réponses", db.get_average_answer_time(True)) # Bonne réponse 
        st.metric("Temps moyen de réponse pour les mauvaises réponses", db.get_average_answer_time(False)) # Mauvaise réponse

        st.header("Vue par Matière et Chapitre")
        
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

            st.plotly_chart(fig_subject_success)
        else:
            st.write("Aucune donnée disponible pour le taux de réussite par sujet.")
                
        # Users Metrics

        st.header("Vue d'ensemble des utilisateurs")
        
        # Récupérer les subjects
        subjects = db.get_subjects()

        # Ajouter des options de filtre
        selected_subject_filter = st.selectbox("Filtrer par matière", ["Tous les sujets"] + subjects)

        # Récupérer les chapitres en fonction du sujet sélectionné
        if selected_subject_filter != "Tous les sujets":
            chapters = db.get_chapters_by_subject(selected_subject_filter)
        else:
            chapters = db.conn.execute("SELECT DISTINCT chapter FROM questions;").fetchall()
            chapters = [chapter[0] for chapter in chapters]

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
                "avg_answer_time": "Temps de Réponse Moyen (s)"
            })

            # Afficher les données dans un tableau
            st.subheader("Métriques des Utilisateurs")
            st.dataframe(df_users_metrics.sort_values(by="Taux de Réussite (%)", ascending=False), use_container_width=True)
        else:
            st.warning("Aucune donnée disponible pour ces filtres actuellement")

    # Vue d'un utilisateur
    st.subheader("Zoom sur un utilisateur")
    usernames = db.get_usernames()

    # Ajouter un filtre pour sélectionner l'utilisateur
    selected_user = st.selectbox("Choisir un utilisateur", usernames)

    if selected_user:
        users = db.conn.execute("SELECT username FROM users WHERE username = ?;", (selected_user,)).fetchall()
        if users:
            user = users[0]

            # Afficher le nombre de quizz et le taux de réussite global
            cols1, cols2, cols3 = st.columns([1, 1, 1])

            with cols1:
                # Calculer le taux de réussite au fil du temps
                taux_reussite_temps = db.get_taux_reussite_user_over_time(user[0])

                if taux_reussite_temps:
                    df = pd.DataFrame(taux_reussite_temps)
                    fig = px.line(df, x="Période", y="Taux de Réussite (%)",
                                title="Évolution du Taux de Réussite dans le temps",
                                markers=True)
                    fig.update_layout(xaxis_title="Période",
                                    yaxis_title="Taux de Réussite (%)",
                                    template="plotly_white",
                                    plot_bgcolor='rgba(0,0,0,0)')
                    st.plotly_chart(fig)
                else:
                    st.info("Aucune donnée de quizz disponible pour cet utilisateur.")

            
            
            with cols2 :
                taux_reussite_subject = db.get_taux_reussite_topics_user(user[0], 'subject')
                if taux_reussite_subject:
                    df_subject = pd.DataFrame(taux_reussite_subject)
                    fig_subject = px.bar(df_subject.sort_values(by="Taux de Réussite (%)", ascending=True), x="Taux de Réussite (%)", y="Sujet",
                                        title="Taux de Réussite par Sujet",
                                        color="Taux de Réussite (%)",
                                        color_continuous_scale='Blues', 
                                        orientation='h')
                    fig_subject.update_layout(xaxis_title="Taux de Réussite (%)",
                                            yaxis_title="Sujet",
                                            template="plotly_white",
                                            xaxis=dict(range=[0, 100], showgrid=True))
                    st.plotly_chart(fig_subject)
                else:
                    st.info("Aucune donnée de quizz par matière disponible pour cet utilisateur.")

            with cols3: 
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
                            chapitres_maitrisés.append(chapitre["Sujet"])
                        elif 31 <= taux <= 79:
                            chapitres_en_cours.append(chapitre["Sujet"])
                        else:
                            chapitres_a_revoir.append(chapitre["Sujet"])

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

        #  # Select Subject
        # subjects = db.get_subjects()
        # selected_subject_gen = st.selectbox("Choisir une matière", subjects)
        
        # # Select Chapter based on subject
        # chapters = db.get_chapters_by_subject(selected_subject_gen)
        # selected_chapter = st.selectbox("Choisir un chapitre", chapters)
        
        st.header("Analyse des questions")
        st.subheader("Analyse générale des questions")

        # Récupérer toutes les questions
        questions = db.conn.execute("SELECT question_id, question_text FROM questions;").fetchall()

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

        # Créer le graph
        fig_question = px.bar(
            x=success_rates,
            y=question_texts,
            orientation='h',
            labels={'x': 'Taux de Réussite (%)', 'y': 'Questions'},
            title="Taux de Réussite par question"
        )

        fig_question.update_layout(
            xaxis=dict(range=[0, 100], showgrid=True),
            template="plotly_white"
        )

        fig_question.add_vline(
        x=global_success_rate,
        line_dash="dash",
        line_color="red",
    )
            # Ajouter une annotation
        fig_question.add_annotation(
            x=global_success_rate,
            y=len(question_texts) - 0.3, 
            text=f"Taux de Réussite Global: {global_success_rate:.2f}%",
            showarrow=False,
            arrowhead=1,
            ax=0,
            ay=-40
        )

        st.plotly_chart(fig_question)

        ################# Métrique sur une question
        st.subheader("Métrique sur une question")
        
        # Récupérer toutes les questions
        questions = db.conn.execute("SELECT question_id, question_text, correct_index FROM questions;").fetchall()
        question_options = {q[0]: q for q in questions}
        
        # Sélectionner une question
        question_ids = [q[0] for q in questions]
        selected_question_id = st.selectbox("Select a Question:", options=question_ids, format_func=lambda x: question_options[x][1])
        
        if selected_question_id:
            # Obtenir l'index correct
            correct_index = question_options[selected_question_id][2]

            # Récupérer les statistiques de la question
            stats = db.get_metrics_question(selected_question_id)
            
            st.write(f"Taux de réussite: {stats['success_rate'] * 100:.2f}%")
            st.write(f"Nombre d'apparitions: {stats['total_attempts']}")
            st.write(f"Temps de réponse moyen: {stats['avg_answer_time']:.2f} secondes")
            st.write(f"Nombre d'indices demandés: {stats['total_hints']}")
            st.write(f"Réponse attendue: {stats['correct_answer']}")
            
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
            
            fig.update_layout(
                title="Distribution des Réponses",
                xaxis_title="Options",
                yaxis_title="Nombre de Sélections",
                template="plotly_white"
            )
            
            st.plotly_chart(fig)

        st.header("Database Management")
        if st.button("Clear Database"):
            try:
                # Supprimer les enregistrements dans l'ordre correct pour respecter les contraintes de clé étrangère
                db.conn.execute("DELETE FROM answers;")
                db.conn.execute("DELETE FROM quizzes;")
                db.conn.execute("DELETE FROM questions;")
                db.conn.execute("DELETE FROM users;")
                db.conn.commit()
                st.success("Database has been cleared successfully.")
                st.rerun()
            except Exception as e:
                st.error(f"An error occurred while clearing the database: {e}")

############################################################################################################
    # Si pas super_user alors afficher l'interface de l'utilisateur normal
    else : 
        st.title(f"Tableau de bords de {username}")
        st.header("Super User Dashboard")
        # affichage des métriques
        st.subheader("Metrics Overview")
        metrics = rag_metrics_db.get_all_metrics()
        print(metrics)
        if metrics:
            df_metrics = pd.DataFrame(metrics)
            st.dataframe(df_metrics)
        else:
            st.warning("No metrics available at the moment.")
        users = db.conn.execute(
            "SELECT username FROM users WHERE username = ?;",
            (username,)).fetchall()
        if users:
            user = users[0]
            total_quizzes = db.get_quizz_id(user[0])
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
                            Vous avez réalisé <br> <span style="color: #007BFF; font-weight: bold;">{total_quizzes}</span> quizz au total
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
                            avec un taux de réussite global de <br> <span style="color: #007BFF; font-weight: bold;">{round(taux_reussite * 100, 2)}%</span>
                        </h2>
                    </div>
                    """,
                    unsafe_allow_html=True,
    )      
    
            with cols2:
                # Calculer le taux de réussite au fil du temps
                taux_reussite_temps = db.get_taux_reussite_user_over_time(user[0])

                if taux_reussite_temps:
                    df = pd.DataFrame(taux_reussite_temps)
                    fig = px.line(df, x="Période", y="Taux de Réussite (%)",
                                    title="Évolution du Taux de Réussite dans le temps",
                                    markers=True)
                    fig.update_layout(xaxis_title="Période",
                                        yaxis_title="Taux de Réussite (%)",
                                        template="plotly_white",
                                        plot_bgcolor='rgba(0,0,0,0)',
                                        
                                        )
                    st.plotly_chart(fig)
                else:
                    st.info("Aucune donnée de quizz disponible pour cet utilisateur.")
       
        st.header("Vue par Matière")
        user = None
        if users :
            user = users[0]
            taux_reussite_subject = db.get_taux_reussite_topics_user(user[0], 'subject')
            if taux_reussite_subject:
                df_subject = pd.DataFrame(taux_reussite_subject)
                fig_subject = px.bar(df_subject.sort_values(by="Taux de Réussite (%)", ascending=True), x="Taux de Réussite (%)", y="Sujet",
                                    title="Taux de Réussite par Sujet",
                                    color="Taux de Réussite (%)",
                                    color_continuous_scale='Blues', 
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
                        chapitres_maitrisés.append(chapitre["Sujet"])
                    elif 31 <= taux <= 79:
                        chapitres_en_cours.append(chapitre["Sujet"])
                    else:
                        chapitres_a_revoir.append(chapitre["Sujet"])
            
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
            
            
            st.title("Paramètres du compte")

            cols3, cols4 = st.columns([1, 1])

            with cols3:
                st.header("Changer le mot de passe")
                old_password = st.text_input("Ancien mot de passe", type="password")
                new_password = st.text_input("Nouveau mot de passe", type="password")
                confirm_password = st.text_input("Confirmer le nouveau de passe", type="password")
            
                if st.button("Changer le mot de passe"):
                    if new_password != confirm_password:
                        st.error("Les mots de passe ne correspondent pas.")
                    else:
                        username = st.session_state.get('username')
                        success = db.change_password(username, old_password, new_password)
                        if success:
                            st.success("Mot de passe changé avec succès !")
                        else:
                            st.error("Echec du changement de mot de passe. Assurez-vous que l'ancien mot de passe est le bon")
            with cols4:
                st.header("Changer le nom d'utilisateur")
                new_username = st.text_input("Nouveau nom d'utilisateur")
                
                if st.button("Changer le nom d'utilisateur"):
                
                        username = st.session_state.get('username')
                        success = db.change_username(username, new_username)
                        if success:
                            st.success("Nom d'utilisateur changé avec succès !")
                            st.session_state['username'] = new_username
                        else:
                            st.error("Échec du changement de nom d'utilisateur. Le nom d'utilisateur est déjà pris.")
        if user is None:
                st.warning("Aucun utilisateur trouvé. Veuillez ajouter des utilisateurs à la base de données.")
                return

if __name__ == '__main__':
    main()