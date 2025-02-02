import streamlit as st
from pages.ressources.components import Navbar , display_brevet_blanc
from src.rag import RAGPipeline
from src.db.utils import QuizDatabase


rag = RAGPipeline(
        generation_model="mistral-large-latest",
        max_tokens=900,
        temperature=0.5,
        top_n=1,
    )
db_manager = QuizDatabase()
def main():
    Navbar()

    # Assurez-vous que l'utilisateur est authentifié
    if not st.session_state.get('authenticated'):
        st.warning("You must be logged in to access the admin dashboard.")
        return

    display_brevet_blanc(rag, db_manager)
    
    
if __name__ == "__main__":
    main()