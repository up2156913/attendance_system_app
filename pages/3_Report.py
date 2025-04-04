import pandas as pd
import streamlit as st
from Home import face_rec
import datetime
from check_authentication import check_auth

# Check authentication before proceeding
check_auth()

st.set_page_config(page_title='Reporting', layout='wide')

st.subheader('Reporting')


# Retrive logs data and show in Report.py
# extract data from redis list
name = 'attendance:logs'
def load_logs(name,end=-1):
    logs_list = face_rec.r.lrange(name,start=0,end=end) # extract all data from the redis database
    return logs_list

# tabs to show the info
tab1, tab2, tab3  = st.tabs(['Registered Data','Logs', 'Attendance Report'])

with tab1:
    if st.button('Refresh Data'):
        # Retrive the data from Redis Database
        with st.spinner('Retriving Data from Redis DB ...'):    
            redis_face_db = face_rec.retrive_data(name='academy:register')

            ds_students = redis_face_db[redis_face_db['Subject'] == 'Distributed Systems']
            ba_students = redis_face_db[redis_face_db['Subject'] == 'Business Analytics']
            
            st.subheader("Distributed Systems Enrolled Students")
            st.dataframe(ds_students[['Name', 'Role']])
            
            st.subheader("Business Analytics Enrolled Students")
            st.dataframe(ba_students[['Name', 'Role']])

with tab2:
    if st.button('Refresh Logs'):
        st.write(load_logs(name=name))# display the logs data in the report.py


with tab3:
    st.subheader('Attendance Report')
    
    # Subject selection for attendance report
    selected_subject = st.selectbox(
        "Select Subject",
        options=["Distributed Systems", "Business Analytics"]
    )
    
    # Load logs and process
    logs_list = load_logs(name='attendance:logs')
    
    # Convert bytes to string
    logs_list_string = [log.decode('utf-8') for log in logs_list]
    
    # Split string by @ and create nested list
    logs_nested_list = [log.split('@') for log in logs_list_string]
    
    # Convert to dataframe - adjusted for 4 fields instead of 3
    if len(logs_nested_list) > 0 and len(logs_nested_list[0]) == 3: 
        logs_df = pd.DataFrame(logs_nested_list, columns=['Name', 'Role', 'Timestamp'])
        logs_df['Subject'] = 'Not Enrolled'
    elif len(logs_nested_list) > 0 and len(logs_nested_list[0]) == 4: 
        logs_df = pd.DataFrame(logs_nested_list, columns=['Name', 'Role', 'Subject', 'Timestamp'])
    else:
        logs_df = pd.DataFrame(columns=['Name', 'Role', 'Subject', 'Timestamp'])
    
    # Filter for selected subject
    subject_logs = logs_df[logs_df['Subject'] == selected_subject]
    
    # Process timestamps
    subject_logs['Timestamp'] = subject_logs['Timestamp'].apply(lambda x: x.split('.')[0])
    subject_logs['Timestamp'] = pd.to_datetime(subject_logs['Timestamp'])
    subject_logs['Date'] = subject_logs['Timestamp'].dt.date
    
    # Create pivoted table with students as rows and dates as columns
    pivot_table = subject_logs.pivot_table(
        index='Name',
        columns='Date',
        values='Timestamp',
        aggfunc='count'
    ).fillna(0)
    
    # Convert to present/absent format
    def format_attendance(value):
        if value > 0:
            return "Present ✅"
        else:
            return "Absent ❌"
    
    formatted_table = pivot_table.applymap(format_attendance)
    
    # Display the table
    st.write(f"Attendance Report for {selected_subject}")
    st.table(formatted_table)