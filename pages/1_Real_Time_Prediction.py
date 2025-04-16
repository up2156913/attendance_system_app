import streamlit as st
from Home import face_rec
from streamlit_webrtc import webrtc_streamer
import av
import time
import cv2
import numpy as np
from live_detection_module import LivenessDetection

from check_authentication import check_auth

# Check authentication before proceeding
check_auth()

st.set_page_config(page_title='Predictions')
st.subheader('Real-Time Attendance System')

# Create a liveness detector instance
liveness_detector = LivenessDetection()

# Enable/disable liveness detection
enable_liveness = st.checkbox("Enable Liveness Detection", value=True, 
                              help="Detect if the person is physically present to prevent spoofing")

# Liveness detection sensitivity
if enable_liveness:
    liveness_threshold = st.slider(
        "Liveness Detection Sensitivity", 
        min_value=0.3, 
        max_value=0.8, 
        value=0.5, 
        step=0.1,
        help="Lower values are more permissive, higher values require stronger evidence of liveness"
    )
    
    with st.expander("Liveness Detection Information"):
        st.info("""
        **Liveness Detection** ensures that the system can verify if a real person is present, 
        rather than a photo or video recording. This prevents attendance spoofing.
        
        The system checks for:
        - Facial texture analysis (photos look different than real faces)
        - Movement detection (slight natural head movements)
        
        For best results:
        - Ensure good lighting
        - Make slight natural head movements
        - Maintain a normal distance from the camera
        """)

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

# Display area for attendance status
status_placeholder = st.empty()
liveness_status_placeholder = st.empty()

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
        
        # Ensure we have a valid frame
        if img is None or img.size == 0:
            print("Invalid frame received")
            return frame
        
        # Clone the image for processing
        display_img = img.copy()
        
        # Get face detection results
        face_results = face_rec.faceapp.get(img)
        
        # Process each detected face
        for res in face_results:
            try:
                # Get bbox coordinates
                x1, y1, x2, y2 = map(int, res['bbox'])
                
                # If liveness detection is enabled
                if enable_liveness:
                    # Get liveness status
                    is_live, confidence, status_message = liveness_detector.detect_liveness(
                        img, 
                        [x1, y1, x2, y2]
                    )
                    
                    # Draw liveness status on image
                    liveness_color = (0, 255, 0) if is_live else (0, 0, 255)
                    cv2.putText(
                        display_img,
                        status_message,
                        (x1, y1 - 35),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6,
                        liveness_color,
                        2
                    )
                    
                    # Only proceed with identification if face is live or confidence is above threshold
                    if not is_live and confidence < liveness_threshold:
                        # Draw red rectangle for non-live faces
                        cv2.rectangle(display_img, (x1, y1), (x2, y2), (0, 0, 255), 2)
                        continue  # Skip to next face
                
                # Get embeddings for face recognition
                embeddings = res['embedding']
                
                # Process the frame with face recognition
                result_tuple = face_rec.ml_search_algorithm(
                    redis_face_db,
                    'Facial_features',
                    test_vector=embeddings,
                    name_role=['Name', 'Role', 'Subject', 'Student_ID'],
                    thresh=0.5
                )
                
                # Handle different return value counts
                if len(result_tuple) == 5:  # New format with original_key
                    person_name, person_role, person_subject, person_id, original_key = result_tuple
                elif len(result_tuple) == 4:
                    person_name, person_role, person_subject, person_id = result_tuple
                    original_key = ''
                else:
                    print(f"Unexpected return format from ml_search_algorithm: {result_tuple}")
                    person_name = 'Unknown'
                    person_role = 'Unknown'
                    person_subject = 'Unknown'
                    person_id = ''
                    original_key = ''
                
                # Handle attendance for selected_subject
                attendance_subject = selected_subject if selected_subject else person_subject
                
                # Set color based on recognition result
                color = (0, 255, 0) if person_name != 'Unknown' else (0, 0, 255)
                
                # Draw rectangle and text
                cv2.rectangle(display_img, (x1, y1), (x2, y2), color, 2)
                
                # Add text with background - include student ID if available
                if person_id:
                    text = f"{person_name} (ID: {person_id})"
                else:
                    text = f"{person_name}"
                
                font = cv2.FONT_HERSHEY_SIMPLEX
                font_scale = 0.7
                thickness = 2
                
                # Get text size
                (text_width, text_height), _ = cv2.getTextSize(text, font, font_scale, thickness)
                
                # Draw background rectangle for text
                cv2.rectangle(
                    display_img, 
                    (x1, y1 - text_height - 10), 
                    (x1 + text_width, y1), 
                    color, 
                    -1
                )
                
                # Add text
                cv2.putText(
                    display_img, 
                    text,
                    (x1, y1 - 5), 
                    font,
                    font_scale,
                    (255, 255, 255),
                    thickness
                )
                
                # Add current time
                current_time = str(time.time())
                readable_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                cv2.putText(
                    display_img, 
                    readable_time,
                    (x1, y1 - 60), 
                    font,
                    font_scale,
                    (255, 255, 255),
                    thickness
                )
                
                # Only add to logs if person is recognized and (liveness check is disabled or passed)
                if person_name != 'Unknown':
                    # Save logs with subject and student ID info
                    realtimepred.logs['name'].append(person_name)
                    realtimepred.logs['role'].append(person_role)
                    realtimepred.logs['subject'].append(attendance_subject)
                    realtimepred.logs['student_id'].append(person_id)
                    realtimepred.logs['current_time'].append(readable_time)
                    realtimepred.logs['original_key'].append(original_key)
                
            except Exception as e:
                print(f"Error processing individual face: {e}")
                continue
        
        # Check if it's time to save logs
        timenow = time.time()
        difftime = timenow - setTime
        if difftime >= waitTime:
            realtimepred.saveLogs_redis()
            setTime = time.time()  # reset time
            print('Save Data to redis database')
            
            # Update status with recognized people
            if len(realtimepred.logs['name']) > 0:
                names = list(set([name for name in realtimepred.logs['name'] if name != 'Unknown']))
                if names:
                    status_placeholder.success(f"✅ Attendance recorded for: {', '.join(names)}")
        
        # Return the processed frame
        return av.VideoFrame.from_ndarray(display_img, format="bgr24")
        
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
    
    ### Liveness Detection:
    When enabled, liveness detection prevents attendance spoofing by verifying that a real person is present,
    not just a photo or video. For best results, maintain good lighting and make natural head movements.
    """)

# WebRTC streamer with improved UI
st.subheader("Start Webcam for Attendance")
webrtc_streamer(
    key="realtimePrediction", 
    video_frame_callback=video_frame_callback, 
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

# Display liveness detection status
if enable_liveness:
    st.success("✅ Liveness Detection is ENABLED - System will verify that real people are present")
else:
    st.warning("⚠️ Liveness Detection is DISABLED - System may be vulnerable to spoofing")