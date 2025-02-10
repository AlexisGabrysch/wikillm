import streamlit as st
from app.pages.ressources.components import Navbar , display_brevet_blanc
from app.src.rag import RAGPipeline
from app.src.db.utils import QuizDatabase


rag = RAGPipeline(
        generation_model="mistral-large-latest",
        max_tokens=900,
        temperature=0.5,
        top_n=1,
    )
db_manager = QuizDatabase()
def main():
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
    
    Navbar()

    # Assurez-vous que l'utilisateur est authentifié
    if not st.session_state.get('authenticated'):
        st.warning("You must be logged in to access the admin dashboard.")
        return

    display_brevet_blanc(rag, db_manager)
    
    
if __name__ == "__main__":
    main()