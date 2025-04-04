import streamlit as st
from Home import face_rec
from streamlit_webrtc import webrtc_streamer
import av
import time

from check_authentication import check_auth

# Check authentication before proceeding
check_auth()

#from auth import authenticator


st.set_page_config(page_title='Predictions')
st.subheader('Real-Time Attendance System')

selected_subject = st.selectbox(
    "Select Subject for Attendance",
    options=["Distributed Systems", "Business Analytics"]
)



# Retrive data from the database
with st.spinner('Retrieving data from the database...'):
    redis_face_db = face_rec.retrive_data(name='academy:register')
    
    # Filter to show only relevant students (optional)
    if not redis_face_db.empty:
        try:
            filtered_db = redis_face_db[redis_face_db['Subject'] == selected_subject]
            if len(filtered_db) > 0:
                st.dataframe(filtered_db)
            else:
                st.dataframe(redis_face_db)
                st.info(f"No students enrolled in {selected_subject} yet.")
        except Exception as e:
            st.error(f"Error filtering data: {e}")
            st.dataframe(redis_face_db)
    else:
        st.info("No registered users found in the database.")


#time
waitTime = 30 # seconds
setTime = time.time()
realtimepred = face_rec.RealTimePred() 


#Real time prediction


#streamlit webrtc

# callback function
# callback function
def video_frame_callback(frame):
    try:
        global setTime

        img = frame.to_ndarray(format="bgr24")
        print(f"Input frame shape: {img.shape}")
        
        # Ensure we have a valid frame
        if img is None or img.size == 0:
            print("Invalid frame received")
            return frame
        
        # Process the frame
        pred_img = realtimepred.face_prediction(img, redis_face_db,
                                          'Facial_features', selected_subject, ['Name', 'Role', 'Subject'],
                                          thresh=0.5)
        
        timenow = time.time()
        difftime = timenow - setTime
        if difftime >= waitTime:
            realtimepred.saveLogs_redis()
            setTime = time.time() # reset time        
            print('Save Data to redis database')
        
        # Ensure we got a valid processed frame back
        if pred_img is None or pred_img.size == 0:
            print("Invalid processed frame")
            return frame
            
        print(f"Output frame shape: {pred_img.shape}")
        return av.VideoFrame.from_ndarray(pred_img, format="bgr24")
        
    except Exception as e:
        print(f"Error in video frame callback: {e}")
        return frame



webrtc_streamer(key="realtimePrediction", video_frame_callback=video_frame_callback, 
                frontend_rtc_configuration={
                    "iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]
                },
                server_rtc_configuration={
                    "iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]
                }
                )
