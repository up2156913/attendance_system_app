import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
import os

class Authentication:
    def __init__(self):
        # Initialize the authentication state
        self.initialize_auth_state()
        
    def initialize_auth_state(self):
        """Initialize authentication state variables in session state"""
        if 'authentication_status' not in st.session_state:
            st.session_state['authentication_status'] = None
        if 'username' not in st.session_state:
            st.session_state['username'] = None
        if 'name' not in st.session_state:
            st.session_state['name'] = None
    
    def load_config(self):
        """Load authentication configuration from YAML file"""
        # Create config file if it doesn't exist
        config_path = 'config.yaml'
        
        if not os.path.exists(config_path):
            # Default credentials: username: admin, password: abc
            default_config = {
                'credentials': {
                    'usernames': {
                        'admin': {
                            'name': 'Admin User',
                            'email': 'attendancesystem282@gmail.com',
                            'password': stauth.Hasher(['abc']).generate()[0]
                        }
                    }
                },
                'cookie': {
                    'expiry_days': 30,
                    'key': 'some_signature_key',
                    'name': 'some_cookie_name'
                }
            }
            
            with open(config_path, 'w') as file:
                yaml.dump(default_config, file, default_flow_style=False)
        
        # Load the config file
        with open(config_path, 'r') as file:
            config = yaml.load(file, Loader=SafeLoader)
            
        return config
    
    def create_authenticator(self):
        """Create and return an authenticator object"""
        config = self.load_config()
        
        authenticator = stauth.Authenticate(
            config['credentials'],
            config['cookie']['name'],
            config['cookie']['key'],
            config['cookie']['expiry_days']
        )
        
        return authenticator
    
    def login(self, title, location):
        """Display the login form and handle authentication"""
        authenticator = self.create_authenticator()
        
        name, authentication_status, username = authenticator.login(title, location)
        
        st.session_state['authentication_status'] = authentication_status
        st.session_state['username'] = username
        st.session_state['name'] = name
        
        return authentication_status, username, name
    
    def logout(self):
        """Log out the current user"""
        authenticator = self.create_authenticator()
        authenticator.logout('Logout', 'sidebar')
        
    def is_authenticated(self):
        """Check if the user is authenticated"""
        return st.session_state['authentication_status']
    
    def show_login_message(self):
        """Show appropriate message based on authentication status"""
        if st.session_state['authentication_status'] is False:
            st.error('Username/password is incorrect')
        elif st.session_state['authentication_status'] is None:
            st.warning('Please enter your username and password')
    
    def register_user(self, username, name, email, password):
        """Register a new user"""
        config = self.load_config()
        
        if username in config['credentials']['usernames']:
            return False, "Username already exists"
        
        # Hash the password
        hashed_password = stauth.Hasher([password]).generate()[0]
        
        # Add the new user
        config['credentials']['usernames'][username] = {
            'name': name,
            'email': email,
            'password': hashed_password
        }
        
        # Save the updated config
        with open('config.yaml', 'w') as file:
            yaml.dump(config, file, default_flow_style=False)
            
        return True, "User registered successfully"


# Create a global authenticator instance
authenticator = Authentication()