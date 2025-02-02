import streamlit as st
from src.metrics_database import RAGMetricsDatabase
# Function to handle user logout
def logout():
    st.session_state.authenticated = False
    st.session_state.username = ""
    st.success("You have been logged out.")
    st.rerun()


@st.dialog("About WikiLLM", width="large")
def project_description_dialog():
    st.subheader("About WikiLLM")
    st.write(
        "WikiLLM est un projet interactif alliant quiz et cours. "
        "Il vous permet de tester vos connaissances via des quiz générés par l'IA, "
        "d'approfondir vos apprentissages grâce à des cours interactifs et de bénéficier d'explications détaillées."
    )
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        
        with st.container(border=True):
            st.header("Quiz Interactif")
            st.write("Générez et passez des quiz pour tester vos connaissances dans divers domaines du programme de troisieme.")
        
        with st.container(border=True):
            st.header("Cours Interactifs")
            st.write("Accédez à des cours structurés et complets pour approfondir tout le programme de troisieme.")
    with col2:    
        with st.container(border=True):
            st.header("Explications et Indices")
            st.write("Après chaque question, visualisez des explications détaillées et utilisez des indices pour mieux comprendre les réponses.")
        
        with st.container(border=True):
            st.header("Suivi de Progression")
            st.write("Consultez des métriques détaillées et suivez votre progression grâce à des tableaux de bord et des statistiques.")
    
    with st.container(border=True):
        st.header("Administration et Analyse")
        st.write("Les administrateurs disposent d'outils avancés pour analyser les performances et optimiser le contenu pédagogique.")
    
    st.markdown("---")
    st.markdown(
        """
        WikiLLM a été réalisé par [Alexis GABRYSCH](https://github.com/AlexisGabrysch), [Antoine ORUEZABALA](https://github.com/AntoineORUEZABALA), [Lucile PERBET](https://github.com/lucilecpp) et [Alexis DARDELET](https://github.com/AlexisDardelet).  
        Voir le repo sur [GitHub](https://github.com/AlexisGabrysch/wikillm).
        """,
        unsafe_allow_html=True
    )

@st.dialog("Metrics Database")
def metrics_database_dialog():
    # Retrieve metrics from the database
    metrics_db = RAGMetricsDatabase()
    avg_metrics = metrics_db.get_average_metrics()
    """    return {
            "avg_latency": row[0],
            "price_input_total": row[1],
            "price_output_total": row[2],
            "price_total": row[3],
            "gwp_total": row[4],
            "energy_usage_total": row[5]
            
        }
"""
    st.subheader("Metrics Database")
    st.write(f"Average Latency: {round(avg_metrics['avg_latency'] , 2)} seconds")
    st.write(f"Total Price Input: {round(avg_metrics['price_input_total'], 2)} €")
    st.write(f"Total Price Output: {round(avg_metrics['price_output_total'], 2)} €")
    st.write(f"Total Price: {round(avg_metrics['price_total'], 2)} €")
    st.write(f"Total GWP: {round(avg_metrics['gwp_total'], 2)} kgCO2e")
    st.write(f"Total Energy Usage: {round(avg_metrics['energy_usage_total'], 2)} kWh")
    st.write("")
    st.write("Ces données sont calculées sur l'ensemble des métriques enregistrées dans la base de données.")
 




# Function to display the navigation bar with authentication controls
def Navbar():
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
    
    with st.sidebar:
        st.markdown("## Navigation")
        st.page_link('app.py', label='Accueil', icon='🏠')
        st.page_link('pages/admin.py', label='Admin', icon='🔒')

        st.markdown("---")  # Separator
        cols = st.columns(2)
        with cols[0]:
            if st.button("About WikiLLM"):
                project_description_dialog()
            
        with cols[1]:
            if st.button("Metrics Database"):
                metrics_database_dialog()
        st.markdown("---")  # Separator
        # Display user information and logout button if authenticated
        if st.session_state.get('authenticated'):
            st.write(f"**Logged in as:** {st.session_state.get('username')}")
            if st.button("Logout"):
                    logout()
            
        else:
            st.write("**Not logged in**")

 
