import streamlit as st
# Fonction pour afficher la barre de navigation
def Navbar():
    with st.sidebar:
        st.page_link('app.py', label='Accueil', icon='🏠')
        st.page_link('pages/admin.py', label='Admin', icon='🔒')
        st.page_link('pages/map.py', label='Map Game', icon='🌍')