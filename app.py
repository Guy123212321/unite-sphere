import streamlit as st
import datetime
import requests
import json
import firebase_admin
from firebase_admin import credentials, firestore

# Config
st.set_page_config(page_title="Unite Sphere", layout="centered")

# Firebase init
if not firebase_admin._apps:
    cred = credentials.Certificate(json.loads(st.secrets["FIREBASE_SERVICE_ACCOUNT"]))
    firebase_admin.initialize_app(cred)

db = firestore.client()
FIREBASE_API_KEY = st.secrets["FIREBASE_API_KEY"]

# Firebase Auth
def signup(email, password):
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={FIREBASE_API_KEY}"
    return requests.post(url, json={"email": email, "password": password, "returnSecureToken": True}).json()

def login(email, password):
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_API_KEY}"
    return requests.post(url, json={"email": email, "password": password, "returnSecureToken": True}).json()

def send_verification_email(id_token):
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:sendOobCode?key={FIREBASE_API_KEY}"
    return requests.post(url, json={"requestType": "VERIFY_EMAIL", "idToken": id_token}).json()

def check_email_verified(id_token):
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:lookup?key={FIREBASE_API_KEY}"
    res = requests.post(url, json={"idToken": id_token}).json()
    return res.get("users", [{}])[0].get("emailVerified", False)

# Post Functions
def post_idea(title, desc, uid):
    db.collection("posts").add({
        "title": title,
        "description": desc,
        "createdAt": datetime.datetime.utcnow(),
        "createdBy": uid,
        "team": [uid]
    })

def get_all_posts():
    posts = db.collection("posts").order_by("createdAt", direction=firestore.Query.DESCENDING).stream()
    return [(doc.id, doc.to_dict()) for doc in posts]

def update_idea(pid, title, desc):
    db.collection("posts").document(pid).update({"title": title, "description": desc})

def delete_idea(pid):
    db.collection("posts").document(pid).delete()

def join_team(pid, uid):
    ref = db.collection("posts").document(pid)
    doc = ref.get()
    if doc.exists:
        team = doc.to_dict().get("team", [])
        if uid not in team:
            team.append(uid)
            ref.update({"team": team})

# Header / Login Sidebar
st.title("Unite Sphere")

if "id_token" not in st.session_state:
    menu = st.sidebar.radio("Login / Sign Up", ["Login", "Sign Up"])
    email = st.sidebar.text_input("Email")
    password = st.sidebar.text_input("Password", type="password")

    if menu == "Login":
        if st.sidebar.button("Login"):
            if email and password:
                res = login(email, password)
                if "idToken" in res:
                    if check_email_verified(res["idToken"]):
                        st.session_state["id_token"] = res["idToken"]
                        st.session_state["email"] = email
                        st.session_state["user_uid"] = res["localId"]
                        st.success("You're logged in!")
                        st.experimental_rerun()
                    else:
                        st.warning("Verify your email before logging in.")
                else:
                    st.error("Invalid credentials.")
    else:
        if st.sidebar.button("Sign Up"):
            if email and password:
                res = signup(email, password)
                if "idToken" in res:
                    send_verification_email(res["idToken"])
                    st.success("Check your email to verify.")
                else:
                    st.error("Sign-up failed.")
    
    st.info("Log in to access full features.")

else:
    st.sidebar.success(f"Logged in as {st.session_state['email']}")
    if st.sidebar.button("Logout"):
        st.session_state.clear()
        st.experimental_rerun()

    menu = st.sidebar.selectbox("Menu", ["Home", "Submit Idea", "Team Chat", "Rules"])

    if menu == "Home":
        st.header("Ideas")
        for post_id, post in get_all_posts():
            with st.expander(post["title"]):
                st.write(post["description"])
                st.write(f"Team Members: {len(post['team'])}")
                for uid in post["team"]:
                    st.markdown(f"- {uid}")
                if st.session_state["user_uid"] not in post["team"]:
                    if st.button("Join Team", key=f"join_{post_id}"):
                        join_team(post_id, st.session_state["user_uid"])
                        st.success("Joined team!")
                        st.experimental_rerun()
                if post["createdBy"] == st.session_state["user_uid"]:
                    new_title = st.text_input("Edit Title", value=post["title"], key=f"edit_title_{post_id}")
                    new_desc = st.text_area("Edit Desc", value=post["description"], key=f"edit_desc_{post_id}")
                    if st.button("Update", key=f"update_{post_id}"):
                        update_idea(post_id, new_title, new_desc)
                        st.success("Idea updated.")
                        st.experimental_rerun()
                    if st.button("Delete", key=f"del_{post_id}"):
                        delete_idea(post_id)
                        st.warning("Idea deleted.")
                        st.experimental_rerun()

    elif menu == "Submit Idea":
        st.header("Submit Your Idea")
        title = st.text_input("Title")
        desc = st.text_area("Description")
        if st.button("Post"):
            if title and desc:
                post_idea(title, desc, st.session_state["user_uid"])
                st.success("Idea posted!")
                st.experimental_rerun()
            else:
                st.warning("Both fields required.")

    elif menu == "Team Chat":
        st.header("Team Chat 💬")
        user_teams = [(pid, p["title"]) for pid, p in get_all_posts() if st.session_state["user_uid"] in p["team"]]

        if not user_teams:
            st.info("You're not in any teams.")
        else:
            selected = st.selectbox("Select Team", user_teams, format_func=lambda x: x[1])
            selected_post_id, selected_title = selected
            st.subheader(f"Chat - {selected_title}")
            chat_ref = db.collection("posts").document(selected_post_id).collection("chat")

            team_doc = db.collection("posts").document(selected_post_id).get()
            team_data = team_doc.to_dict().get("team", []) if team_doc.exists else []
            st.markdown("**Team Members:**")
            for member in team_data:
                st.markdown(f"- {member}")

            messages = list(chat_ref.order_by("timestamp", direction=firestore.Query.ASCENDING).stream())
            for msg in messages:
                msg_data = msg.to_dict()
                sender = msg_data.get("sender", "Unknown")
                text = msg_data.get("message", "")
                st.markdown(f"**{sender}**: {text}")
                if sender == st.session_state["email"]:
                    if st.button("Delete", key=f"del_{msg.id}"):
                        chat_ref.document(msg.id).delete()
                        st.experimental_rerun()

            new_msg = st.text_input("Your message", key=f"msg_input_{selected_post_id}")
            if st.button("Send", key=f"send_{selected_post_id}") and new_msg.strip():
                chat_ref.add({
                    "sender": st.session_state["email"],
                    "message": new_msg.strip(),
                    "timestamp": datetime.datetime.utcnow()
                })
                st.success("Sent.")
                st.experimental_rerun()

    elif menu == "Rules":
        st.header("Platform Rules")
        st.markdown("""
        - Be respectful to others  
        - No spamming  
        - Only join teams you want to contribute to  
        - Stay active if you're in a team  
        """)
