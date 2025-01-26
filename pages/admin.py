import streamlit as st
from pages.ressources.components import Navbar
# Configuration de la page
set_page_config = st.set_page_config(page_title="WikiLLM - Admin", page_icon="🔒", layout="wide")



def main():
    # Barre de navigation
    
    Navbar()
    st.title("Administration")
    st.write("Bienvenue sur la page d'administration de l'application WikiLLM.")
    

if __name__ == '__main__':
    main()
    