import streamlit as st
import datetime
import requests
import json
import firebase_admin
from firebase_admin import credentials, firestore, storage
import uuid
from collections import defaultdict
import plotly.express as px
import pandas as pd
import time

# Define admin emails
ADMINS = ["nameer.ansaf@gmail.com", "anvinimithk2505@gmail.com"]

# Page Config
st.set_page_config(
    page_title="UniteSphere", 
    layout="centered", 
    page_icon="🤝",
    initial_sidebar_state="expanded"
)

# Custom CSS for professional UI with consistent blue text
st.markdown(
    """
    <style>
    /* Hide sidebar expander arrow */
    [data-testid="collapsedControl"] {
        display: none;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0d6efd 0%, #0b5ed7 100%);
        color: white;
        padding: 20px 15px;
    }
    [data-testid="stSidebar"] .sidebar-content {
        color: white;
    }
    [data-testid="stSidebar"] .stSelectbox, [data-testid="stSidebar"] .stButton>button {
        width: 100%;
    }
    [data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"] {
        background-color: white;
    }
    [data-testid="stSidebar"] .stButton>button {
        background: white;
        color: #0d6efd;
        font-weight: bold;
        margin: 5px 0;
        border: none;
    }
    [data-testid="stSidebar"] .stButton>button:hover {
        background: #f8f9fa !important;
        color: #0b5ed7;
    }
    
    /* Main content padding */
    .main .block-container {
        padding: 2rem 3rem;
    }
    
    /* Background */
    .main {
        background-color: #f8f9fa;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    /* Consistent blue text for all content */
    body, h1, h2, h3, h4, h5, h6, p, div, span {
        color: #0d6efd !important;  /* Primary blue color */
    }
    
    /* Headers */
    h1, h2, h3 {
        font-family: 'Arial', sans-serif;
        border-bottom: 2px solid #0d6efd;
        padding-bottom: 8px;
    }
    /* Buttons */
    div.stButton > button:not([class*="st-emotion-cache"]):not([data-testid="baseButton-secondary"]) {
        background: linear-gradient(45deg, #0d6efd 0%, #6f42c1 100%);
        color: white;
        font-weight: bold;
        border-radius: 8px;
        padding: 8px 20px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        transition: background 0.3s ease;
        border: none;
    }
    div.stButton > button:hover:not([class*="st-emotion-cache"]):not([data-testid="baseButton-secondary"]) {
        background: linear-gradient(45deg, #0b5ed7 0%, #5a32a3 100%);
        transform: translateY(-1px);
        box-shadow: 0 4px 6px rgba(0,0,0,0.15);
    }
    /* Text Inputs */
    input[type="text"], input[type="password"], textarea {
        border: 1px solid #ced4da !important;
        border-radius: 6px;
        padding: 8px;
        background-color: white;
        color: #495057 !important;
    }
    /* Select boxes */
    div[role="listbox"] {
        background-color: white;
        color: #495057;
        border-radius: 6px;
        border: 1px solid #ced4da !important;
    }
    /* Scrollbar for chat container */
    .streamlit-expanderContent {
        max-height: 300px;
        overflow-y: auto;
    }
    /* Stats cards */
    .stats-card {
        background: white;
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        border-left: 4px solid #0d6efd;
    }
    .stats-card h3 {
        color: #6c757d !important;
        margin-top: 0;
        font-size: 1rem;
    }
    .stats-card .value {
        font-size: 2rem;
        font-weight: bold;
        color: #0d6efd !important;
        text-align: center;
    }
    /* Product cards */
    .product-card {
        background: white;
        border-radius: 10px;
        padding: 20px;
        margin: 15px 0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        border: 1px solid #e9ecef;
    }
    .volunteer-badge {
        background: #198754;
        color: white;
        border-radius: 12px;
        padding: 2px 10px;
        font-size: 0.8rem;
        font-weight: bold;
        display: inline-block;
        margin: 5px;
    }
    .admin-panel {
        background-color: #fff3cd;
        border-radius: 8px;
        padding: 15px;
        margin: 15px 0;
        border: 1px solid #ffecb5;
    }
    .delete-btn {
        background: #dc3545 !important;
    }
    .milestone {
        background: #e6f7ff;
        border-left: 4px solid #0d6efd;
        padding: 10px;
        margin: 10px 0;
        border-radius: 0 8px 8px 0;
    }
    .home-feature {
        text-align: center;
        margin: 20px;
        padding: 25px 15px;
        border-radius: 12px;
        background: white;
        box-shadow: 0 6px 12px rgba(0,0,0,0.08);
        flex: 1;
        min-width: 250px;
        min-height: 250px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    .home-feature:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 20px rgba(0,0,0,0.12);
    }
    .home-feature-icon {
        font-size: 3.5rem;
        color: #0d6efd;
        font-weight: bold;
        margin-bottom: 15px;
        flex-shrink: 0;
    }
    .home-feature h3 {
        font-size: 1.3rem;
        margin: 10px 0;
        min-height: 3rem;
    }
    .home-feature p {
        font-size: 1rem;
        line-height: 1.4;
        margin-bottom: 0;
        flex-grow: 1;
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 0 5px;
    }
    .home-container {
        background: white;
        border-radius: 15px;
        padding: 30px;
        margin: 20px 0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        text-align: center;
    }
    .feature-container {
        display: flex;
        justify-content: center;
        flex-wrap: wrap;
        margin: 30px 0;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        padding: 0 20px;
        border-radius: 8px !important;
        background-color: #e9ecef !important;
    }
    .stTabs [aria-selected="true"] {
        background-color: #0d6efd !important;
        color: white !important;
    }
    .logo-container {
        display: flex;
        justify-content: center;
        margin-bottom: 20px;
    }
    /* Mobile responsiveness */
    @media (max-width: 768px) {
        .main .block-container {
            padding: 1rem;
        }
        .home-feature {
            min-width: 100%;
            margin: 10px 0;
        }
        .stats-card {
            padding: 15px;
        }
        .stats-card .value {
            font-size: 1.5rem;
        }
    }
    /* Task cards */
    .task-card {
        background: white;
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        border-left: 3px solid #0d6efd;
    }
    .task-card.completed {
        border-left-color: #198754;
        opacity: 0.8;
    }
    .tag {
        display: inline-block;
        background: #e6f7ff;
        color: #0d6efd;
        border-radius: 20px;
        padding: 2px 10px;
        font-size: 0.8rem;
        margin: 2px;
    }
    .bookmark-btn {
        position: absolute;
        top: 10px;
        right: 10px;
        background: transparent;
        border: none;
        font-size: 1.5rem;
        cursor: pointer;
        z-index: 10;
    }
    .notification-badge {
        position: absolute;
        top: -5px;
        right: -5px;
        background: #dc3545;
        color: white;
        border-radius: 50%;
        width: 20px;
        height: 20px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 0.7rem;
        font-weight: bold;
    }
    .user-card {
        background: white;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        border: 1px solid #e9ecef;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Firebase setup - make sure it's initialized once
if not firebase_admin._apps:
    try:
        # Load Firebase Service Account from secrets
        service_account_json = st.secrets["FIREBASE_SERVICE_ACCOUNT"]
        
        # Parse the JSON string to a dictionary
        key_dict = json.loads(service_account_json)
        
        # Create credentials from the dictionary
        cred = credentials.Certificate(key_dict)
        
        # Get project ID and format bucket name correctly
        project_id = key_dict['project_id']
        # Replace hyphens with dots in bucket name
        formatted_project_id = project_id.replace('-', '.')
        bucket_name = f"{formatted_project_id}.appspot.com"
        
        # Initialize Firebase app with credentials and storage bucket
        firebase_admin.initialize_app(cred, {
            'storageBucket': bucket_name
        })
    except Exception as e:
        st.error(f"Firebase initialization failed: {e}")

# Set up Firestore client and API key
db = firestore.client()
FIREBASE_API_KEY = st.secrets["FIREBASE_API_KEY"]

# Get storage bucket explicitly using the bucket name
try:
    if firebase_admin._apps:
        FIREBASE_BUCKET = storage.bucket()
    else:
        FIREBASE_BUCKET = None
except Exception as e:
    st.error(f"Failed to initialize Firebase Storage: {e}")
    FIREBASE_BUCKET = None

# Helper function for safe data access
def safe_get(data, key, default=None):
    """Safely get value from dictionary with default fallback"""
    if data is None:
        return default
    return data.get(key, default)

# Auth functions
def signup(email, password):
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={FIREBASE_API_KEY}"
    payload = {"email": email, "password": password, "returnSecureToken": True}
    return requests.post(url, json=payload).json()

def login(email, password):
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_API_KEY}"
    payload = {"email": email, "password": password, "returnSecureToken": True}
    return requests.post(url, json=payload).json()

def send_verification_email(id_token):
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:sendOobCode?key={FIREBASE_API_KEY}"
    return requests.post(url, json={"requestType": "VERIFY_EMAIL", "idToken": id_token}).json()

def check_email_verified(id_token):
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:lookup?key={FIREBASE_API_KEY}"
    res = requests.post(url, json={"idToken": id_token}).json()
    return res.get("users", [{}])[0].get("emailVerified", False)

def reset_password(email):
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:sendOobCode?key={FIREBASE_API_KEY}"
    payload = {"requestType": "PASSWORD_RESET", "email": email}
    return requests.post(url, json=payload).json()

# Firestore functions
def post_idea(title, description, user_uid, deadline, milestones, contact, tags=None, skills_needed=None):
    idea_data = {
        "title": title,
        "description": description,
        "createdAt": datetime.datetime.utcnow(),
        "createdBy": user_uid,
        "team": [user_uid],
        "deadline": deadline,
        "contact": contact,
        "status": "Planning",
        "milestones": milestones or [],
        "tags": tags or [],
        "skills_needed": skills_needed or [],
        "bookmarks": []
    }
    return db.collection("posts").add(idea_data)

def update_idea(post_id, new_title, new_description, new_deadline, new_status, new_milestones, new_contact, new_tags, new_skills):
    update_data = {
        "title": new_title,
        "description": new_description,
        "deadline": new_deadline,
        "status": new_status,
        "contact": new_contact,
        "tags": new_tags,
        "skills_needed": new_skills
    }
    if new_milestones is not None:
        update_data["milestones"] = new_milestones
    db.collection("posts").document(post_id).update(update_data)

def delete_idea(post_id):
    db.collection("posts").document(post_id).delete()

def get_all_posts():
    posts = db.collection("posts").order_by("createdAt", direction=firestore.Query.DESCENDING).stream()
    return [(doc.id, doc.to_dict()) for doc in posts]

def join_team(post_id, user_uid):
    ref = db.collection("posts").document(post_id)
    doc = ref.get()
    if doc.exists:
        data = doc.to_dict()
        if user_uid not in data["team"]:
            data["team"].append(user_uid)
            ref.update({"team": data["team"]})

def get_all_products_services():
    items = db.collection("products_services").order_by("createdAt", direction=firestore.Query.DESCENDING).stream()
    return [(doc.id, doc.to_dict()) for doc in items]

def get_user_teams(user_uid):
    posts = get_all_posts()
    return [(pid, safe_get(p, "title", "Untitled Project")) for pid, p in posts if user_uid in safe_get(p, "team", [])]

def upload_image_to_firebase(img_file):
    if img_file is not None and FIREBASE_BUCKET is not None:
        try:
            blob_name = f"products/{uuid.uuid4().hex}_{img_file.name}"
            blob = FIREBASE_BUCKET.blob(blob_name)
            blob.upload_from_file(img_file, content_type=img_file.type)
            blob.make_public()
            return blob.public_url
        except Exception as e:
            st.error(f"Failed to upload image: {e}")
    return None

def delete_product(item_id):
    db.collection("products_services").document(item_id).delete()

def count_total_stats():
    # Count total ideas
    total_ideas = len(list(db.collection("posts").stream()))
    
    # Count products and services
    items = db.collection("products_services").stream()
    total_products = 0
    total_services = 0
    for item in items:
        data = item.to_dict()
        if safe_get(data, "type") == "product":
            total_products += 1
        elif safe_get(data, "type") == "service":
            total_services += 1
    
    # Count unique users
    user_set = set()
    posts = db.collection("posts").stream()
    for post in posts:
        data = post.to_dict()
        user_set.add(safe_get(data, "createdBy", ""))
        for member in safe_get(data, "team", []):
            user_set.add(member)
    
    total_users = len(user_set)
    
    return total_ideas, total_products, total_services, total_users

def add_milestone(post_id, milestone):
    ref = db.collection("posts").document(post_id)
    ref.update({"milestones": firestore.ArrayUnion([milestone])})

def mark_milestone_complete(post_id, milestone_index):
    ref = db.collection("posts").document(post_id)
    doc = ref.get()
    if doc.exists:
        data = doc.to_dict()
        milestones = safe_get(data, "milestones", [])
        if milestone_index < len(milestones):
            milestones[milestone_index]["completed"] = True
            ref.update({"milestones": milestones})

# NEW: Task management functions
def add_task(post_id, task):
    ref = db.collection("posts").document(post_id)
    ref.update({"tasks": firestore.ArrayUnion([task])})

def update_task(post_id, task_index, updated_task):
    ref = db.collection("posts").document(post_id)
    doc = ref.get()
    if doc.exists:
        data = doc.to_dict()
        tasks = safe_get(data, "tasks", [])
        if task_index < len(tasks):
            tasks[task_index] = updated_task
            ref.update({"tasks": tasks})

# NEW: Bookmark functions
def toggle_bookmark(post_id, user_uid):
    ref = db.collection("posts").document(post_id)
    doc = ref.get()
    if doc.exists:
        data = doc.to_dict()
        bookmarks = safe_get(data, "bookmarks", [])
        if user_uid in bookmarks:
            bookmarks.remove(user_uid)
        else:
            bookmarks.append(user_uid)
        ref.update({"bookmarks": bookmarks})

# NEW: User profile functions
def get_user_profile(user_uid):
    doc = db.collection("profiles").document(user_uid).get()
    if doc.exists:
        return doc.to_dict()
    return None

def update_user_profile(user_uid, profile_data):
    db.collection("profiles").document(user_uid).set(profile_data, merge=True)

# NEW: Notification functions
def create_notification(user_uid, message, link=None):
    notification = {
        "message": message,
        "timestamp": datetime.datetime.utcnow(),
        "read": False,
        "link": link
    }
    db.collection("notifications").document(user_uid).update({
        "items": firestore.ArrayUnion([notification])
    })

def mark_notification_read(user_uid, index):
    doc = db.collection("notifications").document(user_uid).get()
    if doc.exists:
        data = doc.to_dict()
        notifications = safe_get(data, "items", [])
        if index < len(notifications):
            notifications[index]["read"] = True
            db.collection("notifications").document(user_uid).set({"items": notifications})

# NEW: Get all tags from projects
def get_all_tags():
    tags = set()
    posts = db.collection("posts").stream()
    for post in posts:
        data = post.to_dict()
        for tag in safe_get(data, "tags", []):
            tags.add(tag)
    return sorted(tags)

# NEW: Get all skills from projects
def get_all_skills():
    skills = set()
    posts = db.collection("posts").stream()
    for post in posts:
        data = post.to_dict()
        for skill in safe_get(data, "skills_needed", []):
            skills.add(skill)
    return sorted(skills)

# Simplified chat system
def post_chat_message(chat_ref, message, sender, file_url=None):
    try:
        message_data = {
            "sender": sender,
            "message": message.strip(),
            "timestamp": datetime.datetime.utcnow()
        }
        if file_url:
            message_data["file_url"] = file_url
            message_data["file_name"] = file_url.split("/")[-1].split("?")[0]
            
        chat_ref.add(message_data)
        return True
    except Exception as e:
        st.error(f"Failed to send message: {e}")
        return False

# UI starts
st.markdown('<div class="main">', unsafe_allow_html=True)

# Initialize session state for current page
if "current_page" not in st.session_state:
    st.session_state.current_page = "Project Ideas"

# NEW: Initialize notification count
if "notification_count" not in st.session_state:
    st.session_state.notification_count = 0

# Show sidebar only if logged in
if "id_token" in st.session_state:
    # Sidebar navigation
    st.sidebar.title("Navigation")
    
    # Check admin status
    is_admin = st.session_state.get("email") in ADMINS
    
    # Menu options with descriptions
    menu_options = [
        ("Project Ideas", "💡 Browse and join exciting projects"),
        ("Submit Idea", "✨ Pitch your project idea and build a team"),
        ("Team Chat", "💬 Collaborate with your team in real-time"),
        ("Products & Services", "🛒 Showcase and discover completed work"),
        ("My Profile", "👤 Manage your profile and skills"),
        ("Bookmarks", "🔖 View your saved projects"),
        ("Notifications", "🔔 View your notifications"),
        ("Rules", "📜 Community guidelines for everyone"),
        ("Stats", "📊 Platform statistics and insights")
    ]
    
    if is_admin:
        menu_options.append(("Admin", "🔒 Administrative tools and controls"))
    
    # Create sidebar menu with descriptions
    for page, description in menu_options:
        # Add notification badge to Notifications tab
        badge = ""
        if page == "Notifications" and st.session_state.notification_count > 0:
            badge = f'<span class="notification-badge">{st.session_state.notification_count}</span>'
        
        if st.sidebar.button(f"**{page}** {badge}\n{description}", use_container_width=True, key=f"menu_{page}"):
            st.session_state.current_page = page
    
    # Logout button at bottom
    st.sidebar.markdown("---")
    st.sidebar.write(f"Logged in as: {st.session_state['email']}")
    if st.sidebar.button("Logout", use_container_width=True, key="logout_button"):
        st.session_state.clear()
        st.rerun()

# Home Page - Show login/signup when not logged in
if "id_token" not in st.session_state:
    # Main menu with descriptions
    st.markdown("""
    <div class="home-container" style="text-align: center;">
        <h1>UniteSphere</h1>
        <h3>Team Collaboration Platform</h3>
        <p style="font-size: 1.2rem; max-width: 800px; margin: 20px auto;">
            Where developers, designers, and innovators come together to bring ideas to life
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Feature grid with descriptions
    features = [
        {"icon": "💡", "title": "Project Ideas", "desc": "Browse and join exciting projects"},
        {"icon": "✨", "title": "Submit Idea", "desc": "Pitch your project and build a team"},
        {"icon": "💬", "title": "Team Chat", "desc": "Collaborate in real-time with your team"},
        {"icon": "🛒", "title": "Marketplace", "desc": "Showcase and discover completed work"},
        {"icon": "👤", "title": "User Profiles", "desc": "Showcase your skills and experience"},
        {"icon": "🔖", "title": "Bookmarks", "desc": "Save interesting projects for later"},
        {"icon": "📊", "title": "Analytics", "desc": "Track project progress visually"},
        {"icon": "🔔", "title": "Notifications", "desc": "Stay updated on project activities"},
        {"icon": "📜", "title": "Community Rules", "desc": "Guidelines for a productive environment"}
    ]
    
    # Create 3 columns
    cols = st.columns(3)
    
    for i, feature in enumerate(features):
        with cols[i % 3]:
            st.markdown(f"""
            <div class="home-feature">
                <div class="home-feature-icon">{feature['icon']}</div>
                <h3>{feature['title']}</h3>
                <p>{feature['desc']}</p>
            </div>
            """, unsafe_allow_html=True)
    
    # Login/Signup Section
    st.markdown("---")
    st.subheader("Get Started")
    tab1, tab2, tab3 = st.tabs(["Login", "Sign Up", "Reset Password"])

    with tab1:
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_password")
        if st.button("Login", use_container_width=True, key="login_button"):
            if not email or not password:
                st.warning("Please enter your email and password")
            else:
                res = login(email, password)
                if "idToken" in res:
                    if check_email_verified(res["idToken"]):
                        st.session_state["id_token"] = res["idToken"]
                        st.session_state["email"] = email
                        st.session_state["user_uid"] = res["localId"]
                        st.session_state["current_page"] = "Project Ideas"
                        st.success("Login successful")
                        st.rerun()
                    else:
                        st.warning("Please verify your email first")
                else:
                    st.error("Login failed. Please check your credentials")

    with tab2:
        email = st.text_input("Email", key="signup_email")
        password = st.text_input("Password", type="password", key="signup_password")
        confirm_password = st.text_input("Confirm Password", type="password", key="confirm_password")
        if st.button("Sign Up", use_container_width=True, key="signup_button"):
            if not email or not password:
                st.warning("Please enter both email and password")
            elif password != confirm_password:
                st.warning("Passwords do not match")
            else:
                res = signup(email, password)
                if "idToken" in res:
                    send_verification_email(res["idToken"])
                    st.success("Account created. Please check your email for verification")
                else:
                    st.error("Sign up failed. Please try again")

    with tab3:
        email = st.text_input("Email for password reset", key="reset_email")
        if st.button("Send Reset Link", use_container_width=True, key="reset_button"):
            if email:
                res = reset_password(email)
                if "email" in res:
                    st.success("Password reset email sent. Please check your inbox.")
                else:
                    st.error("Failed to send reset email. Please check the email address.")
            else:
                st.warning("Please enter your email address")

# Project Ideas Page
elif st.session_state.current_page == "Project Ideas":
    st.header("Project Ideas")
    
    # NEW: Search and filter section
    col1, col2, col3 = st.columns([3, 2, 2])
    with col1:
        search_query = st.text_input("Search projects", placeholder="Search by title, description, or tags")
    with col2:
        status_filter = st.selectbox("Status", ["All", "Planning", "In Progress", "Testing", "Completed", "On Hold"])
    with col3:
        tags = get_all_tags()
        tag_filter = st.multiselect("Tags", tags)
    
    posts = get_all_posts()
    
    # NEW: Filter posts based on search and filters
    filtered_posts = []
    for post_id, post in posts:
        # Apply search filter
        if search_query:
            search_lower = search_query.lower()
            title = safe_get(post, 'title', '').lower()
            desc = safe_get(post, 'description', '').lower()
            post_tags = " ".join(safe_get(post, 'tags', [])).lower()
            if search_lower not in title and search_lower not in desc and search_lower not in post_tags:
                continue
        
        # Apply status filter
        if status_filter != "All":
            if safe_get(post, 'status', '') != status_filter:
                continue
                
        # Apply tag filter
        if tag_filter:
            post_tags = safe_get(post, 'tags', [])
            if not any(tag in post_tags for tag in tag_filter):
                continue
                
        filtered_posts.append((post_id, post))
    
    if not filtered_posts:
        st.info("No project ideas found matching your criteria")
    for post_id, post in filtered_posts:
        # Safe title generation
        title = safe_get(post, 'title', 'Untitled Project')
        team_size = len(safe_get(post, 'team', []))
        status = safe_get(post, 'status', 'Active')
        
        with st.expander(f"{title} - Team: {team_size} members | Status: {status}"):
            # NEW: Bookmark button
            bookmarks = safe_get(post, "bookmarks", [])
            is_bookmarked = st.session_state["user_uid"] in bookmarks
            bookmark_icon = "❤️" if is_bookmarked else "🤍"
            if st.button(f"{bookmark_icon}", key=f"bookmark_{post_id}"):
                toggle_bookmark(post_id, st.session_state["user_uid"])
                st.rerun()
            
            st.write(safe_get(post, "description", "No description available"))
            st.caption(f"Created by: {safe_get(post, 'createdBy', 'Unknown')}")
            
            # NEW: Display tags
            tags = safe_get(post, "tags", [])
            if tags:
                st.write("**Tags:**")
                for tag in tags:
                    st.markdown(f'<span class="tag">{tag}</span>', unsafe_allow_html=True)
            
            # Project details
            deadline = safe_get(post, "deadline")
            if deadline:
                try:
                    deadline_date = datetime.datetime.strptime(deadline, "%Y-%m-%d")
                    days_left = (deadline_date - datetime.datetime.now()).days
                    deadline_status = f"⏰ Deadline: {deadline} ({days_left} days left)"
                    st.write(deadline_status)
                except:
                    st.write(f"⏰ Deadline: {deadline}")
            
            contact = safe_get(post, "contact")
            if contact:
                st.write(f"📞 Contact: {contact}")
            
            # NEW: Skills needed
            skills_needed = safe_get(post, "skills_needed", [])
            if skills_needed:
                st.write("**Skills Needed:**")
                for skill in skills_needed:
                    st.markdown(f'<span class="tag">{skill}</span>', unsafe_allow_html=True)
            
            # Milestones section
            milestones = safe_get(post, "milestones", [])
            if milestones:
                st.subheader("Project Milestones")
                for i, milestone in enumerate(milestones):
                    status = "✅" if safe_get(milestone, "completed", False) else "⏳"
                    with st.container():
                        st.markdown(
                            f"<div class='milestone'><b>{status} {safe_get(milestone, 'name', 'Unnamed Milestone')}</b><br>"
                            f"{safe_get(milestone, 'description', 'No description')}</div>", 
                            unsafe_allow_html=True
                        )
                        
                        # NEW: Progress bar for milestones
                        progress = safe_get(milestone, "progress", 0)
                        if progress > 0:
                            st.progress(min(progress, 100))
                        
                        # Mark as complete button
                        if st.session_state["user_uid"] in safe_get(post, "team", []) and not safe_get(milestone, "completed", False):
                            if st.button(f"Mark Complete", key=f"complete_{post_id}_{i}"):
                                mark_milestone_complete(post_id, i)
                                st.success("Milestone marked as complete!")
                                st.rerun()
            
            # NEW: Task management
            tasks = safe_get(post, "tasks", [])
            if tasks:
                st.subheader("Project Tasks")
                for i, task in enumerate(tasks):
                    completed = safe_get(task, "completed", False)
                    with st.container():
                        st.markdown(f"<div class='task-card {'completed' if completed else ''}'>", unsafe_allow_html=True)
                        st.write(f"**{safe_get(task, 'title', 'Untitled Task')}**")
                        st.caption(f"Assigned to: {safe_get(task, 'assigned_to', 'Unassigned')} | Due: {safe_get(task, 'due_date', 'No due date')}")
                        st.write(safe_get(task, "description", "No description"))
                        
                        if st.session_state["user_uid"] == safe_get(post, "createdBy") or st.session_state["user_uid"] == safe_get(task, "assigned_to"):
                            if st.button(f"{'Unmark' if completed else 'Mark'} Complete", key=f"task_{post_id}_{i}"):
                                task["completed"] = not completed
                                update_task(post_id, i, task)
                                st.rerun()
                        st.markdown("</div>", unsafe_allow_html=True)
            
            # Join team button
            if st.session_state["user_uid"] not in safe_get(post, "team", []):
                if st.button("Join Team", key=f"join_{post_id}"):
                    join_team(post_id, st.session_state["user_uid"])
                    st.success("You joined this team")
                    st.rerun()
            
            # Idea owner controls
            if safe_get(post, "createdBy") == st.session_state["user_uid"]:
                st.subheader("Manage Your Project")
                new_title = st.text_input("Edit Title", value=title, key=f"title_{post_id}")
                new_desc = st.text_area("Edit Description", value=safe_get(post, "description", ""), key=f"desc_{post_id}")
                
                # Deadline and contact
                col1, col2 = st.columns(2)
                with col1:
                    try:
                        deadline_value = datetime.datetime.strptime(deadline or str(datetime.date.today()), "%Y-%m-%d")
                    except:
                        deadline_value = datetime.datetime.now()
                    new_deadline = st.date_input("Edit Deadline", 
                                                value=deadline_value, 
                                                key=f"deadline_{post_id}")
                with col2:
                    new_contact = st.text_input("Edit Contact", value=contact or "", key=f"contact_{post_id}")
                
                # Status
                status_options = ["Planning", "In Progress", "Testing", "Completed", "On Hold"]
                current_status = status
                status_index = status_options.index(current_status) if current_status in status_options else 0
                new_status = st.selectbox("Project Status", status_options, index=status_index, key=f"status_{post_id}")
                
                # NEW: Tags and skills
                col3, col4 = st.columns(2)
                with col3:
                    all_tags = get_all_tags()
                    new_tags = st.multiselect("Edit Tags", all_tags, default=safe_get(post, "tags", []), key=f"tags_{post_id}")
                with col4:
                    all_skills = get_all_skills()
                    new_skills = st.multiselect("Edit Skills Needed", all_skills, default=safe_get(post, "skills_needed", []), key=f"skills_{post_id}")
                
                # Milestone management
                st.subheader("Manage Milestones")
                new_milestones = []
                existing_milestones = milestones
                
                # Display existing milestones for editing
                for i, milestone in enumerate(existing_milestones):
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        name = st.text_input(f"Milestone {i+1} Name", value=safe_get(milestone, "name", ""), key=f"milestone_name_{post_id}_{i}")
                        desc = st.text_area(f"Description", value=safe_get(milestone, "description", ""), key=f"milestone_desc_{post_id}_{i}")
                        # NEW: Progress input
                        progress = st.slider("Progress (%)", 0, 100, value=safe_get(milestone, "progress", 0), key=f"milestone_progress_{post_id}_{i}")
                    with col2:
                        completed = st.checkbox("Completed", value=safe_get(milestone, "completed", False), key=f"milestone_complete_{post_id}_{i}")
                    new_milestones.append({"name": name, "description": desc, "completed": completed, "progress": progress})
                
                # Add new milestone
                if st.button("Add New Milestone", key=f"add_milestone_{post_id}"):
                    new_milestones.append({"name": "New Milestone", "description": "", "completed": False, "progress": 0})
                
                # NEW: Task management
                st.subheader("Manage Tasks")
                new_tasks = []
                existing_tasks = tasks
                
                for i, task in enumerate(existing_tasks):
                    with st.expander(f"Task {i+1}: {safe_get(task, 'title', 'Untitled Task')}"):
                        title_task = st.text_input("Title", value=safe_get(task, "title", ""), key=f"task_title_{post_id}_{i}")
                        desc_task = st.text_area("Description", value=safe_get(task, "description", ""), key=f"task_desc_{post_id}_{i}")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            assigned_to = st.text_input("Assigned To (User ID)", value=safe_get(task, "assigned_to", ""), key=f"task_assigned_{post_id}_{i}")
                        with col2:
                            due_date = st.date_input("Due Date", value=datetime.datetime.strptime(safe_get(task, "due_date", str(datetime.date.today())), "%Y-%m-%d") if "due_date" in task else datetime.date.today(), key=f"task_due_{post_id}_{i}")
                        
                        completed_task = st.checkbox("Completed", value=safe_get(task, "completed", False), key=f"task_completed_{post_id}_{i}")
                        new_tasks.append({
                            "title": title_task, 
                            "description": desc_task, 
                            "assigned_to": assigned_to,
                            "due_date": str(due_date),
                            "completed": completed_task
                        })
                
                # Add new task
                if st.button("Add New Task", key=f"add_task_{post_id}"):
                    new_tasks.append({
                        "title": "New Task",
                        "description": "",
                        "assigned_to": "",
                        "due_date": str(datetime.date.today()),
                        "completed": False
                    })
                
                # Update button
                if st.button("Update Project", key=f"update_{post_id}"):
                    update_idea(post_id, new_title, new_desc, str(new_deadline), new_status, new_milestones, new_contact, new_tags, new_skills)
                    if new_tasks:
                        db.collection("posts").document(post_id).update({"tasks": new_tasks})
                    st.success("Project updated")
                    st.rerun()
                
                # Delete button
                if st.button("Delete Project", key=f"delete_{post_id}", type="secondary"):
                    delete_idea(post_id)
                    st.success("Project deleted")
                    st.rerun()

# Submit Idea Page
elif st.session_state.current_page == "Submit Idea":
    st.header("Submit a New Project Idea")
    title = st.text_input("Project Title", key="new_project_title")
    description = st.text_area("Project Description", key="new_project_desc")
    
    col1, col2 = st.columns(2)
    with col1:
        deadline = st.date_input("Project Deadline", min_value=datetime.date.today(), key="new_project_deadline")
    with col2:
        contact = st.text_input("Contact Information", key="new_project_contact")
    
    # NEW: Tags and skills
    col3, col4 = st.columns(2)
    with col3:
        tags = st.multiselect("Tags (optional)", get_all_tags(), key="new_project_tags")
    with col4:
        skills_needed = st.multiselect("Skills Needed (optional)", get_all_skills(), key="new_project_skills")
    
    # Milestones
    st.subheader("Project Milestones")
    milestones = []
    num_milestones = st.slider("Number of Milestones", 0, 10, 3, key="milestone_count")
    
    for i in range(num_milestones):
        st.markdown(f"### Milestone {i+1}")
        name = st.text_input(f"Name", key=f"milestone_name_{i}")
        desc = st.text_area(f"Description", key=f"milestone_desc_{i}")
        # NEW: Progress input
        progress = st.slider("Initial Progress (%)", 0, 100, 0, key=f"milestone_progress_{i}")
        milestones.append({"name": name, "description": desc, "completed": False, "progress": progress})
    
    if st.button("Submit Project", use_container_width=True, key="submit_project_button"):
        if title and description:
            post_idea(title, description, st.session_state["user_uid"], str(deadline), milestones, contact, tags, skills_needed)
            st.success("Your project has been posted")
            st.rerun()
        else:
            st.warning("Please fill both title and description fields")

# Team Chat Page
elif st.session_state.current_page == "Team Chat":
    st.header("Team Communication")
    user_posts = [(pid, safe_get(p, "title", "Untitled Project")) for pid, p in get_all_posts() if st.session_state["user_uid"] in safe_get(p, "team", [])]

    if not user_posts:
        st.info("You need to join a team to access team chat")
    else:
        selected = st.selectbox("Select a team", user_posts, format_func=lambda x: x[1], key="chat_team_select")
        selected_post_id, selected_title = selected

        st.subheader(f"Chat: {selected_title}")
        chat_ref = db.collection("posts").document(selected_post_id).collection("chat")

        # NEW: File upload for chat
        uploaded_file = st.file_uploader("Upload a file", type=["pdf", "docx", "xlsx", "jpg", "png", "zip"], key="chat_file_upload")
        
        # Chat messages display
        chat_container = st.container()
        with chat_container:
            chat_messages = list(chat_ref.order_by("timestamp", direction=firestore.Query.DESCENDING).limit(50).stream())
            for msg in reversed(chat_messages):
                msg_data = msg.to_dict()
                sender = safe_get(msg_data, "sender", "Unknown")
                content = safe_get(msg_data, "message", "")
                timestamp = safe_get(msg_data, "timestamp", datetime.datetime.utcnow()).strftime("%H:%M")
                file_url = safe_get(msg_data, "file_url")
                file_name = safe_get(msg_data, "file_name")
                
                # Different styling for current user
                if sender == st.session_state["email"]:
                    st.markdown(f"""
                    <div style="background: #e6f2ff; padding: 10px; border-radius: 10px; margin: 5px 0; text-align: right;">
                        <div><strong>You</strong> • {timestamp}</div>
                        <div>{content}</div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div style="background: #f8f9fa; padding: 10px; border-radius: 10px; margin: 5px 0; border: 1px solid #dee2e6;">
                        <div><strong>{sender}</strong> • {timestamp}</div>
                        <div>{content}</div>
                    """, unsafe_allow_html=True)
                
                # File display
                if file_url:
                    st.markdown(f"""
                    <div style="margin-top: 5px;">
                        <a href="{file_url}" target="_blank" style="color: #0d6efd; text-decoration: none;">
                            📎 {file_name}
                        </a>
                    </div>
                    """, unsafe_allow_html=True)
                
                st.markdown("</div>", unsafe_allow_html=True)

        # Message input
        st.markdown("---")
        new_msg = st.text_input("Type your message", key=f"chat_input_{selected_post_id}")
        col1, col2 = st.columns([1, 3])
        with col1:
            if st.button("Send", key=f"send_button_{selected_post_id}"):
                file_url = None
                if uploaded_file:
                    file_url = upload_image_to_firebase(uploaded_file)
                if new_msg.strip() or file_url:
                    if post_chat_message(chat_ref, new_msg, st.session_state["email"], file_url):
                        st.success("Message sent")
                        st.rerun()
        with col2:
            if st.button("Clear Chat", type="secondary", key=f"clear_chat_{selected_post_id}"):
                st.warning("This feature is currently under development")

# Products & Services Page
elif st.session_state.current_page == "Products & Services":
    st.header("Products & Services Marketplace")
    st.info("This is where completed projects can be offered as products or services")
    
    user_teams = get_user_teams(st.session_state["user_uid"])
    
    if not user_teams:
        st.info("Join or create a team first to post products or services")
    else:
        tab_prod, tab_serv, tab_view = st.tabs(["Post Product", "Offer Service", "Browse Marketplace"])
        
        # Product Submission
        with tab_prod:
            st.subheader("Submit a Completed Product")
            selected_team = st.selectbox("Team", user_teams, format_func=lambda x: x[1], key="prod_team_select")
            prod_title = st.text_input("Product Name", key="prod_title")
            prod_desc = st.text_area("Product Description", key="prod_desc")
            prod_price = st.text_input("Price", key="prod_price")
            prod_contact = st.text_input("Contact Information", key="prod_contact")
            prod_image = st.file_uploader("Product Image", type=["png", "jpg", "jpeg"], key="prod_image")
            
            # NEW: Rating system
            prod_rating = st.slider("Quality Rating (1-5)", 1, 5, 3, key="prod_rating")
            
            if st.button("Submit Product", use_container_width=True, key="submit_product_button"):
                if prod_title and prod_desc and prod_contact and prod_price:
                    image_url = upload_image_to_firebase(prod_image) if prod_image else None
                    db.collection("products_services").add({
                        "team_id": selected_team[0],
                        "team_title": selected_team[1],
                        "type": "product",
                        "title": prod_title,
                        "description": prod_desc,
                        "price": prod_price,
                        "contact": prod_contact,
                        "image_url": image_url,
                        "createdBy": st.session_state["user_uid"],
                        "createdAt": datetime.datetime.utcnow(),
                        "rating": prod_rating,
                        "reviews": []
                    })
                    st.success("Product submitted to marketplace")
                    st.rerun()
                else:
                    st.warning("Please fill all required fields")
        
        # Service Submission
        with tab_serv:
            st.subheader("Offer a Service")
            selected_team_s = st.selectbox("Team", user_teams, format_func=lambda x: x[1], key="serv_team_select")
            serv_title = st.text_input("Service Name", key="serv_title")
            serv_desc = st.text_area("Service Description", key="serv_desc")
            serv_price = st.text_input("Price", key="serv_price")
            serv_contact = st.text_input("Contact Information", key="serv_contact")
            
            # NEW: Service availability
            availability = st.selectbox("Availability", ["Full-time", "Part-time", "Contract", "As needed"], key="serv_availability")
            
            if st.button("Submit Service", use_container_width=True, key="submit_service_button"):
                if serv_title and serv_desc and serv_contact and serv_price:
                    db.collection("products_services").add({
                        "team_id": selected_team_s[0],
                        "team_title": selected_team_s[1],
                        "type": "service",
                        "title": serv_title,
                        "description": serv_desc,
                        "price": serv_price,
                        "contact": serv_contact,
                        "availability": availability,
                        "createdBy": st.session_state["user_uid"],
                        "createdAt": datetime.datetime.utcnow(),
                        "volunteers": []
                    })
                    st.success("Service submitted to marketplace")
                    st.rerun()
                else:
                    st.warning("Please fill all required fields")
        
        # Marketplace
        with tab_view:
            st.subheader("Marketplace")
            items = get_all_products_services()
            
            if not items:
                st.info("No products or services available")
            else:
                # Filter options
                filter_type = st.selectbox("Filter by Type", ["All", "Products", "Services"], key="marketplace_filter")
                
                # NEW: Search
                search_query = st.text_input("Search items", key="marketplace_search")
                
                # Display items
                for idx, (item_id, item) in enumerate(items):
                    item_type = safe_get(item, "type", "unknown")
                    
                    # Apply filter
                    if filter_type == "Products" and item_type != "product":
                        continue
                    if filter_type == "Services" and item_type != "service":
                        continue
                        
                    # Apply search
                    if search_query:
                        search_lower = search_query.lower()
                        title = safe_get(item, "title", "").lower()
                        desc = safe_get(item, "description", "").lower()
                        if search_lower not in title and search_lower not in desc:
                            continue
                            
                    with st.container():
                        st.markdown(f"<div class='product-card'>", unsafe_allow_html=True)
                        
                        # Header with type badge
                        st.markdown(f"**{safe_get(item, 'title', 'Untitled Item')}**")
                        st.caption(f"Type: {'Product' if item_type == 'product' else 'Service' if item_type == 'service' else 'Item'}")
                        
                        # NEW: Rating display
                        rating = safe_get(item, "rating", 0)
                        if rating > 0:
                            st.write(f"⭐ {'★' * rating}{'☆' * (5 - rating)}")
                        
                        image_url = safe_get(item, "image_url")
                        if image_url:
                            try:
                                st.image(image_url, width=300)
                            except Exception as e:
                                st.warning("Image unavailable or failed to load")
                        else:
                            st.info("No image available for this item")
                        
                        # Details
                        st.caption(f"By Team: {safe_get(item, 'team_title', 'Unknown Team')}")
                        st.write(safe_get(item, "description", "No description available"))
                        
                        # NEW: Availability for services
                        if item_type == "service":
                            availability = safe_get(item, "availability")
                            if availability:
                                st.write(f"**Availability**: {availability}")
                        
                        # Price
                        price = safe_get(item, "price", "Not specified")
                        st.write(f"**Price**: {price}")
                        
                        # Contact
                        contact = safe_get(item, "contact", "Contact information not provided")
                        st.write(f"**Contact**: {contact}")
                        
                        # Volunteers for services
                        if item_type == "service":
                            volunteers = safe_get(item, "volunteers", [])
                            st.write(f"**Volunteers**: {len(volunteers)}")
                            if st.session_state["user_uid"] not in volunteers:
                                if st.button("Join as Volunteer", key=f"join_vol_{item_id}_{idx}"):
                                    volunteers.append(st.session_state["user_uid"])
                                    db.collection("products_services").document(item_id).update({"volunteers": volunteers})
                                    st.success("You're now a volunteer")
                                    st.rerun()
                            else:
                                st.info("You're already volunteering for this service")
                        
                        # NEW: Reviews for products
                        if item_type == "product":
                            reviews = safe_get(item, "reviews", [])
                            with st.expander(f"Reviews ({len(reviews)})"):
                                if reviews:
                                    for review in reviews:
                                        st.write(f"**{safe_get(review, 'user', 'Anonymous')}** ⭐ {safe_get(review, 'rating', 0)}")
                                        st.write(safe_get(review, "comment", ""))
                                        st.markdown("---")
                                else:
                                    st.info("No reviews yet")
                            
                            # Add review
                            if st.session_state["user_uid"] not in [r.get("user_id") for r in reviews]:
                                with st.form(key=f"review_form_{item_id}"):
                                    st.subheader("Add a Review")
                                    rating = st.slider("Rating", 1, 5, 3, key=f"review_rating_{item_id}")
                                    comment = st.text_area("Comment", key=f"review_comment_{item_id}")
                                    if st.form_submit_button("Submit Review"):
                                        new_review = {
                                            "user": st.session_state["email"],
                                            "user_id": st.session_state["user_uid"],
                                            "rating": rating,
                                            "comment": comment,
                                            "timestamp": datetime.datetime.utcnow()
                                        }
                                        db.collection("products_services").document(item_id).update({
                                            "reviews": firestore.ArrayUnion([new_review])
                                        })
                                        st.success("Review submitted")
                                        st.rerun()
                        
                        # Owner controls
                        if safe_get(item, "createdBy") == st.session_state["user_uid"]:
                            if st.button("Delete", key=f"delete_{item_id}_{idx}", type="secondary"):
                                delete_product(item_id)
                                st.success("Item deleted")
                                st.rerun()
                        
                        st.markdown("</div>", unsafe_allow_html=True)
                        st.markdown("---")

# NEW: User Profile Page
elif st.session_state.current_page == "My Profile":
    st.header("My Profile")
    
    # Get user profile
    profile = get_user_profile(st.session_state["user_uid"]) or {}
    
    # Profile form
    with st.form(key="profile_form"):
        display_name = st.text_input("Display Name", value=profile.get("display_name", ""))
        bio = st.text_area("Bio", value=profile.get("bio", ""))
        skills = st.text_area("Skills (comma separated)", value=", ".join(profile.get("skills", [])))
        contact_info = st.text_area("Contact Information", value=profile.get("contact_info", ""))
        profile_image = st.file_uploader("Profile Image", type=["png", "jpg", "jpeg"])
        
        if st.form_submit_button("Save Profile"):
            profile_data = {
                "display_name": display_name,
                "bio": bio,
                "skills": [s.strip() for s in skills.split(",") if s.strip()],
                "contact_info": contact_info,
                "last_updated": datetime.datetime.utcnow()
            }
            
            # Upload profile image if provided
            if profile_image:
                image_url = upload_image_to_firebase(profile_image)
                if image_url:
                    profile_data["profile_image"] = image_url
            
            update_user_profile(st.session_state["user_uid"], profile_data)
            st.success("Profile saved successfully")
            st.rerun()
    
    # Display profile
    if profile:
        st.subheader("Your Profile")
        col1, col2 = st.columns([1, 3])
        with col1:
            if "profile_image" in profile:
                st.image(profile["profile_image"], width=150)
            else:
                st.info("No profile image")
        with col2:
            st.write(f"**Name:** {profile.get('display_name', 'Not set')}")
            st.write(f"**Email:** {st.session_state['email']}")
            st.write(f"**Bio:** {profile.get('bio', 'Not set')}")
            if "skills" in profile and profile["skills"]:
                st.write("**Skills:**")
                for skill in profile["skills"]:
                    st.markdown(f'<span class="tag">{skill}</span>', unsafe_allow_html=True)
            if "contact_info" in profile:
                st.write(f"**Contact:** {profile['contact_info']}")

# NEW: Bookmarks Page
elif st.session_state.current_page == "Bookmarks":
    st.header("Your Bookmarked Projects")
    
    posts = get_all_posts()
    bookmarked_posts = [p for p in posts if st.session_state["user_uid"] in safe_get(p[1], "bookmarks", [])]
    
    if not bookmarked_posts:
        st.info("You haven't bookmarked any projects yet")
    for post_id, post in bookmarked_posts:
        title = safe_get(post, 'title', 'Untitled Project')
        team_size = len(safe_get(post, 'team', []))
        status = safe_get(post, 'status', 'Active')
        
        with st.expander(f"{title} - Team: {team_size} members | Status: {status}"):
            st.write(safe_get(post, "description", "No description available")[:200] + "...")
            st.caption(f"Created by: {safe_get(post, 'createdBy', 'Unknown')}")
            
            if st.button("View Project", key=f"view_{post_id}"):
                st.session_state.current_page = "Project Ideas"
                st.experimental_set_query_params(project=post_id)
                st.rerun()
            
            if st.button("Remove Bookmark", key=f"remove_bookmark_{post_id}"):
                toggle_bookmark(post_id, st.session_state["user_uid"])
                st.rerun()

# NEW: Notifications Page
elif st.session_state.current_page == "Notifications":
    st.header("Your Notifications")
    
    doc = db.collection("notifications").document(st.session_state["user_uid"]).get()
    notifications = []
    if doc.exists:
        notifications = safe_get(doc.to_dict(), "items", [])
    
    # Reset notification count
    st.session_state.notification_count = 0
    
    if not notifications:
        st.info("You have no notifications")
    for i, notification in enumerate(notifications):
        read_class = "read" if notification.get("read", False) else "unread"
        with st.container():
            st.markdown(f"<div class='notification {read_class}'>", unsafe_allow_html=True)
            col1, col2 = st.columns([8, 1])
            with col1:
                st.write(f"**{notification.get('message', '')}**")
                st.caption(notification.get("timestamp").strftime("%Y-%m-%d %H:%M"))
            with col2:
                if not notification.get("read", False):
                    if st.button("✓", key=f"mark_read_{i}"):
                        mark_notification_read(st.session_state["user_uid"], i)
                        st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
            st.markdown("---")

# Rules Page
elif st.session_state.current_page == "Rules":
    st.header("Community Guidelines")
    st.markdown("""
    <div style="background: white; border-radius: 10px; padding: 20px; margin: 20px 0; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
        <ul style="font-size: 1.1rem;">
            <li style="margin: 10px 0;"><strong>Respect others</strong>: Treat all community members with courtesy</li>
            <li style="margin: 10px 0;"><strong>No spamming</strong>: Keep content relevant and valuable</li>
            <li style="margin: 10px 0;"><strong>Meaningful participation</strong>: Join teams only if you can contribute</li>
            <li style="margin: 10px 0;"><strong>Verify information</strong>: Ensure accuracy before sharing</li>
            <li style="margin: 10px 0;"><strong>Protect intellectual property</strong>: Always credit sources</li>
            <li style="margin: 10px 0;"><strong>Report issues</strong>: Notify admins of any problems or violations</li>
            <li style="margin: 10px 0;"><strong>Quality contributions</strong>: Maintain high standards for products and services</li>
            <li style="margin: 10px 0;"><strong>Respect deadlines</strong>: Communicate proactively if you can't meet commitments</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    st.info("These guidelines help maintain a productive and respectful environment for everyone.")

# Stats Page
elif st.session_state.current_page == "Stats":
    st.header("Platform Statistics")
    total_ideas, total_products, total_services, total_users = count_total_stats()
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""
        <div class="stats-card">
            <h3>Total Ideas</h3>
            <div class="value">{total_ideas}</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <div class="stats-card">
            <h3>Products</h3>
            <div class="value">{total_products}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="stats-card">
            <h3>Services</h3>
            <div class="value">{total_services}</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <div class="stats-card">
            <h3>Registered Users</h3>
            <div class="value">{total_users}</div>
        </div>
        """, unsafe_allow_html=True)
    
    # NEW: Activity chart with real data
    st.subheader("Project Activity Timeline")
    posts = db.collection("posts").stream()
    timeline_data = []
    for post in posts:
        data = post.to_dict()
        timeline_data.append({
            "Project": safe_get(data, "title", "Untitled"),
            "Start": safe_get(data, "createdAt"),
            "End": safe_get(data, "deadline"),
            "Status": safe_get(data, "status", "Unknown")
        })
    
    if timeline_data:
        df = pd.DataFrame(timeline_data)
        fig = px.timeline(df, x_start="Start", x_end="End", y="Project", color="Status",
                          title="Project Timeline", color_discrete_map={
                              "Planning": "blue",
                              "In Progress": "orange",
                              "Testing": "purple",
                              "Completed": "green",
                              "On Hold": "gray"
                          })
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No project data available for timeline")
    
    # NEW: Skills distribution chart
    st.subheader("Most Needed Skills")
    all_skills = []
    posts = db.collection("posts").stream()
    for post in posts:
        data = post.to_dict()
        all_skills.extend(safe_get(data, "skills_needed", []))
    
    if all_skills:
        skill_counts = pd.Series(all_skills).value_counts().head(10)
        fig = px.bar(skill_counts, x=skill_counts.values, y=skill_counts.index, 
                     orientation='h', title="Top 10 Skills in Demand")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No skills data available")

# Admin Page
elif st.session_state.current_page == "Admin":
    st.header("Administration Panel")
    st.warning("You have administrative privileges on this platform")
    
    # Create tabs for different admin functions
    admin_tabs = st.tabs(["Project Ideas", "Products & Services", "User Management", "Platform Analytics"])
    
    # Tab 1: Project Ideas Management
    with admin_tabs[0]:
        st.subheader("All Project Ideas")
        all_ideas = db.collection("posts").order_by("createdAt", direction=firestore.Query.DESCENDING).stream()
        idea_count = 0
        
        for idea in all_ideas:
            idea_count += 1
            data = idea.to_dict()
            with st.container():
                st.markdown(f"**{safe_get(data, 'title', 'Untitled Project')}**")
                st.caption(f"Created by: {safe_get(data, 'createdBy', 'Unknown')} | Team members: {len(safe_get(data, 'team', []))}")
                st.write(safe_get(data, "description", "No description available")[:200] + "...")
                
                deadline = safe_get(data, "deadline")
                if deadline:
                    st.write(f"**Deadline**: {deadline}")
                
                # Delete button for each idea
                if st.button("Delete Idea", key=f"del_idea_{idea.id}", type="secondary"):
                    db.collection("posts").document(idea.id).delete()
                    st.success("Idea deleted")
                    st.rerun()
                
                st.markdown("---")
        
        if idea_count == 0:
            st.info("No project ideas found")
            
        # Upload new idea as admin
        st.subheader("Create New Idea (Admin)")
        admin_title = st.text_input("Idea Title", key="admin_title")
        admin_desc = st.text_area("Description", key="admin_desc")
        if st.button("Post Idea as Admin", key="admin_post_idea_button"):
            if admin_title and admin_desc:
                post_idea(admin_title, admin_desc, "admin", str(datetime.date.today()), [], "admin@example.com")
                st.success("Admin idea posted")
                st.rerun()
    
    # Tab 2: Products & Services Management
    with admin_tabs[1]:
        st.subheader("All Products & Services")
        all_items = db.collection("products_services").order_by("createdAt", direction=firestore.Query.DESCENDING).stream()
        item_count = 0
        
        # Filter options
        filter_type = st.selectbox("Filter by Type", ["All", "Products", "Services"], key="admin_items_filter")
        
        for item in all_items:
            data = item.to_dict()
            item_type = safe_get(data, "type", "unknown")
            
            # Apply filter
            if filter_type == "Products" and item_type != "product":
                continue
            if filter_type == "Services" and item_type != "service":
                continue
                
            item_count += 1
            with st.container():
                st.markdown(f"**{safe_get(data, 'title', 'Untitled Item')}**")
                st.caption(f"Type: {item_type} | Created by: {safe_get(data, 'createdBy', 'Unknown')}")
                st.write(safe_get(data, "description", "No description available")[:200] + "...")
                
                # FIXED: Robust image display with error handling
                image_url = safe_get(data, "image_url")
                if image_url:
                    try:
                        st.image(image_url, width=200)
                    except Exception as e:
                        st.warning("Image unavailable or failed to load")
                else:
                    st.info("No image available for this item")
                
                # Delete button for each item
                if st.button("Delete Item", key=f"del_item_{item.id}", type="secondary"):
                    db.collection("products_services").document(item.id).delete()
                    st.success("Item deleted")
                    st.rerun()
                
                st.markdown("---")
        
        if item_count == 0:
            st.info("No products or services found")
            
        # Upload new product/service as admin
        st.subheader("Create New Item (Admin)")
        admin_item_type = st.selectbox("Item Type", ["product", "service"], key="admin_item_type")
        admin_item_title = st.text_input("Item Name", key="admin_item_title")
        admin_item_desc = st.text_area("Description", key="admin_item_desc")
        admin_item_price = st.text_input("Price", key="admin_item_price")
        admin_item_contact = st.text_input("Contact Information", key="admin_item_contact")
        admin_item_image = st.file_uploader("Item Image (optional)", type=["png", "jpg", "jpeg"], key="admin_item_image")
        
        if st.button("Submit as Admin", key="admin_submit_item_button"):
            if admin_item_title and admin_item_desc and admin_item_contact and admin_item_price:
                image_url = upload_image_to_firebase(admin_item_image) if admin_item_image else None
                db.collection("products_services").add({
                    "team_id": "admin",
                    "team_title": "Admin Team",
                    "type": admin_item_type,
                    "title": admin_item_title,
                    "description": admin_item_desc,
                    "price": admin_item_price,
                    "contact": admin_item_contact,
                    "image_url": image_url,
                    "createdBy": "admin",
                    "createdAt": datetime.datetime.utcnow(),
                    "volunteers": []
                })
                st.success("Item submitted as admin")
                st.rerun()
    
    # Tab 3: User Management
    with admin_tabs[2]:
        st.subheader("User Management")
        
        # Search users
        search_query = st.text_input("Search users by email", key="user_search")
        
        users_ref = db.collection("profiles").stream()
        users = []
        for user in users_ref:
            user_data = user.to_dict()
            user_data["id"] = user.id
            users.append(user_data)
        
        if search_query:
            search_lower = search_query.lower()
            users = [u for u in users if search_lower in u.get("email", "").lower()]
        
        if not users:
            st.info("No users found")
        for user in users:
            with st.container():
                st.markdown(f"**{user.get('display_name', 'No name')}**")
                st.caption(f"ID: {user['id']} | Email: {user.get('email', 'No email')}")
                
                if "skills" in user and user["skills"]:
                    st.write("**Skills:**")
                    for skill in user["skills"]:
                        st.markdown(f'<span class="tag">{skill}</span>', unsafe_allow_html=True)
                
                if st.button("View Profile", key=f"view_user_{user['id']}"):
                    st.session_state.view_user_id = user["id"]
                
                # NEW: User suspension
                if st.button("Suspend User", key=f"suspend_{user['id']}", type="secondary"):
                    db.collection("suspended_users").document(user["id"]).set({
                        "suspended_at": datetime.datetime.utcnow(),
                        "reason": "Admin suspension"
                    })
                    st.success("User suspended")
                    st.rerun()
                
                st.markdown("---")
    
    # NEW: Tab 4: Platform Analytics
    with admin_tabs[3]:
        st.subheader("Platform Analytics")
        
        # User growth chart
        st.write("### User Growth Over Time")
        users_ref = db.collection("profiles").order_by("createdAt").stream()
        user_counts = []
        current_count = 0
        for user in users_ref:
            current_count += 1
            user_data = user.to_dict()
            user_counts.append({
                "Date": user_data.get("createdAt", datetime.datetime.utcnow()),
                "Users": current_count
            })
        
        if user_counts:
            df = pd.DataFrame(user_counts)
            fig = px.line(df, x="Date", y="Users", title="User Growth Over Time")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No user data available")
        
        # Project status distribution
        st.write("### Project Status Distribution")
        posts = db.collection("posts").stream()
        status_counts = defaultdict(int)
        for post in posts:
            data = post.to_dict()
            status = data.get("status", "Unknown")
            status_counts[status] += 1
        
        if status_counts:
            df = pd.DataFrame({
                "Status": list(status_counts.keys()),
                "Count": list(status_counts.values())
            })
            fig = px.pie(df, values='Count', names='Status', title='Project Status Distribution')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No project data available")

st.markdown('</div>', unsafe_allow_html=True)
