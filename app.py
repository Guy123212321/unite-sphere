import datetime
import streamlit as st
import requests  # gotta have this for making API calls
import json
import firebase_admin
from firebase_admin import credentials, firestore

# Only set up Firebase once, no need to keep re-initializing it every time
if not firebase_admin._apps:
    # grab the Firebase service account info from Streamlit secrets (keep it safe!)
    service_account_json = st.secrets["FIREBASE_SERVICE_ACCOUNT"]
    key_dict = json.loads(service_account_json)  # convert from string to dict
    cred = credentials.Certificate(key_dict)
    firebase_admin.initialize_app(cred)

db = firestore.client()  # connect to Firestore database
FIREBASE_API_KEY = st.secrets["FIREBASE_API_KEY"]  # grab API key from secrets

# Sign up a new user with email and password
def signup(email, password):
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={FIREBASE_API_KEY}"
    payload = {
        "email": email,
        "password": password,
        "returnSecureToken": True
    }
    return requests.post(url, json=payload).json()

# Log in an existing user
def login(email, password):
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_API_KEY}"
    payload = {"email": email, "password": password, "returnSecureToken": True}
    return requests.post(url, json=payload).json()

# Send a verification email after signup so user can confirm their email
def send_verification_email(id_token):
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:sendOobCode?key={FIREBASE_API_KEY}"
    return requests.post(url, json={"requestType": "VERIFY_EMAIL", "idToken": id_token}).json()

# Check if the user's email is verified or not (important!)
def check_email_verified(id_token):
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:lookup?key={FIREBASE_API_KEY}"
    res = requests.post(url, json={"idToken": id_token}).json()
    return res.get("users", [{}])[0].get("emailVerified", False)

# Add a new idea post to Firestore
def post_idea(title, description, user_uid):
    db.collection("posts").add({
        "title": title,
        "description": description,
        "createdAt": datetime.datetime.utcnow(),
        "createdBy": user_uid,
        "team": [user_uid]  # creator automatically joins the team
    })

# Grab all idea posts from Firestore, newest first
def get_all_posts():
    posts = db.collection("posts").order_by("createdAt", direction=firestore.Query.DESCENDING).stream()
    return [(doc.id, doc.to_dict()) for doc in posts]

# Let a user join a team for a given post
def join_team(post_id, user_uid):
    ref = db.collection("posts").document(post_id)
    doc = ref.get()
    if doc.exists:
        data = doc.to_dict()
        if user_uid not in data["team"]:
            data["team"].append(user_uid)
            ref.update({"team": data["team"]})

# Streamlit app UI starts here
st.set_page_config(page_title="Unite Sphere", layout="centered")
st.title("TeamUp - Build Teams on Ideas")

# If the user isn't logged in yet, show login/signup options
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
                        # logged in and email is verified - yay!
                        st.session_state["id_token"] = res["idToken"]
                        st.session_state["email"] = email
                        st.session_state["user_uid"] = res["localId"]
                        st.success("You're in!")
                        st.experimental_rerun()  # <--- ONLY here
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
                    # no rerun here because user must verify email first
                else:
                    st.error("Sign up didn't go through. Try again?")

# If logged in, show main menu and features
else:
    st.sidebar.write(f"Logged in as: {st.session_state['email']}")
    if st.sidebar.button("Logout"):
        st.session_state.clear()
        st.experimental_rerun()  # <--- ONLY here

    menu = st.sidebar.selectbox("Menu", ["Home", "Submit Idea", "Rules"])

    if menu == "Home":
        st.header("Ideas List")

        # Initialize a flag to track which post user wants to join
        if "join_post_id" not in st.session_state:
            st.session_state["join_post_id"] = None

        for post_id, post in get_all_posts():
            with st.expander(post["title"]):
                st.write(post["description"])
                st.write(f"Team Members: {len(post['team'])}")

                if st.session_state["user_uid"] not in post["team"]:
                    if st.button("Join Team", key=f"join_{post_id}"):
                        st.session_state["join_post_id"] = post_id

        # After rendering all posts, check if user clicked to join a team
        if st.session_state["join_post_id"]:
            join_team(st.session_state["join_post_id"], st.session_state["user_uid"])
            st.success("You joined this team!")
            st.session_state["join_post_id"] = None  # reset flag
            st.experimental_rerun()

    elif menu == "Submit Idea":
        st.header("Got an Idea?")
        title = st.text_input("Idea Title")
        description = st.text_area("What's it about?")
        if st.button("Post"):
            if title and description:
                post_idea(title, description, st.session_state["user_uid"])
                st.success("Your idea is posted!")
                st.experimental_rerun()  # <--- ONLY here
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
