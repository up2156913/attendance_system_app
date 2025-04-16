import pandas as pd
import streamlit as st
from Home import face_rec
import datetime
from check_authentication import check_auth

# Check authentication before proceeding
check_auth()

st.set_page_config(page_title='Reporting', layout='wide')

st.subheader('Attendance Reporting System')

# Dictionary of module codes for reference
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

# Retrieve logs data and show in Report.py
# extract data from redis list
def load_logs(name, end=-1):
    try:
        logs_list = face_rec.r.lrange(name, start=0, end=end)  # extract all data from the redis database
        return logs_list
    except Exception as e:
        st.error(f"Error loading logs: {e}")
        return []


# tabs to show the info
tab1, tab2, tab3 = st.tabs(['Registered Data', 'Attendance Logs', 'Attendance Report'])

with tab1:
    if st.button('Refresh Data'):
        # Retrieve the data from Redis Database
        with st.spinner('Retrieving Data from Redis DB...'):
            try:
                redis_face_db = face_rec.retrive_data(name='academy:register')
                
                # Create a selectbox for filtering by subject
                selected_subject_filter = st.selectbox(
                    "Filter by Subject",
                    options=["All Subjects"] + subject_options
                )
                
                if selected_subject_filter == "All Subjects":
                    # Show all students, grouped by subject
                    st.subheader("All Registered Students")
                    
                    # Group by subject and display each group
                    for subject in subject_options:
                        subject_students = redis_face_db[redis_face_db['Subject'] == subject]
                        if not subject_students.empty:
                            st.write(f"**{subject}** (Module Code: {module_codes.get(subject, 'N/A')})")
                            # Include Student ID in the display
                            st.dataframe(subject_students[['Name', 'Student_ID', 'Role']])
                else:
                    # Show students for a specific subject
                    subject_students = redis_face_db[redis_face_db['Subject'] == selected_subject_filter]
                    if not subject_students.empty:
                        st.subheader(f"Students Enrolled in {selected_subject_filter}")
                        st.write(f"Module Code: {module_codes.get(selected_subject_filter, 'N/A')}")
                        # Include Student ID in the display
                        st.dataframe(subject_students[['Name', 'Student_ID', 'Role']])
                    else:
                        st.info(f"No students enrolled in {selected_subject_filter} yet.")
            except Exception as e:
                st.error(f"Error retrieving or displaying data: {e}")
                import traceback
                st.code(traceback.format_exc())

with tab2:
    st.subheader("Raw Attendance Logs")
    if st.button('Refresh Logs'):
        try:
            logs_list = load_logs(name='attendance:logs')
            
            # Convert bytes to string
            logs_list_string = [log.decode('utf-8') for log in logs_list]
            
            # Create a DataFrame for better display
            logs_nested_list = []
            
            for log in logs_list_string:
                # Split the log safely
                parts = log.split('@')
                # Process based on the number of parts
                if len(parts) == 3:  # Old format: name@role@timestamp
                    logs_nested_list.append([parts[0], parts[1], 'Not Enrolled', '', parts[2]])
                elif len(parts) == 4:  # Format: name@role@subject@timestamp
                    logs_nested_list.append([parts[0], parts[1], parts[2], '', parts[3]])
                elif len(parts) == 5:  # New format with ID: name@role@subject@id@timestamp
                    logs_nested_list.append([parts[0], parts[1], parts[2], parts[3], parts[4]])
                else:
                    st.warning(f"Unexpected log format: {log}")
                    continue
            
            # Create DataFrame with explicit column names
            if logs_nested_list:
                logs_df = pd.DataFrame(logs_nested_list, columns=['Name', 'Role', 'Subject', 'Student_ID', 'Timestamp'])

                # Add some formatting for better readability
                # Use a more flexible date parser that can handle both formats
                try:
                    # First try to convert timestamps with a more permissive parser
                    logs_df['Timestamp'] = pd.to_datetime(logs_df['Timestamp'], errors='coerce')
                    
                    # Check for any NaT (not a time) values which indicate parsing failures
                    if logs_df['Timestamp'].isna().any():
                        st.warning("Some timestamps could not be parsed correctly.")
                    
                    # Sort by timestamp
                    logs_df = logs_df.sort_values(by='Timestamp', ascending=False)
                    
                    # Add module code column if available
                    logs_df['Module Code'] = logs_df['Subject'].map(lambda x: module_codes.get(x, ''))
                    
                    st.dataframe(logs_df)
                except Exception as e:
                    # If conversion fails, just display the raw data
                    st.error(f"Error formatting timestamps: {e}")
                    logs_df['Module Code'] = logs_df['Subject'].map(lambda x: module_codes.get(x, ''))
                    st.dataframe(logs_df)
                
            else:
                st.info("No attendance logs found.")
                
        except Exception as e:
            st.error(f"Error processing logs: {e}")
            import traceback
            st.code(traceback.format_exc())


