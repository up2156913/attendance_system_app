import streamlit_authenticator as stauth

# Replace 'your_password' with your desired admin password
hashed_password = stauth.Hasher(['your_password']).generate()[0]
print(f"Your hashed password is: {hashed_password}")