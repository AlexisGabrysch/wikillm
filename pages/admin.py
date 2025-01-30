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
        st.header("Adminisatreur")

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
        
        st.header("Quiz Responses")
        quizzes = db.conn.execute("""
            SELECT quizzes.quiz_id, users.username, quizzes.timestamp
            FROM quizzes
            JOIN users ON quizzes.user_id = users.user_id;
        """).fetchall()

        for quiz in quizzes:
            st.subheader(f"Quiz ID: {quiz[0]} | User: {quiz[1]} | Timestamp: {quiz[2]}")
            answers = db.conn.execute("""
                SELECT questions.question_text, 
                    answers.selected_option, 
                    answers.is_correct
                FROM answers
                JOIN questions ON answers.question_id = questions.question_id
                WHERE answers.quiz_id = ?;
            """, (quiz[0],)).fetchall()
            
            quiz_details = []
            for answer in answers:
                question, selected, correct = answer
                status = "✅ Correct" if correct else "❌ Incorrect"
                quiz_details.append({
                    "Question": question,
                    "Selected Option": selected if selected else "Aucune réponse",
                    "Status": status
                })
            st.table(quiz_details)
            st.write("---")
        

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
                    st.info("Aucune donnée de quiz disponible pour cet utilisateur.")
        
        
        
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