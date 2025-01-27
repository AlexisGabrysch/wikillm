# FILE: app.py
import asyncio
import streamlit as st
from pages.ressources.components import Navbar
from src.database import DatabaseManager
from src.rag import RAGPipeline
from src.ml_model import classify_answer
from dotenv import find_dotenv, load_dotenv
import os
import random

st.set_page_config(page_title="WikiLLM", page_icon="📚", layout="wide")

def main():
    
    # Charger les variables d'environnement
    load_dotenv(find_dotenv())
    API_KEY = os.getenv("MISTRAL_API_KEY")
    
    # Initialisation de la base de données et du pipeline RAG
    db_manager = DatabaseManager(db_path="./chromadb_data")
    rag = RAGPipeline(
        generation_model="mistral-large-latest",
        role_prompt="Tu es un assistant pédagogique pour le programme de lycée français.",
        db_path="./chromadb_data",
        max_tokens=300,
        temperature=0.9,
        top_n=1,
    )

    # Injecter du CSS pour que les boutons occupent toute la largeur
    st.markdown(
        """
        <style>
        /* Cible tous les boutons Streamlit pour qu'ils occupent 100% de la largeur de leur conteneur */
        div.stButton > button {
            width: 100%;
            padding: 10px;
            font-size: 16px;
        }
        /* Ajouter un peu de marge entre les lignes de boutons */
        .button-row {
            margin-bottom: 10px;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    # Barre de navigation
    Navbar()

    st.title("🎓 WikiLLM - Quiz et Chat avec l'IA")

    # Séparation des sections
    tabs = st.tabs(["Quiz", "Chat"])

    # Section Quiz
    with tabs[0]:
        # Initialisation des variables de session
        if "correct_answers" not in st.session_state:
            st.session_state["correct_answers"] = 0
        if "total_questions" not in st.session_state:
            st.session_state["total_questions"] = 0
        if "hints_requested" not in st.session_state:
            st.session_state["hints_requested"] = 0
        if "current_question" not in st.session_state:
            st.session_state["current_question"] = None
        if "user_answer" not in st.session_state:
            st.session_state["user_answer"] = None


        st.sidebar.markdown(f"## Score: {st.session_state['correct_answers']}")

        # Charger les sujets
        topics = db_manager.get_topics()

        # Vérifier si des sujets sont disponibles
        if not topics:
            st.warning("Aucun sujet disponible. Veuillez ajouter des documents à la base de données.")
            return

        # Sélection du sujet
        selected_topic = st.selectbox("Choisissez un sujet :", topics)

       

                # Bouton pour générer une question
        if st.button("Générer une question", key="generate_question_button"):
            quiz_data = rag.generate_quiz_question(selected_topic)
            if quiz_data["correct_index"] == -1:
                st.error(quiz_data["question"])
            else:
                st.session_state["current_question"] = quiz_data
                st.session_state["user_answer"] = None
                st.session_state["total_questions"] += 1
            st.rerun()  # Assurez la mise à jour immédiate de l'interface

        # Afficher la question actuelle et les options
        if st.session_state["current_question"]:
            quiz_data = st.session_state["current_question"]
            question = quiz_data["question"]
            options = quiz_data["options"]
            correct_index = quiz_data["correct_index"]
            explanation = quiz_data.get("explanation", "")
            st.markdown(f"### Question:\n{question}")

            # Calculer le nombre de colonnes nécessaires (2 par défaut)
            num_columns = 2
            cols = st.columns(num_columns)  # Crée les colonnes

            # Diviser les options en lignes de 2
            for i in range(0, len(options), num_columns):
                # Créer une ligne de colonnes
                cols = st.columns(num_columns)
                
                for j in range(num_columns):
                    option_index = i + j
                    if option_index < len(options):
                        option = options[option_index]
                        col = cols[j]
                        with col:
                            if st.button(option, key=f"option_{option_index}"):
                                # Valider immédiatement la réponse
                                st.session_state["user_answer"] = option_index
                               

            if st.session_state["user_answer"] is not None:
                # Vérifier la réponse de l'utilisateur
                if st.session_state["user_answer"] == correct_index:
                    st.success("Bonne réponse ! 🎉")
                    st.session_state["correct_answers"] += 1
                else:
                    st.error("Mauvaise réponse. 😔")
                st.session_state["user_answer"] = None  # Réinitialiser la réponse de l'utilisateur
                st.session_state["current_question"] = None  # Réinitialiser la question actuelle
                st.session_state["hints_requested"] = 0  # Réinitialiser les indices demandés
                correct_index = None  # Réinitialiser l'index correct
                
                # Afficher l'explication
                st.markdown(f"**Explication :** {explanation}")

           
    
            # Bouton pour passer à la prochaine question
            if st.button("Prochaine question", key="next_question_button"):
                quiz_data = rag.generate_quiz_question(selected_topic)

                if quiz_data["correct_index"] == -1:
                    st.error(quiz_data["question"])
                else:
                    st.session_state["current_question"] = quiz_data
                    st.session_state["user_answer"] = None  # Réinitialiser la réponse de l'utilisateur
                    st.session_state["total_questions"] += 1  # Incrémenter ici
                st.rerun()  # Forcer une mise à jour de l'interface utilisateur
            if st.session_state :
                st.write(st.session_state)

    # Section Chat
    with tabs[1]:
        st.header("💬 Discutez avec l'IA")

        # Initialize chat history
        if "chat_history" not in st.session_state:
            st.session_state["chat_history"] = []

        # Display chat history
        for message in st.session_state["chat_history"]:
            if message["role"] == "user":
                st.markdown(f"**Vous :** {message['content']}")
            else:
                st.markdown(f"**IA :** {message['content']}")

        # User input
        user_input = st.text_input("Vous :", key="chat_input")

        if st.button("Envoyer", key="send_button") and user_input:
            # Ajouter le message de l'utilisateur à l'historique
            st.session_state["chat_history"].append({"role": "user", "content": user_input})

            # Préparer l'historique pour le pipeline RAG
            history = st.session_state["chat_history"]

            # Générer une réponse de l'IA
            response = rag.query(user_input, history=history)
            ai_response = response if isinstance(response, str) else "Je n'ai pas compris votre demande."

            st.session_state["chat_history"].append({"role": "assistant", "content": ai_response})

    # Vérification de la présence de la clé API Mistral
    if not API_KEY:
        if 'mistral_api_warning' not in st.session_state:
            st.warning("Vous n'avez pas ajouté votre clé API Mistral dans le fichier `.env`. Veuillez ajouter le fichier `.env` à la racine du projet puis redémarrer l'application.")
            st.session_state['mistral_api_warning'] = True

    if "current_question" not in st.session_state and not st.session_state.get("chat_history"):
        st.title("Bienvenue sur WikiLLM !")

if __name__ == '__main__':
    main()