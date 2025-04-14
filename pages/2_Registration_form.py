import streamlit as st
from Home import face_rec
import cv2
import numpy as np
from streamlit_webrtc import webrtc_streamer
import av
from check_authentication import check_auth
import redis

# Initialize session state variables for unenrollment process
if 'show_confirmation' not in st.session_state:
    st.session_state['show_confirmation'] = False
if 'selected_user_key' not in st.session_state:
    st.session_state['selected_user_key'] = None
if 'selected_user_display' not in st.session_state:
    st.session_state['selected_user_display'] = None

# Check authentication before proceeding
check_auth()

st.set_page_config(page_title='Registration Management')

# Create tabs for registration and unenrollment
tab1, tab2 = st.tabs(["Register Users", "Unenroll Users"])

with tab1:
    st.subheader('Registration Form')

    ## init registration form
    registration_form = face_rec.RegistrationForm()

    # step-2: Collect facial embedding of that person
    def video_callback_func(frame):
        img = frame.to_ndarray(format='bgr24') # 3d array bgr
        reg_img, embedding = registration_form.get_embedding(img)
        # two step process
        # 1st step save data into local computer txt
        if embedding is not None:
            with open('face_embedding.txt',mode='ab') as f:
                np.savetxt(f,embedding)
        
        return av.VideoFrame.from_ndarray(reg_img,format='bgr24')


    ####### Registration Form ##########
    with st.container(border=True):
        name = st.text_input(label='Name',placeholder='Enter First name and Last name')
        role = st.selectbox(label='Role', placeholder='Select Role', options=('--select--',
                                                                            'Student', 'Teacher'))
        subject = st.selectbox(label='Subject Enrollment', options=('--select--', 
                                                        'Distributed Systems', 
                                                        'Business Analytics'))

        st.write('Click on Start button to collect your face samples')
        with st.expander('Instructions'):
            st.caption('1. Give different expression to capture your face details.')
            st.caption('2. Click on stop after getting 200 samples.')

        webrtc_streamer(key='registration', video_frame_callback=video_callback_func, 
                        frontend_rtc_configuration={
                        "iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]
                    },
                    server_rtc_configuration={
                        "iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]
                    }
                    )

    if st.button('Submit'):
        if role == '--select--' or subject == '--select--':
            st.error("Please select both Role and Subject")
        else:
            return_val = registration_form.save_data_in_redis_db(name, role, subject)
            if return_val == True:
                st.success("Registration completed successfully!")
            elif return_val == 'name_false':
                st.error("Please enter a valid name")
            elif return_val == 'file_false':
                st.error("No facial embeddings captured. Please try again.")

with tab2:
    st.subheader('Unenroll Users')
    
    # Connect to Redis Client
    hostname = 'redis-19487.c8.us-east-1-4.ec2.redns.redis-cloud.com'
    portnumber = 19487
    password = 'ee3x3qAQ7yPMws3P5vHquvbE8o6LY84d'
    
    r = redis.StrictRedis(host=hostname,
                         port=portnumber,
                         password=password)
    
    # Retrieve all registered users
    with st.spinner('Loading registered users...'):
        # Get all keys from register
        all_keys = r.hkeys('academy:register')
        
        # Convert bytes to strings
        registered_users = [key.decode('utf-8') for key in all_keys]
        
        # Create a more readable display format for selection
        display_users = []
        for user in registered_users:
            parts = user.split('@')
            if len(parts) == 3:
                display_users.append(f"{parts[0]} ({parts[1]}) - {parts[2]}")
            elif len(parts) == 2:
                display_users.append(f"{parts[0]} ({parts[1]})")
            else:
                display_users.append(user)
    
    if not registered_users:
        st.info("No registered users found in the system.")
    else:
        st.write("Select a user to unenroll from the system:")
        
        # Create a selectbox with the display names
        selected_display = st.selectbox("Select User", options=display_users)
        
        # Get the corresponding key for the selected display name
        selected_index = display_users.index(selected_display)
        selected_key = registered_users[selected_index]
        
        # Create a unique key for the "Unenroll User" button
        if st.button("Unenroll User", key="unenroll_button"):
            # Store the selected user in session state to preserve it
            st.session_state['selected_user_key'] = selected_key
            st.session_state['selected_user_display'] = selected_display
            st.session_state['show_confirmation'] = True
        
        # If confirmation dialog should be shown
        if st.session_state.get('show_confirmation', False):
            # Show confirmation dialog
            st.warning(f"Are you sure you want to unenroll {st.session_state['selected_user_display']}? This action cannot be undone.")
            
            # Create two columns for confirm/cancel buttons
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Confirm Unenrollment", key="confirm_button"):
                    try:
                        # Delete the user from Redis using the stored key
                        r.hdel('academy:register', st.session_state['selected_user_key'])
                        st.success(f"Successfully unenrolled {st.session_state['selected_user_display']} from the system.")
                        
                        # Reset the confirmation state
                        st.session_state['show_confirmation'] = False
                        del st.session_state['selected_user_key']
                        del st.session_state['selected_user_display']
                        
                        # Refresh the page to update the user list
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error occurred during unenrollment: {e}")
            with col2:
                if st.button("Cancel", key="cancel_button"):
                    # Reset the confirmation state
                    st.session_state['show_confirmation'] = False
                    del st.session_state['selected_user_key']
                    del st.session_state['selected_user_display']
                    st.rerun()