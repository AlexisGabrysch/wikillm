import asyncio
import streamlit as st
from pages.ressources.components import Navbar
from src.database import DatabaseManager
from src.rag import RAGPipeline
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

    st.title(" WikiLLM - Quiz et Chat avec l'IA")

    # Initialisation des variables de session
    if "quiz_data" not in st.session_state:
        st.session_state.quiz_data = []
    if "current_question_index" not in st.session_state:
        st.session_state.current_question_index = 0
    if "score" not in st.session_state:
        st.session_state.score = 0
    if "completed_quiz" not in st.session_state:
        st.session_state.completed_quiz = False

    # Section Quiz
    st.header("Quiz")

    # Charger les sujets
    topics = db_manager.get_topics()

    if not topics:
        st.warning("Aucun sujet disponible. Veuillez ajouter des documents à la base de données.")
        return

    # Sélection des sujets
    selected_topics = st.multiselect("Choisissez un ou plusieurs sujets :", topics)

    if st.button("Commencer le quiz") and selected_topics:
        st.session_state.quiz_data = []
        st.session_state.current_question_index = 0
        st.session_state.score = 0
        st.session_state.completed_quiz = False

        # Générer les questions pour 10 tours de quiz
        for _ in range(10):
            topic = random.choice(selected_topics)
            quiz_data = rag.generate_quiz_question(topic)
            if quiz_data["correct_index"] != -1:
                st.session_state.quiz_data.append(quiz_data)

        if not st.session_state.quiz_data:
            st.error("Aucune question n'a pu être générée. Veuillez réessayer.")

    # Gestion du quiz
    if st.session_state.quiz_data and not st.session_state.completed_quiz:
        question_data = st.session_state.quiz_data[st.session_state.current_question_index]
        question = question_data["question"]
        options = question_data["options"]
        correct_index = question_data["correct_index"]

        st.markdown(f"### Question {st.session_state.current_question_index + 1} : {question}")

        # Affichage des options
        for i, option in enumerate(options):
            if st.button(option, key=f"option_{i}"):
                if i == correct_index:
                    st.success("Bonne réponse ! 🎉")
                    st.session_state.score += 1
                else:
                    st.error("Mauvaise réponse. 😔")

                if st.session_state.current_question_index + 1 < len(st.session_state.quiz_data):
                    st.session_state.current_question_index += 1
                else:
                    st.session_state.completed_quiz = True
                st.rerun()

        if st.button("Terminer le quiz"):
            st.session_state.completed_quiz = True

    # Récapitulatif du quiz
    if st.session_state.completed_quiz:
        st.header("Récapitulatif du Quiz")
        st.markdown(f"### Score final : {st.session_state.score} / {len(st.session_state.quiz_data)}")

        st.write("**Détails des questions :**")
        for i, question_data in enumerate(st.session_state.quiz_data):
            question = question_data["question"]
            correct_index = question_data["correct_index"]
            user_answer = ("Bonne réponse" if i < st.session_state.current_question_index and
                           st.session_state.quiz_data[i]["correct_index"] == correct_index
                           else "Mauvaise réponse")

            st.markdown(f"**Question {i + 1}** : {question}")
            st.markdown(f"\u2714 Réponse correcte : {question_data['options'][correct_index]}")
            st.markdown(f"\u2716 Votre réponse : {user_answer}")

    
    if not API_KEY:
        st.warning("Veuillez ajouter votre clé API Mistral dans le fichier `.env`. Redémarrez l'application après avoir ajouté la clé.")

if __name__ == '__main__':
    main()
