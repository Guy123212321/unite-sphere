import streamlit as st
import datetime
import requests
import json
import firebase_admin
from firebase_admin import credentials, firestore

# Set page layout
st.set_page_config(page_title="Unite Sphere", layout="centered")

# Initialize session flags only once
if "rerun_now" not in st.session_state:
    st.session_state["rerun_now"] = False

# Firebase setup - make sure it's initialized once
if not firebase_admin._apps:
    service_account_json = st.secrets["FIREBASE_SERVICE_ACCOUNT"]
    key_dict = json.loads(service_account_json)
    cred = credentials.Certificate(key_dict)
    firebase_admin.initialize_app(cred)

# Set up Firestore client and API key
db = firestore.client()
FIREBASE_API_KEY = st.secrets["FIREBASE_API_KEY"]

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

# Firestore post functions
def post_idea(title, description, user_uid):
    db.collection("posts").add({
        "title": title,
        "description": description,
        "createdAt": datetime.datetime.utcnow(),
        "createdBy": user_uid,
        "team": [user_uid]
    })

def update_idea(post_id, new_title, new_description):
    db.collection("posts").document(post_id).update({
        "title": new_title,
        "description": new_description
    })

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

# UI
st.title("Unite Sphere - Build Teams on Ideas")

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
                        st.session_state["rerun_now"] = True
                        st.stop()  # stop before rerun
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

else:
    st.sidebar.write(f"Logged in as: {st.session_state['email']}")
    if st.sidebar.button("Logout"):
        st.session_state.clear()
        st.session_state["rerun_now"] = True
        st.stop()  # stop before rerun

    menu = st.sidebar.selectbox("Menu", ["Home", "Submit Idea", "Team Chat", "Rules"])

    if menu == "Home":
        st.header("Ideas List")
        for post_id, post in get_all_posts():
            with st.expander(post["title"]):
                st.write(post["description"])
                st.write(f"Team Members: {len(post['team'])}")
                if st.session_state["user_uid"] not in post["team"]:
                    if st.button("Join Team", key=post_id):
                        join_team(post_id, st.session_state["user_uid"])
                        st.success("You joined this team!")
                        st.session_state["rerun_now"] = True
                        st.stop()
                if post["createdBy"] == st.session_state["user_uid"]:
                    new_title = st.text_input("Edit Title", value=post["title"], key=f"title_{post_id}")
                    new_desc = st.text_area("Edit Description", value=post["description"], key=f"desc_{post_id}")
                    if st.button("Update Idea", key=f"update_{post_id}"):
                        update_idea(post_id, new_title, new_desc)
                        st.success("Idea updated!")
                        st.session_state["rerun_now"] = True
                        st.stop()
                    if st.button("Delete Idea", key=f"delete_{post_id}"):
                        delete_idea(post_id)
                        st.success("Idea deleted!")
                        st.session_state["rerun_now"] = True
                        st.stop()

    elif menu == "Submit Idea":
        st.header("Got an Idea?")
        title = st.text_input("Idea Title")
        description = st.text_area("What's it about?")
        if st.button("Post"):
            if title and description:
                post_idea(title, description, st.session_state["user_uid"])
                st.success("Your idea is posted!")
                st.session_state["rerun_now"] = True
                st.stop()
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

    elif menu == "Team Chat":
        st.header("Team Chat 💬")
        user_posts = [(pid, p["title"]) for pid, p in get_all_posts() if st.session_state["user_uid"] in p["team"]]

        if not user_posts:
            st.info("You're not in any team yet! Join a team to chat.")
        else:
            selected = st.selectbox("Choose a team to chat in:", user_posts, format_func=lambda x: x[1], key="chat_team_select")
            selected_post_id, selected_title = selected

            st.subheader(f"Chat Room for: {selected_title}")
            chat_ref = db.collection("posts").document(selected_post_id).collection("chat")

            chat_messages = list(chat_ref.order_by("timestamp", direction=firestore.Query.ASCENDING).stream())
            for msg in chat_messages:
                msg_data = msg.to_dict()
                sender = msg_data.get("sender", "Unknown")
                content = msg_data.get("message", "")
                st.markdown(f"**{sender}**: {content}")
                if sender == st.session_state["email"]:
                    if st.button("Delete", key=f"del_{msg.id}"):
                        chat_ref.document(msg.id).delete()
                        st.success("Message deleted!")
                        st.experimental_rerun()

            st.markdown("---")
            new_msg = st.text_input("Your message", key=f"chat_input_{selected_post_id}")
            send = st.button("Send Message", key=f"send_button_{selected_post_id}")
            if send and new_msg.strip():
                chat_ref.add({
                    "sender": st.session_state["email"],
                    "message": new_msg.strip(),
                    "timestamp": datetime.datetime.utcnow()
                })
                st.success("Sent! Scroll to see your message.")
                st.session_state["rerun_now"] = True
                st.stop()