with tab3:
    st.subheader('Attendance Report')
    
    # Subject selection for attendance report
    selected_subject = st.selectbox(
        "Select Subject",
        options=subject_options
    )
    
    # Show module code
    st.write(f"Module Code: {module_codes.get(selected_subject, 'N/A')}")
    
    # Date range selection
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("From Date", datetime.date.today() - datetime.timedelta(days=30))
    with col2:
        end_date = st.date_input("To Date", datetime.date.today())
    
    if start_date > end_date:
        st.error("Error: End date must be after start date")
    else:
        try:
            # Load logs and process
            logs_list = load_logs(name='attendance:logs')
            
            # Convert bytes to string
            logs_list_string = [log.decode('utf-8') for log in logs_list]
            
            # Process logs with safe parsing
            logs_nested_list = []

            for log in logs_list_string:
                    # Split the log safely
                    parts = log.split('@')
                    # Process based on the number of parts
                    if len(parts) == 3:  # Old format: name@role@timestamp
                        logs_nested_list.append([parts[0], parts[1], 'Not Enrolled', '', parts[2]])
                    elif len(parts) == 4:  # Format: name@role@subject@timestamp
                        logs_nested_list.append([parts[0], parts[1], parts[2], '', parts[3]])
                    elif len(parts) == 5:  # New format with ID: name@role@subject@id@timestamp
                        logs_nested_list.append([parts[0], parts[1], parts[2], parts[3], parts[4]])
                    else:
                        continue  # Skip invalid formats
            
            if logs_nested_list:
                logs_df = pd.DataFrame(logs_nested_list, columns=['Name', 'Role', 'Subject', 'Student_ID', 'Timestamp'])
                
                # Filter for selected subject
                subject_logs = logs_df[logs_df['Subject'] == selected_subject]
                
                if not subject_logs.empty:
                    # Process timestamps
                    subject_logs['Timestamp'] = pd.to_datetime(subject_logs['Timestamp'], errors= 'coerce')
                    # Drop rows where timestamp parsing failed
                    subject_logs = subject_logs.dropna(subset=['Timestamp'])
                    # Continue only if we still have valid data
                    if not subject_logs.empty:
                        subject_logs['Date'] = subject_logs['Timestamp'].dt.date
                        
                        # Filter by date range
                        subject_logs = subject_logs[
                            (subject_logs['Date'] >= start_date) & 
                            (subject_logs['Date'] <= end_date)
                        ]
                    
                        if not subject_logs.empty:
                            # Add ID to the name for the pivot table if available
                            subject_logs['Name_with_ID'] = subject_logs.apply(
                                lambda row: f"{row['Name']} (ID: {row['Student_ID']})" if row['Student_ID'] and str(row['Student_ID']).strip() != '' else row['Name'], 
                                axis=1
                            )
                            
                            # Create pivoted table with students as rows and dates as columns
                            pivot_table = subject_logs.pivot_table(
                                index=['Name_with_ID'],
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
                            
                            # Calculate and add attendance statistics
                            attendance_count = pivot_table.applymap(lambda x: 1 if x > 0 else 0).sum(axis=1)
                            total_days = pivot_table.shape[1]
                            attendance_percentage = (attendance_count / total_days * 100).round(1)
                            
                            formatted_table['Attendance Days'] = attendance_count
                            formatted_table['Total Days'] = total_days
                            formatted_table['Percentage'] = attendance_percentage.apply(lambda x: f"{x}%")
                            
                            # Display the table
                            st.write(f"### Attendance Report for {selected_subject}")
                            st.write(f"Period: {start_date} to {end_date}")
                            st.table(formatted_table)
                        
                            # Create a detailed table with student IDs
                            st.write("### Detailed Attendance Data")
                            detailed_data = subject_logs.groupby(['Name', 'Student_ID']).agg({
                                'Date': 'nunique',
                                'Timestamp': 'count'
                            }).reset_index()
                            
                            detailed_data.columns = ['Name', 'Student ID', 'Days Present', 'Total Check-ins']
                            detailed_data['Attendance Rate'] = (detailed_data['Days Present'] / total_days * 100).round(1)
                            detailed_data['Attendance Rate'] = detailed_data['Attendance Rate'].apply(lambda x: f"{x}%")
                            
                            st.dataframe(detailed_data)
                            
                            # Add download button for CSV
                            csv = formatted_table.to_csv().encode('utf-8')
                            st.download_button(
                                label="Download Report as CSV",
                                data=csv,
                                file_name=f"{selected_subject}_attendance_{start_date}_to_{end_date}.csv",
                                mime="text/csv",
                            )
                            
                            # Add download button for detailed CSV
                            detailed_csv = detailed_data.to_csv().encode('utf-8')
                            st.download_button(
                                label="Download Detailed Report as CSV",
                                data=detailed_csv,
                                file_name=f"{selected_subject}_detailed_attendance_{start_date}_to_{end_date}.csv",
                                mime="text/csv",
                            )
                        else:
                            st.info(f"No attendance records found for {selected_subject} in the selected date range.")
                    else:
                        st.info(f"No valid attendance records found for {selected_subject}.")
                else:
                    st.warning("Failed to parse timestamps for this subject's attendance data.")
            else:
                st.info("No attendance logs found in the database.")
        except Exception as e:
            st.error(f"Error processing attendance logs: {e}")
            import traceback
            st.code(traceback.format_exc())
