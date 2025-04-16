import streamlit as st
from auth import authenticator

st.set_page_config(
    page_title='Smart Attendance', 
    page_icon='👁️',
    layout='wide', 
    initial_sidebar_state='auto'
)

st.markdown("""
<style>
    /* Primary colors */
    :root {
        --primary: #3B82F6;       /* Bright blue - brand color */
        --primary-light: #93C5FD; /* Light blue */
        --accent: #F59E0B;        /* Amber - for highlights/buttons */
        --success: #10B981;       /* Emerald green - for success messages */
        --text-primary: #1E293B;  /* Dark slate - primary text */
        --text-secondary: #64748B; /* Slate - secondary text */
    }
    
    /* Light/Dark mode responsive styling */
    .streamlit-container {
        background-color: var(--background-color);
    }
    
    .main-header {
        color: var(--primary);
        font-size: 2.5rem;
        font-weight: 800;
        margin-bottom: 0;
    }
    
    .tagline {
        color: var(--primary-light);
        font-size: 1.2rem;
        margin-top: -0.5rem;
        margin-bottom: 2rem;
        font-weight: 400;
    }
    
    .welcome-card {
        background-color: rgba(59, 130, 246, 0.1);
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 1.5rem;
        border-left: 4px solid var(--primary);
    }
    
    .dashboard-icon {
        color: var(--accent);
    }
    
    .success-message {
        background-color: rgba(16, 185, 129, 0.1);
        color: var(--success);
        padding: 0.75rem;
        border-radius: 5px;
        border-left: 3px solid var(--success);
        font-weight: 500;
    }
    
    .quick-access-card {
        background-color: rgba(59, 130, 246, 0.05);
        padding: 1.25rem;
        border-radius: 8px;
        transition: all 0.2s ease;
        height: 100%;
    }
    
    .quick-access-card:hover {
        background-color: rgba(59, 130, 246, 0.1);
        transform: translateY(-2px);
    }
    
    .footer {
        text-align: center;
        color: var(--text-secondary);
        font-size: 0.8rem;
        margin-top: 3rem;
        border-top: 1px solid rgba(100, 116, 139, 0.2);
        padding-top: 1rem;
    }
    
    /* Button styling */
    .stButton button {
        background-color: var(--primary);
        color: white;
        border-radius: 6px;
        padding: 0.5rem 1rem;
        border: none;
        transition: all 0.2s ease;
    }
    
    .stButton button:hover {
        background-color: var(--accent);
        transform: translateY(-1px);
    }
</style>
""", unsafe_allow_html=True)


# Make sure authentication state is initialized
authenticator.initialize_auth_state()

# Check authentication status
if not st.session_state['authentication_status']:
    # Login page with branding
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown('<div class="main-header">Smart Attendance</div>', unsafe_allow_html=True)
        st.markdown('<div class="tagline">Attendance made intelligent</div>', unsafe_allow_html=True)
        
        st.markdown("""
        <div class="welcome-card">
            <h3>👋 Welcome to Smart Attendance</h3>
            <p>This facial recognition system makes attendance tracking effortless, accurate, and secure.</p>
            <p>Please login to access the system.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        authenticator.login('Login', 'main')
        authenticator.show_login_message()
    
    # Feature highlights
    st.markdown("### Key Features")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("#### 📝 Easy Registration")
        st.write("Register once with facial recognition and you're all set.")
        
    with col2:
        st.markdown("#### 📸 Real-time Tracking")
        st.write("Automatic attendance marking using advanced facial recognition.")
        
    with col3:
        st.markdown("#### 📊 Detailed Reports")
        st.write("Access attendance data and generate comprehensive reports.")
    
    st.stop()  # Stop execution if not authenticated
else:
    # Show logout button in sidebar if authenticated
    with st.sidebar:
        st.write(f"Welcome, {st.session_state['name']}")
        authenticator.logout()

    # Main content - only shown if authenticated
    st.markdown('<div class="main-header">Smart Attendance</div>', unsafe_allow_html=True)
    st.markdown('<div class="tagline">Attendance made intelligent</div>', unsafe_allow_html=True)
    
    # Dashboard overview
    st.markdown("### 🚀 Dashboard")
    st.markdown("""
    <div class="welcome-card">
        <h3>Welcome back, {}</h3>
        <p>Your facial recognition attendance system is up and running. Use the sidebar to navigate through different features.</p>
    </div>
    """.format(st.session_state['name']), unsafe_allow_html=True)
    
    # System status
    with st.spinner("Loading Models and Connecting to Redis db ..."):
        import face_rec

    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="success-message">✅ Model loaded successfully</div>', unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="success-message">✅ Redis db connected successfully</div>', unsafe_allow_html=True)
    
    # Quick access cards
    st.markdown("### Quick Access")
    quick_col1, quick_col2, quick_col3 = st.columns(3)
    
    with quick_col1:
        st.markdown("#### 📝 Registration")
        st.write("Register new users with facial recognition")
        if st.button("Go to Registration"):
            st.switch_page("pages/2_Registration_form.py")
    
    with quick_col2:
        st.markdown("#### 📸 Take Attendance")
        st.write("Start real-time attendance tracking")
        if st.button("Go to Attendance"):
            st.switch_page("pages/1_Real_Time_Prediction.py")
    
    with quick_col3:
        st.markdown("#### 📊 Reports")
        st.write("View and export attendance reports")
        if st.button("Go to Reports"):
            st.switch_page("pages/3_Report.py")
    
    # Footer
    st.markdown('<div class="footer">© 2025 SmartAttend | Secure • Accurate • Efficient</div>', unsafe_allow_html=True)