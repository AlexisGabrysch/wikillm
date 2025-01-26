# FILE: app.py
import streamlit as st
from pages.ressources.components import Navbar
from src.database import DatabaseManager
from src.rag import RAGPipeline
from src.ml_model import classify_answer
import os
from dotenv import load_dotenv, find_dotenv
import asyncio

st.set_page_config(page_title="WikiLLM", page_icon="📚", layout="wide")

# Load environment variables
load_dotenv(find_dotenv())
API_KEY = os.getenv("MISTRAL_API_KEY")

# Initialize the DatabaseManager
db_manager = DatabaseManager(db_path="./chromadb_data")

# Initialize the RAGPipeline instance
rag = RAGPipeline(
    generation_model="ministral-8b-latest",
    role_prompt="Tu es un assistant pédagogique pour le programme de collège français.",
    db_path="./chromadb_data",
    max_tokens=300,  # Augmenter le nombre de tokens si nécessaire pour l'explication
    temperature=0.5,
    top_n=2,
)


def main():
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
        if "score" not in st.session_state:
            st.session_state["score"] = 0.0
        if "hints_requested" not in st.session_state:
            st.session_state["hints_requested"] = 0
        if "current_question" not in st.session_state:
            st.session_state["current_question"] = None
        if "user_answer" not in st.session_state:
            st.session_state["user_answer"] = None

        # Charger les sujets
        topics = db_manager.get_topics()

        # Vérifier si des sujets sont disponibles
        if not topics:
            st.warning("Aucun sujet disponible. Veuillez ajouter des documents à la base de données.")
            return

        # Sélection du sujet
        selected_topic = st.selectbox("Choisissez un sujet :", topics)

        # Générer une question de quiz
        if st.button("Générer une question"):
            st.session_state["total_questions"] += 1
            quiz_data = asyncio.run(rag.generate_quiz_question_async(selected_topic))
           

            if quiz_data["correct_index"] == -1:
                st.error(quiz_data["question"])
            else:
                st.session_state["current_question"] = quiz_data
                st.session_state["user_answer"] = None  # Réinitialiser la réponse de l'utilisateur

        # Afficher la question actuelle et les options
        if st.session_state["current_question"]:
            question = st.session_state["current_question"]["question"]
            options = st.session_state["current_question"]["options"]
            correct_index = st.session_state["current_question"]["correct_index"]
            explanation = st.session_state["current_question"].get("explanation", "")
            context = rag.fetch_context_by_topic_cached(selected_topic)  # Utiliser la version cachée

            st.markdown(f"### Question:\n{question}")

            with st.form(key='answer_form'):
                selected_option = st.radio("Choisissez une réponse :", options, key='quiz_options')
                indice_clicked = st.form_submit_button("💡 Indice")
                validate_clicked = st.form_submit_button("Valider la réponse")

            if indice_clicked:
                hint = rag.generate_hint(question=question, context=context)
                st.session_state["hints_requested"] += 1
                st.session_state["score"] -= 0.5  # Déduction de 0.5 points
                st.info(f"**Indice:** {hint}")

            if validate_clicked:
                try:
                    selected_index = options.index(selected_option)
                except ValueError:
                    st.error("Veuillez sélectionner une option valide.")
                    selected_index = -1

                st.session_state["user_answer"] = selected_index

                if selected_index == correct_index:
                    st.session_state["correct_answers"] += 1
                    st.session_state["score"] += 1  # Ajouter 1 point pour une bonne réponse
                    st.success("✅ Bonne réponse!")
                else:
                    st.error("❌ Mauvaise réponse.")

                st.markdown(f"**La bonne réponse était:** {correct_index + 1}. {options[correct_index]}")

                with st.expander("📖 Explication"):
                    st.write(explanation)

                # Statistiques de performance
                st.sidebar.markdown(
                    f"""
                    ### 📊 Statistiques
                    - Questions répondues : {st.session_state['total_questions']}
                    - Réponses correctes : {st.session_state['correct_answers']}
                    - Indices utilisés : {st.session_state['hints_requested']}
                    - Score total : {st.session_state['score']}
                    """
                )

                # Option pour passer à la prochaine question après validation
                if st.button("Prochaine question", key="next_question_button"):
                    st.session_state["current_question"] = None
                    st.session_state["user_answer"] = None
                    st.experimental_rerun()

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

        if st.button("Envoyer") and user_input:
            # Ajouter le message de l'utilisateur à l'historique
            st.session_state["chat_history"].append({"role": "user", "content": user_input})

            # Préparer l'historique pour le pipeline RAG
            history = st.session_state["chat_history"]

            # Générer une réponse de l'IA
            response = rag(query=user_input, history=history)
            ai_response = response if isinstance(response, str) else "Je n'ai pas compris votre demande."

            st.session_state["chat_history"].append({"role": "assistant", "content": ai_response})

            # Rafraîchir la page pour afficher les nouveaux messages
            st.rerun()

    # Vérification de la présence de la clé API Mistral
    if not API_KEY:
        if 'mistral_api_warning' not in st.session_state:
            st.warning("Vous n'avez pas ajouté votre clé API Mistral dans le fichier `.env`. Veuillez ajouter le fichier `.env` à la racine du projet puis redémarrer l'application.")
            st.session_state['mistral_api_warning'] = True

    if "current_question" not in st.session_state and not st.session_state.get("chat_history"):
        st.title("Bienvenue sur WikiLLM !")


if __name__ == '__main__':
    main()