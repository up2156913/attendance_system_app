import streamlit as st
from Home import face_rec
from streamlit_webrtc import webrtc_streamer
import av
import time

from check_authentication import check_auth

# Check authentication before proceeding
check_auth()

st.set_page_config(page_title='Predictions')
st.subheader('Real-Time Attendance System')

# Create a dictionary of module codes for reference
module_codes = {
    'Distributed Systems': 'M30225',
    'Business Analytics': 'M26507',
    'Final Year Project': 'M24739',
    'COMP Tutorial Level 6': 'M22733',
    'Theoretical Computer Science': 'M21276',
    'Advanced Networks': 'M21279',
    'Artificial Intelligence': 'M33174',
    'Complex Problem Solving': 'M33132',
    'Graphics and Computer Vision': 'M30242',
    'Practical Data Analytics and Mining': 'M25764',
    'Project Management': 'M30245',
    'Digital Enterprise and Innovation': 'M33173',
    'Internet of Things': 'M30226',
    'IT and Internetworking Security': 'M33141',
    'Robotics': 'M30241'
}

# Updated subject options based on final year modules
subject_options = [
    'Distributed Systems',
    'Business Analytics',
    'Final Year Project',
    'COMP Tutorial Level 6',
    'Theoretical Computer Science',
    'Advanced Networks',
    'Artificial Intelligence',
    'Complex Problem Solving',
    'Graphics and Computer Vision',
    'Practical Data Analytics and Mining',
    'Project Management',
    'Digital Enterprise and Innovation',
    'Internet of Things',
    'IT and Internetworking Security',
    'Robotics'
]

selected_subject = st.selectbox(
    "Select Subject for Attendance",
    options=subject_options
)

# Display module code for the selected subject
st.info(f"Module Code: {module_codes.get(selected_subject, 'N/A')}")

# Retrive data from the database
with st.spinner('Retrieving data from the database...'):
    redis_face_db = face_rec.retrive_data(name='academy:register')
    
    # Filter to show only relevant students (optional)
    if not redis_face_db.empty:
        try:
            filtered_db = redis_face_db[redis_face_db['Subject'] == selected_subject]
            if len(filtered_db) > 0:
                st.subheader(f"Students Enrolled in {selected_subject}")
                st.dataframe(filtered_db[['Name', 'Student_ID', 'Role']])
            else:
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
                                          'Facial_features', selected_subject, ['Name', 'Role', 'Subject', 'Student_ID'],
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


# Add a container for additional information
with st.expander("Attendance Information", expanded=True):
    st.write("""
    ### How attendance works:
    1. Select the subject you are taking attendance for
    2. The system will show all students enrolled in this subject
    3. Start the webcam by clicking the 'START' button below
    4. The system will recognize students' faces and mark attendance automatically
    5. Attendance is saved every 30 seconds to the database
    """)
    

# WebRTC streamer with improved UI
st.subheader("Start Webcam for Attendance")
webrtc_streamer(key="realtimePrediction", video_frame_callback=video_frame_callback, 
                frontend_rtc_configuration={
                    "iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]
                },
                server_rtc_configuration={
                    "iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]
                },
                media_stream_constraints={"video": True, "audio": False},
                async_processing=True
                )

# Add a note about attendance logs
st.info("💡 Attendance logs are saved automatically and can be viewed in the Reports page.")