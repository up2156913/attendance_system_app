import streamlit as st
from Home import face_rec
import cv2
import numpy as np
from streamlit_webrtc import webrtc_streamer
import av
from check_authentication import check_auth

# Check authentication before proceeding
check_auth()

#from auth import authenticator


st.set_page_config(page_title='Registration Form')
st.subheader('Registration Form')


## init registration form
registration_form = face_rec.RegistrationForm()

# Step-1: Collect person name and role
# form
#person_name = st.text_input(label='Name',placeholder='First & Last Name')
#role = st.selectbox(label='Select your Role',options=('Student',
#                                                      'Teacher'))




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




#webrtc_streamer(key='registration',video_frame_callback=video_callback_func)




# step-3: save the data in redis database


if st.button('Submit'):
    if role == '--select--' or subject == '--select--':
        st.error("Please select both Role and Subject")
    else:
        return_val = registration_form.save_data_in_redis_db(name, role, subject)

#else:
#        authenticator.login('Login', 'main') 


