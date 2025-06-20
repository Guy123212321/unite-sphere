import streamlit as st
import datetime
import requests
import json
import firebase_admin
from firebase_admin import credentials, firestore, storage
import uuid
import base64
from google.cloud import storage as gcs
from collections import defaultdict

# Page Config
st.set_page_config(page_title="UniteSphere", layout="centered", page_icon="🤝")

# Custom CSS for enhanced UI
st.markdown(
    """
    <style>
    /* Background */
    .main {
        background-color: #121212;
        color: #e0e0e0;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        padding: 15px 30px;
    }
    /* Headers */
    h1, h2, h3 {
        color: #00ffe7;
        font-family: 'Arial Black', Gadget, sans-serif;
    }
    /* Buttons */
    div.stButton > button {
        background: linear-gradient(45deg, #00ffa2 0%, #00e1ff 100%);
        color: #121212;
        font-weight: bold;
        border-radius: 10px;
        padding: 8px 20px;
        box-shadow: 0 4px 8px rgba(0,255,255,0.4);
        transition: background 0.3s ease;
    }
    div.stButton > button:hover {
        background: linear-gradient(45deg, #00e1ff 0%, #00ffa2 100%);
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0,255,255,0.5);
    }
    /* Text Inputs */
    input[type="text"], input[type="password"], textarea {
        border: 2px solid #00e1ff !important;
        border-radius: 8px;
        padding: 8px;
        background-color: #222;
        color: #e0e0e0;
    }
    /* Select boxes */
    div[role="listbox"] {
        background-color: #222;
        color: #e0e0e0;
        border-radius: 8px;
        border: 2px solid #00e1ff !important;
    }
    /* Scrollbar for chat container */
    .streamlit-expanderContent {
        max-height: 300px;
        overflow-y: auto;
    }
    /* Stats cards */
    .stats-card {
        background: #1e1e1e;
        border-radius: 15px;
        padding: 20px;
        margin: 10px 0;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        border-left: 4px solid #00e1ff;
    }
    .stats-card h3 {
        color: #00ffa2;
        margin-top: 0;
    }
    .stats-card .value {
        font-size: 2.5rem;
        font-weight: bold;
        color: #00e1ff;
        text-align: center;
    }
    /* Product cards */
    .product-card {
        background: #1e1e1e;
        border-radius: 15px;
        padding: 20px;
        margin: 15px 0;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        border: 1px solid #00e1ff;
    }
    .volunteer-badge {
        background: #00b894;
        color: #121212;
        border-radius: 12px;
        padding: 2px 10px;
        font-size: 0.8rem;
        font-weight: bold;
        display: inline-block;
        margin: 5px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

def request_rerun():
    st.session_state["rerun_now"] = True
    st.experimental_rerun()

# Initialize session flags only once
if "rerun_now" not in st.session_state:
    st.session_state["rerun_now"] = False

# Firebase setup - make sure it's initialized once
if not firebase_admin._apps:
    service_account_json = st.secrets["FIREBASE_SERVICE_ACCOUNT"]
    key_dict = json.loads(service_account_json)
    cred = credentials.Certificate(key_dict)
    firebase_admin.initialize_app(cred, {
        'storageBucket': st.secrets["FIREBASE_STORAGE_BUCKET"]
    })

# Set up Firestore client and API key
db = firestore.client()
FIREBASE_API_KEY = st.secrets["FIREBASE_API_KEY"]
FIREBASE_BUCKET = storage.bucket()

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

# Firestore functions
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

def get_all_products_services():
    items = db.collection("products_services").order_by("createdAt", direction=firestore.Query.DESCENDING).stream()
    return [(doc.id, doc.to_dict()) for doc in items]

def get_user_teams(user_uid):
    posts = get_all_posts()
    return [(pid, p["title"]) for pid, p in posts if user_uid in p["team"]]

def upload_image_to_firebase(img_file):
    if img_file is not None:
        blob_name = f"products/{uuid.uuid4().hex}_{img_file.name}"
        blob = FIREBASE_BUCKET.blob(blob_name)
        blob.upload_from_file(img_file, content_type=img_file.type)
        blob.make_public()
        return blob.public_url
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
        if data.get("type") == "product":
            total_products += 1
        elif data.get("type") == "service":
            total_services += 1
    
    # Count unique users
    user_set = set()
    posts = db.collection("posts").stream()
    for post in posts:
        data = post.to_dict()
        user_set.add(data["createdBy"])
        for member in data.get("team", []):
            user_set.add(member)
    
    total_users = len(user_set)
    
    return total_ideas, total_products, total_services, total_users

# UI starts
st.markdown('<div class="main">', unsafe_allow_html=True)
st.title("🤝 UniteSphere - Build Teams on Ideas")

if "id_token" not in st.session_state:
    st.subheader("Login or Sign Up")
    tab1, tab2 = st.tabs(["Login", "Sign Up"])

    with tab1:
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_password")
        if st.button("Login", use_container_width=True):
            if not email or not password:
                st.warning("Please enter your email and password!")
            else:
                res = login(email, password)
                if "idToken" in res:
                    if check_email_verified(res["idToken"]):
                        st.session_state["id_token"] = res["idToken"]
                        st.session_state["email"] = email
                        st.session_state["user_uid"] = res["localId"]
                        st.success("Login successful!")
                        request_rerun()
                    else:
                        st.warning("Please verify your email first.")
                else:
                    st.error("Login failed. Please check your credentials.")

    with tab2:
        email = st.text_input("Email", key="signup_email")
        password = st.text_input("Password", type="password", key="signup_password")
        if st.button("Sign Up", use_container_width=True):
            if not email or not password:
                st.warning("Please enter both email and password.")
            else:
                res = signup(email, password)
                if "idToken" in res:
                    send_verification_email(res["idToken"])
                    st.success("Account created! Please check your email for verification.")
                else:
                    st.error("Sign up failed. Please try again.")

else:
    st.sidebar.write(f"👤 Logged in as: {st.session_state['email']}")
    if st.sidebar.button("Logout", use_container_width=True):
        st.session_state.clear()
        request_rerun()

    menu = st.sidebar.selectbox("Menu", ["Home", "Submit Idea", "Team Chat", "Products & Services", "Rules", "Stats"])

    if menu == "Home":
        st.header("🚀 Ideas List")
        for post_id, post in get_all_posts():
            with st.expander(f"💡 {post['title']} - Team: {len(post['team'])} members"):
                st.write(post["description"])
                st.caption(f"Created by: {post['createdBy']}")
                
                # Join team button
                if st.session_state["user_uid"] not in post["team"]:
                    if st.button("Join Team", key=f"join_{post_id}"):
                        join_team(post_id, st.session_state["user_uid"])
                        st.success("You joined this team!")
                        request_rerun()
                
                # Idea owner controls
                if post["createdBy"] == st.session_state["user_uid"]:
                    st.subheader("Manage Your Idea")
                    new_title = st.text_input("Edit Title", value=post["title"], key=f"title_{post_id}")
                    new_desc = st.text_area("Edit Description", value=post["description"], key=f"desc_{post_id}")
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("Update Idea", key=f"update_{post_id}"):
                            update_idea(post_id, new_title, new_desc)
                            st.success("Idea updated!")
                            request_rerun()
                    with col2:
                        if st.button("Delete Idea", key=f"delete_{post_id}"):
                            delete_idea(post_id)
                            st.success("Idea deleted!")
                            request_rerun()

    elif menu == "Submit Idea":
        st.header("💡 Got an Idea?")
        title = st.text_input("Idea Title")
        description = st.text_area("What's it about?")
        if st.button("Post Idea", use_container_width=True):
            if title and description:
                post_idea(title, description, st.session_state["user_uid"])
                st.success("Your idea is live!")
                request_rerun()
            else:
                st.warning("Please fill both title and description fields!")

    elif menu == "Rules":
        st.header("📜 Community Guidelines")
        st.markdown("""
        - **Be respectful** to all community members  
        - **No spamming** - keep content relevant  
        - **Join teams meaningfully** - contribute actively  
        - **Verify information** before sharing  
        - **Respect intellectual property** - credit sources  
        - **Report issues** to admins when needed  
        """)
        st.image("https://images.unsplash.com/photo-1553877522-43269d4ea984?auto=format&fit=crop&w=800", 
                caption="Together we build better ideas")

    elif menu == "Team Chat":
        st.header("💬 Team Chat")
        user_posts = [(pid, p["title"]) for pid, p in get_all_posts() if st.session_state["user_uid"] in p["team"]]

        if not user_posts:
            st.info("You're not in any team yet! Join a team to start chatting.")
        else:
            selected = st.selectbox("Choose a team to chat in:", user_posts, format_func=lambda x: x[1], key="chat_team_select")
            selected_post_id, selected_title = selected

            st.subheader(f"💬 Chat Room: {selected_title}")
            chat_ref = db.collection("posts").document(selected_post_id).collection("chat")

            # Chat messages display
            chat_container = st.container()
            with chat_container:
                chat_messages = list(chat_ref.order_by("timestamp", direction=firestore.Query.DESCENDING).limit(20).stream())
                for msg in reversed(chat_messages):
                    msg_data = msg.to_dict()
                    sender = msg_data.get("sender", "Unknown")
                    content = msg_data.get("message", "")
                    timestamp = msg_data.get("timestamp").strftime("%H:%M")
                    
                    # Different styling for current user
                    if sender == st.session_state["email"]:
                        st.markdown(f"""
                        <div style="background: #006266; padding: 10px; border-radius: 10px; margin: 5px 0; text-align: right;">
                            <div><strong>You</strong> • {timestamp}</div>
                            <div>{content}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown(f"""
                        <div style="background: #1B1464; padding: 10px; border-radius: 10px; margin: 5px 0;">
                            <div><strong>{sender}</strong> • {timestamp}</div>
                            <div>{content}</div>
                        </div>
                        """, unsafe_allow_html=True)

            # Message input
            st.markdown("---")
            new_msg = st.text_input("Type your message", key=f"chat_input_{selected_post_id}")
            col1, col2 = st.columns([1, 3])
            with col1:
                if st.button("Send", key=f"send_button_{selected_post_id}"):
                    if new_msg.strip():
                        chat_ref.add({
                            "sender": st.session_state["email"],
                            "message": new_msg.strip(),
                            "timestamp": datetime.datetime.utcnow()
                        })
                        st.success("Message sent!")
                        request_rerun()
            with col2:
                if st.button("Clear Chat", type="secondary"):
                    # This would typically require admin privileges in a real app
                    st.warning("This will delete all chat history. Admins only.")

    elif menu == "Products & Services":
        st.header("🛍️ Products & Services Hub")
        user_teams = get_user_teams(st.session_state["user_uid"])
        
        if not user_teams:
            st.info("Join or create a team first to post products or services.")
        else:
            tab_prod, tab_serv, tab_view = st.tabs(["Post Product", "Offer Service", "Browse Marketplace"])
            
            # Product Submission
            with tab_prod:
                st.subheader("🚀 Launch a Product")
                selected_team = st.selectbox("Select Team", user_teams, format_func=lambda x: x[1], key="prod_team_select")
                prod_title = st.text_input("Product Name")
                prod_desc = st.text_area("Product Description")
                prod_contact = st.text_input("Contact Info (email/phone)")
                prod_deadline = st.date_input("Target Launch Date", min_value=datetime.date.today())
                prod_image = st.file_uploader("Product Image", type=["png", "jpg", "jpeg"])
                
                if st.button("Launch Product", use_container_width=True):
                    if prod_title and prod_desc and prod_contact:
                        image_url = upload_image_to_firebase(prod_image) if prod_image else None
                        db.collection("products_services").add({
                            "team_id": selected_team[0],
                            "team_title": selected_team[1],
                            "type": "product",
                            "title": prod_title,
                            "description": prod_desc,
                            "contact": prod_contact,
                            "deadline": str(prod_deadline),
                            "image_url": image_url,
                            "createdBy": st.session_state["user_uid"],
                            "createdAt": datetime.datetime.utcnow()
                        })
                        st.success("Product launched successfully!")
                        request_rerun()
                    else:
                        st.warning("Please fill all required fields.")
            
            # Service Submission
            with tab_serv:
                st.subheader("💼 Offer a Service")
                selected_team_s = st.selectbox("Select Team", user_teams, format_func=lambda x: x[1], key="serv_team_select")
                serv_title = st.text_input("Service Name")
                serv_desc = st.text_area("Service Description")
                serv_contact = st.text_input("Contact Info (email/phone)")
                serv_deadline = st.date_input("Service Availability", min_value=datetime.date.today())
                
                if st.button("Offer Service", use_container_width=True):
                    if serv_title and serv_desc and serv_contact:
                        db.collection("products_services").add({
                            "team_id": selected_team_s[0],
                            "team_title": selected_team_s[1],
                            "type": "service",
                            "title": serv_title,
                            "description": serv_desc,
                            "contact": serv_contact,
                            "deadline": str(serv_deadline),
                            "createdBy": st.session_state["user_uid"],
                            "createdAt": datetime.datetime.utcnow(),
                            "volunteers": []
                        })
                        st.success("Service offered successfully!")
                        request_rerun()
                    else:
                        st.warning("Please fill all required fields.")
            
            # Marketplace
            with tab_view:
                st.subheader("🌟 Marketplace")
                items = get_all_products_services()
                
                if not items:
                    st.info("No products or services available yet.")
                else:
                    # Filter options
                    filter_type = st.selectbox("Filter by Type", ["All", "Products", "Services"])
                    
                    # Display items
                    for item_id, item in items:
                        if filter_type == "Products" and item["type"] != "product":
                            continue
                        if filter_type == "Services" and item["type"] != "service":
                            continue
                            
                        with st.container():
                            st.markdown(f"<div class='product-card'>", unsafe_allow_html=True)
                            
                            # Header with type badge
                            st.markdown(f"**{'🚀 Product' if item['type'] == 'product' else '💼 Service'}**: {item['title']}")
                            
                            # Image display
                            if item.get("image_url"):
                                st.image(item["image_url"], width=300)
                            
                            # Details
                            st.caption(f"By Team: {item['team_title']}")
                            st.write(item["description"])
                            
                            # Deadline
                            if item.get("deadline"):
                                st.write(f"⏰ **Deadline**: {item['deadline']}")
                            
                            # Contact
                            st.write(f"📞 **Contact**: {item['contact']}")
                            
                            # Volunteers for services
                            if item["type"] == "service":
                                volunteers = item.get("volunteers", [])
                                st.write(f"👥 **Volunteers**: {len(volunteers)}")
                                if st.session_state["user_uid"] not in volunteers:
                                    if st.button("Join as Volunteer", key=f"join_vol_{item_id}"):
                                        volunteers.append(st.session_state["user_uid"])
                                        db.collection("products_services").document(item_id).update({"volunteers": volunteers})
                                        st.success("You're now a volunteer!")
                                        request_rerun()
                                else:
                                    st.info("You're already volunteering for this service.")
                            
                            # Owner controls
                            if item["createdBy"] == st.session_state["user_uid"]:
                                if st.button("Delete", key=f"delete_{item_id}"):
                                    delete_product(item_id)
                                    st.success("Item deleted!")
                                    request_rerun()
                            
                            st.markdown("</div>", unsafe_allow_html=True)
                            st.markdown("---")

    elif menu == "Stats":
        st.header("📊 Platform Statistics")
        total_ideas, total_products, total_services, total_users = count_total_stats()
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"""
            <div class="stats-card">
                <h3>Ideas</h3>
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
                <h3>Users</h3>
                <div class="value">{total_users}</div>
            </div>
            """, unsafe_allow_html=True)
        
        # Activity chart placeholder
        st.subheader("📈 Activity Over Time")
        st.line_chart({
            'Ideas': [5, 12, 8, 15, 20, 25, 30],
            'Products': [2, 5, 7, 10, 12, 15, 18],
            'Services': [1, 3, 5, 8, 10, 12, 15]
        })

        # Top teams
        st.subheader("🏆 Top Teams")
        teams_data = defaultdict(int)
        posts = db.collection("posts").stream()
        for post in posts:
            data = post.to_dict()
            teams_data[data["title"]] = len(data.get("team", []))
        
        top_teams = sorted(teams_data.items(), key=lambda x: x[1], reverse=True)[:5]
        for team, members in top_teams:
            st.progress(min(members/20, 1.0), text=f"{team}: {members} members")

st.markdown('</div>', unsafe_allow_html=True)
