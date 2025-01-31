import streamlit as st

# Function to handle user logout
def logout():
    st.session_state.authenticated = False
    st.session_state.username = ""
    st.success("You have been logged out.")
    st.rerun()

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

        # Display user information and logout button if authenticated
        if st.session_state.get('authenticated'):
            st.write(f"**Logged in as:** {st.session_state.get('username')}")
            if st.button("Logout"):
                logout()
        else:
            st.write("**Not logged in**")

 
