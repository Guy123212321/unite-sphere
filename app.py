import datetime
import streamlit as st
import requests  # for API calls
import json
import firebase_admin
from firebase_admin import credentials, firestore

# Initialize Firebase Admin only once
if not firebase_admin._apps:
    # Grab Firebase service account JSON from secrets (make sure it's correctly formatted!)
    service_account_json = st.secrets["FIREBASE_SERVICE_ACCOUNT"]
    key_dict = json.loads(service_account_json)
    cred = credentials.Certificate(key_dict)
    firebase_admin.initialize_app(cred)

db = firestore.client()
FIREBASE_API_KEY = st.secrets["FIREBASE_API_KEY"]

# Signup function
def signup(email, password):
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={FIREBASE_API_KEY}"
    payload = {"email": email, "password": password, "returnSecureToken": True}
    return requests.post(url, json=payload).json()

# Login function
def login(email, password):
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_API_KEY}"
    payload = {"email": email, "password": password, "returnSecureToken": True}
    return requests.post(url, json=payload).json()

# Send email verification link
def send_verification_email(id_token):
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:sendOobCode?key={FIREBASE_API_KEY}"
    return requests.post(url, json={"requestType": "VERIFY_EMAIL", "idToken": id_token}).json()

# Check if user’s email is verified
def check_email_verified(id_token):
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:lookup?key={FIREBASE_API_KEY}"
    res = requests.post(url, json={"idToken": id_token}).json()
    return res.get("users", [{}])[0].get("emailVerified", False)

# Add a new idea post
def post_idea(title, description, user_uid):
    db.collection("posts").add({
        "title": title,
        "description": description,
        "createdAt": datetime.datetime.utcnow(),
        "createdBy": user_uid,
        "team": [user_uid]
    })

# Get all posts sorted by newest first
def get_all_posts():
    posts = db.collection("posts").order_by("createdAt", direction=firestore.Query.DESCENDING).stream()
    return [(doc.id, doc.to_dict()) for doc in posts]

# Add user to the team of a post
def join_team(post_id, user_uid):
    ref = db.collection("posts").document(post_id)
    doc = ref.get()
    if doc.exists:
        data = doc.to_dict()
        if user_uid not in data.get("team", []):
            data["team"].append(user_uid)
            ref.update({"team": data["team"]})

# UI setup
st.set_page_config(page_title="Unite Sphere", layout="centered")
st.title("TeamUp - Build Teams on Ideas")

# Login/signup UI
if "id_token" not in st.session_state:
    st.subheader("Login or Sign Up")
    tab1, tab2 = st.tabs(["Login", "Sign Up"])

    with tab1:
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_password")
        if st.button("Login"):
            if not email or not password:
                st.warning("Hey, don't forget to enter your email and password!")
            else:
                res = login(email, password)
                if "idToken" in res:
                    if check_email_verified(res["idToken"]):
                        st.session_state["id_token"] = res["idToken"]
                        st.session_state["email"] = email
                        st.session_state["user_uid"] = res["localId"]
                        st.success("You're in!")
                        st.experimental_rerun()
                    else:
                        st.warning("Looks like you haven't verified your email yet.")
                else:
                    st.error("Hmm, login failed. Double-check your credentials?")

    with tab2:
        email = st.text_input("Email", key="signup_email")
        password = st.text_input("Password", type="password", key="signup_password")
        if st.button("Sign Up"):
            if not email or not password:
                st.warning("You gotta enter both email and password to sign up.")
            else:
                res = signup(email, password)
                if "idToken" in res:
                    send_verification_email(res["idToken"])
                    st.success("Almost done! Check your email for the verification link.")
                else:
                    st.error("Sign up didn't go through. Try again?")

# Main app UI after login
else:
    st.sidebar.write(f"Logged in as: {st.session_state['email']}")
    if st.sidebar.button("Logout"):
        st.session_state.clear()
        st.experimental_rerun()

    menu = st.sidebar.selectbox("Menu", ["Home", "Submit Idea", "Rules"])

    if menu == "Home":
        st.header("Ideas List")
        for post_id, post in get_all_posts():
            with st.expander(post["title"]):
                st.write(post["description"])
                st.write(f"Team Members: {len(post.get('team', []))}")
                if st.session_state["user_uid"] not in post.get("team", []):
                    if st.button("Join Team", key=post_id):
                        join_team(post_id, st.session_state["user_uid"])
                        st.success("You joined this team!")
                        st.experimental_rerun()

    elif menu == "Submit Idea":
        st.header("Got an Idea?")
        title = st.text_input("Idea Title")
        description = st.text_area("What's it about?")
        if st.button("Post"):
            if title and description:
                post_idea(title, description, st.session_state["user_uid"])
                st.success("Your idea is posted!")
                st.experimental_rerun()
            else:
                st.warning("Make sure to fill both the title and description!")

    elif menu == "Rules":
        st.header("Rules")
        st.markdown("""
        - Be respectful to others  
        - No spamming please  
        - Don’t just join random teams for no reason  
        - If you join a team, try to stay active
        """)

