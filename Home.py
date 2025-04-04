import streamlit as st
from auth import authenticator

st.set_page_config(page_title=' Attendance System ', page_icon=':bar_chart:', layout='wide', initial_sidebar_state='auto')

# Make sure authentication state is initialized
authenticator.initialize_auth_state()

# Check authentication status
if not st.session_state['authentication_status']:
    st.title('Smart Attendance System Login')
    authenticator.login('Login', 'main')
    authenticator.show_login_message()
    st.stop()  # Stop execution if not authenticated
else:
    # Show logout button in sidebar if authenticated
    with st.sidebar:
        st.write(f"Welcome, {st.session_state['name']}")
        authenticator.logout()

    # Main content - only shown if authenticated
    st.header('Smart Attendance System with Face Recognition')

    with st.spinner("Loading Models and Connecting to Redis db ..."):
        import face_rec

    st.success('Model loaded successfully')
    st.success('Redis db connected successfully')