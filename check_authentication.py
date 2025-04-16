import streamlit as st
from auth import authenticator

def check_auth():
    """
    Check if user is authenticated and redirect to login if not.
    Returns True if authenticated, False otherwise.
    """
    # Initialize authentication state
    authenticator.initialize_auth_state()
    
    # Check if user is authenticated
    if not st.session_state.get('authentication_status'):
        st.error("Please login to access this page")
        st.info("Redirecting to login page...")
        # Add a button to redirect to home
        if st.button("Go to Login Page"):
            st.switch_page("Home.py")
        
        st.stop()
        return False
    return True