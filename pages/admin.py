import streamlit as st
from auth import authenticator
import yaml
from yaml.loader import SafeLoader
import os
from check_authentication import check_auth

st.set_page_config(page_title='Admin Portal', layout='wide')

check_auth()

# Authentication is handled in Home.py
# Check if user is admin
if st.session_state.get('username') != 'admin':
    st.error("You need admin privileges to access this page.")
    st.stop()

st.title('Admin Portal')
st.subheader('User Management')

# Load current users
with open('config.yaml', 'r') as file:
    config = yaml.load(file, Loader=SafeLoader)

# Display current users
st.subheader("Current Users")

user_data = []
for username, details in config['credentials']['usernames'].items():
    user_data.append({
        "Username": username,
        "Name": details['name'],
        "Email": details['email']
    })

st.table(user_data)

# Add new user form
st.subheader("Add New User")

with st.form("add_user_form"):
    new_username = st.text_input("Username")
    new_name = st.text_input("Full Name")
    new_email = st.text_input("Email")
    new_password = st.text_input("Password", type="password")
    confirm_password = st.text_input("Confirm Password", type="password")
    
    submitted = st.form_submit_button("Add User")
    
    if submitted:
        if not new_username or not new_name or not new_email or not new_password:
            st.error("All fields are required")
        elif new_password != confirm_password:
            st.error("Passwords do not match")
        elif new_username in config['credentials']['usernames']:
            st.error(f"Username '{new_username}' already exists")
        else:
            success, message = authenticator.register_user(
                new_username, 
                new_name, 
                new_email, 
                new_password
            )
            
            if success:
                st.success(message)
                st.rerun()
            else:
                st.error(message)

# Delete user
st.subheader("Delete User")

with st.form("delete_user_form"):
    username_to_delete = st.selectbox(
        "Select User to Delete",
        options=[user for user in config['credentials']['usernames'].keys() if user != 'admin']
    )
    
    delete_submitted = st.form_submit_button("Delete User")
    
    if delete_submitted and username_to_delete:
        # Cannot delete admin
        if username_to_delete == 'admin':
            st.error("Cannot delete admin user")
        else:
            # Remove the user
            del config['credentials']['usernames'][username_to_delete]
            
            # Save the updated config
            with open('config.yaml', 'w') as file:
                yaml.dump(config, file, default_flow_style=False)
            
            st.success(f"User '{username_to_delete}' deleted successfully")
            st.rerun()