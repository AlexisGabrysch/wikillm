# pages/admin.py

import streamlit as st
from pages.ressources.components import Navbar
from src.databasebis import DatabaseManagerbis
import os
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

def main():
    Navbar()

    # Assurez-vous que l'utilisateur est authentifié
    if not st.session_state.get('authenticated'):
        st.warning("You must be logged in to access the admin dashboard.")
        return

    # Initialiser le gestionnaire de base de données
    base_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(base_dir, "..", "user_quiz.db")
    db = DatabaseManagerbis(db_path=db_path)

    username = st.session_state.get('username')
    super_user = db.get_super_user(username)

    # Afficher l'interface d'administration en fonction du rôle de l'utilisateur
    if super_user == 1:
        st.header("Super User Dashboard")
        
        st.header("Admin Dashboard")
        
        # Metrique 
        st.subheader("Vue globale des métrique")
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
        # Ajouter à la base le temps de réponse pour chaque question
    
        # Questions Performance
        # st.subheader("Questions Performance")
        # question_metrics = db.get_questions_metrics()
        # fig = px.bar(question_metrics, x='question_text', y='correct_rate', title='Correct Rate per Question')
        # st.plotly_chart(fig)

        st.header("Vue par Matière et chapitre")
        
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
                
        # Users Overview
        st.subheader("Users Overview")
        users_data = db.get_users_data()
        fig_users = px.pie(users_data, names='username', values='quiz_count', title='Quizzes per User')
        st.plotly_chart(fig_users)
        
        # Generate New Questions
        st.subheader("Generate New Questions")
        selected_topic = st.selectbox("Choose Topic", db.get_subjects())
        if st.button("Generate Question"):
            new_question = db.generate_question(selected_topic)
            st.write("**Question:**", new_question['question_text'])
            st.write("**Options:**", new_question['options'])
            st.write("**Explanation:**", new_question['explanation'])
            if st.button("Validate and Save"):
                db.add_question(new_question['question_text'], new_question['options'], new_question['correct_index'], selected_topic, new_question['chapter'])
                st.success("Question added to the database.")
        
        # Custom Graphs
        st.subheader("Custom Graphs")
        x_axis = st.selectbox("Select X-axis", options=['Metric1', 'Metric2', 'Metric3'])  # Replace with actual metrics
        y_axis = st.selectbox("Select Y-axis", options=['MetricA', 'MetricB', 'MetricC'])  # Replace with actual metrics
        if st.button("Generate Graph"):
            custom_data = db.get_custom_graph_data(x_axis, y_axis)
            fig_custom = px.scatter(custom_data, x=x_axis, y=y_axis, title=f"{y_axis} vs {x_axis}")
            st.plotly_chart(fig_custom)
        
        # Leaderboard
        st.subheader("Top 10")
        leaderboard = db.get_leaderboard()
        leaderboard_sorted = sorted(leaderboard, key=lambda x: x['success_rate'], reverse=True)

        # Add Success Rate to Leaderboard Table
        leaderboard_display = [
            {
                "Utilisateur": user['username'],
                "Taux de réussite globale (%)": f"{user['success_rate']:.2f}",
                "Nombre de quizz total": user['total_quizzes']
                
            } for user in leaderboard_sorted
        ]
        
        st.table(leaderboard_display)

        st.header("Answer Distribution by Question")
        
        # Récupérer toutes les questions
        questions = db.conn.execute("SELECT question_id, question_text, correct_index FROM questions;").fetchall()
        question_options = {q[0]: q for q in questions}
        
        # Sélectionner une question
        question_ids = [q[0] for q in questions]
        selected_question_id = st.selectbox("Select a Question:", options=question_ids, format_func=lambda x: question_options[x][1])
        
        if selected_question_id:
            # Obtenir l'index correct
            correct_index = question_options[selected_question_id][2]
            
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

    # Si pas super_user alors afficher l'interface de l'utilisateur normal
    else : 
        st.title(f"Tableau de bords de {username}")
        
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
                                        plot_bgcolor='rgba(0,0,0,0)'
                                        )
                    st.plotly_chart(fig)
                else:
                    st.info("Aucune donnée de quizz disponible pour cet utilisateur.")

    
    # Si pas super_user alors afficher l'interface de l'utilisateur normal
    # else:
    #     st.title(f"Tableau de bords de {username}")
    
    #     users = db.conn.execute(
    #         "SELECT username FROM users WHERE username = ?;",
    #         (username,)).fetchall()
    #     if users:
    #         user = users[0]
    
    #         # Ajouter un filtre pour sélectionner le chapitre ou le sujet
    #         filter_option = st.selectbox("Filtrer par", ["Aucun", "Chapitre", "Sujet"])
    
    #         if filter_option == "Chapitre":
    #             chapitres = db.conn.execute("SELECT DISTINCT chapter FROM questions;").fetchall()
    #             chapitre_selectionne = st.selectbox("Sélectionner un chapitre", [chap[0] for chap in chapitres])
    #             total_quizzes = db.get_quizz_id_by_topics(user[0], chapitre_selectionne)
    #             taux_reussite = db.get_taux_reussite_user_by_topics(user[0], chapitre_selectionne)
            
    #         elif filter_option == "Sujet":
    #             sujets = db.conn.execute("SELECT DISTINCT subject FROM questions;").fetchall()
    #             sujet_selectionne = st.selectbox("Sélectionner un sujet", [suj[0] for suj in sujets])
    #             total_quizzes = db.get_quizz_id_by_topics(user[0], sujet_selectionne)
    #             taux_reussite = db.get_taux_reussite_user_by_topics(user[0], sujet_selectionne)
            
    #         else:
    #             total_quizzes = db.get_quizz_id(user[0])
    #             taux_reussite = db.get_taux_reussite_user(user[0])
    
    #         # Afficher le nombre de quizz et le taux de réussite
    #         cols1, cols2 = st.columns([1, 1])
    
    #         with cols1:
    #             st.write("")
    #             st.write("")
    #             st.markdown(
    #                 f"""
    #                 <div style="background-color: #F0F2F6; padding: 20px; border-radius: 15px; text-align: center; width: 100%; margin: auto;">
    #                     <h2 style="color: #333; font-family: 'Arial', sans-serif; font-weight: 500; font-size: 22px;">
    #                         Vous avez réalisé <br> <span style="color: #007BFF; font-weight: bold;">{total_quizzes}</span> quizz au total
    #                     </h2>
    #                 </div>
    #                 """,
    #                 unsafe_allow_html=True,
    #             )
    #             st.write("")
    #             st.write("")
    #             st.write("")
    #             st.write("")
    #             st.write("")
    
    #             st.markdown(
    #                 f"""
    #                 <div style="background-color: #F0F2F6; padding: 20px; border-radius: 15px; text-align: center; width: 100%; margin: auto;">
    #                     <h2 style="color: #333; font-family: 'Arial', sans-serif; font-weight: 500; font-size: 22px;">
    #                         avec un taux de réussite global de <br> <span style="color: #007BFF; font-weight: bold;">{round(taux_reussite * 100, 2)}%</span>
    #                     </h2>
    #                 </div>
    #                 """,
    #                 unsafe_allow_html=True,
    #             )
    
    #         with cols2:
    #             # Calculer le taux de réussite au fil du temps
    #             taux_reussite_temps = db.get_taux_reussite_user_over_time(user[0])
    
    #             if taux_reussite_temps:
    #                 df = pd.DataFrame(taux_reussite_temps)
    #                 fig = px.line(df, x="Période", y="Taux de Réussite (%)",
    #                               title="Évolution du Taux de Réussite dans le temps",
    #                               markers=True)
    #                 fig.update_layout(xaxis_title="Période",
    #                                   yaxis_title="Taux de Réussite (%)",
    #                                   template="plotly_white",
    #                                   plot_bgcolor='rgba(0,0,0,0)')
    #                 st.plotly_chart(fig)
    #             else:
    #                 st.info("Aucune donnée de quizz disponible pour cet utilisateur.")
    
        
        st.header("Vue par Matière")
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
                                      template="plotly_white"
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


if __name__ == '__main__':
    main()