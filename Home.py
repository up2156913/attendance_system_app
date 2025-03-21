import streamlit as st
from auth import authenticator

st.set_page_config(page_title=' Attendance System ', page_icon=':bar_chart:', layout='wide', initial_sidebar_state='auto')

# Check authentication status
auth_status = authenticator.is_authenticated()

# If not authenticated, show login form
if not auth_status:
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