import streamlit as st
import datetime
import requests
import json
import firebase_admin
from firebase_admin import credentials, firestore, storage
import uuid
from collections import defaultdict

# Define admin emails
ADMINS = ["nameer.ansaf@gmail.com", "anvinimithk2505@gmail.com"]

# Page Config
st.set_page_config(page_title="UniteSphere", layout="centered", page_icon="🤝")

# Custom CSS for professional UI
st.markdown(
    """
    <style>
    /* Background */
    .main {
        background-color: #f8f9fa;
        color: #343a40;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        padding: 15px 30px;
    }
    /* Headers */
    h1, h2, h3 {
        color: #0d6efd;
        font-family: 'Arial', sans-serif;
        border-bottom: 2px solid #0d6efd;
        padding-bottom: 8px;
    }
    /* Buttons */
    div.stButton > button {
        background: linear-gradient(45deg, #0d6efd 0%, #6f42c1 100%);
        color: white;
        font-weight: bold;
        border-radius: 8px;
        padding: 8px 20px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        transition: background 0.3s ease;
    }
    div.stButton > button:hover {
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
        color: #495057;
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
        color: #6c757d;
        margin-top: 0;
        font-size: 1rem;
    }
    .stats-card .value {
        font-size: 2rem;
        font-weight: bold;
        color: #0d6efd;
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
st.title("UniteSphere - Team Collaboration Platform")

if "id_token" not in st.session_state:
    st.subheader("Login or Sign Up")
    tab1, tab2 = st.tabs(["Login", "Sign Up"])

    with tab1:
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_password")
        if st.button("Login", use_container_width=True):
            if not email or not password:
                st.warning("Please enter your email and password")
            else:
                res = login(email, password)
                if "idToken" in res:
                    if check_email_verified(res["idToken"]):
                        st.session_state["id_token"] = res["idToken"]
                        st.session_state["email"] = email
                        st.session_state["user_uid"] = res["localId"]
                        st.success("Login successful")
                        request_rerun()
                    else:
                        st.warning("Please verify your email first")
                else:
                    st.error("Login failed. Please check your credentials")

    with tab2:
        email = st.text_input("Email", key="signup_email")
        password = st.text_input("Password", type="password", key="signup_password")
        if st.button("Sign Up", use_container_width=True):
            if not email or not password:
                st.warning("Please enter both email and password")
            else:
                res = signup(email, password)
                if "idToken" in res:
                    send_verification_email(res["idToken"])
                    st.success("Account created. Please check your email for verification")
                else:
                    st.error("Sign up failed. Please try again")

else:
    st.sidebar.write(f"Logged in as: {st.session_state['email']}")
    if st.sidebar.button("Logout", use_container_width=True):
        st.session_state.clear()
        request_rerun()
    
    # Check admin status
    is_admin = st.session_state.get("email") in ADMINS
    menu_options = ["Home", "Submit Idea", "Team Chat", "Products & Services", "Rules", "Stats"]
    if is_admin:
        menu_options.append("Admin")
    
    menu = st.sidebar.selectbox("Menu", menu_options)

    if menu == "Home":
        st.header("Project Ideas")
        for post_id, post in get_all_posts():
            with st.expander(f"{post['title']} - Team: {len(post['team'])} members"):
                st.write(post["description"])
                st.caption(f"Created by: {post['createdBy']}")
                
                # Join team button
                if st.session_state["user_uid"] not in post["team"]:
                    if st.button("Join Team", key=f"join_{post_id}"):
                        join_team(post_id, st.session_state["user_uid"])
                        st.success("You joined this team")
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
                            st.success("Idea updated")
                            request_rerun()
                    with col2:
                        if st.button("Delete Idea", key=f"delete_{post_id}", type="secondary"):
                            delete_idea(post_id)
                            st.success("Idea deleted")
                            request_rerun()

    elif menu == "Submit Idea":
        st.header("Submit a New Idea")
        title = st.text_input("Idea Title")
        description = st.text_area("Description")
        if st.button("Post Idea", use_container_width=True):
            if title and description:
                post_idea(title, description, st.session_state["user_uid"])
                st.success("Your idea has been posted")
                request_rerun()
            else:
                st.warning("Please fill both title and description fields")

    elif menu == "Rules":
        st.header("Community Guidelines")
        st.markdown("""
        - **Respect others**: Treat all community members with courtesy
        - **No spamming**: Keep content relevant and valuable
        - **Meaningful participation**: Join teams only if you can contribute
        - **Verify information**: Ensure accuracy before sharing
        - **Protect intellectual property**: Always credit sources
        - **Report issues**: Notify admins of any problems or violations
        """)
        st.info("These guidelines help maintain a productive and respectful environment for everyone.")

    elif menu == "Team Chat":
        st.header("Team Communication")
        user_posts = [(pid, p["title"]) for pid, p in get_all_posts() if st.session_state["user_uid"] in p["team"]]

        if not user_posts:
            st.info("You need to join a team to access team chat")
        else:
            selected = st.selectbox("Select a team", user_posts, format_func=lambda x: x[1], key="chat_team_select")
            selected_post_id, selected_title = selected

            st.subheader(f"Chat: {selected_title}")
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
                        <div style="background: #e6f2ff; padding: 10px; border-radius: 10px; margin: 5px 0; text-align: right;">
                            <div><strong>You</strong> • {timestamp}</div>
                            <div>{content}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown(f"""
                        <div style="background: #f8f9fa; padding: 10px; border-radius: 10px; margin: 5px 0; border: 1px solid #dee2e6;">
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
                        st.success("Message sent")
                        request_rerun()
            with col2:
                if st.button("Clear Chat", type="secondary"):
                    st.warning("This feature is currently under development")

    elif menu == "Products & Services":
        st.header("Products & Services")
        user_teams = get_user_teams(st.session_state["user_uid"])
        
        if not user_teams:
            st.info("Join or create a team first to post products or services")
        else:
            tab_prod, tab_serv, tab_view = st.tabs(["Post Product", "Offer Service", "Browse Marketplace"])
            
            # Product Submission
            with tab_prod:
                st.subheader("Submit a Product")
                selected_team = st.selectbox("Team", user_teams, format_func=lambda x: x[1], key="prod_team_select")
                prod_title = st.text_input("Product Name")
                prod_desc = st.text_area("Product Description")
                prod_contact = st.text_input("Contact Information")
                prod_deadline = st.date_input("Target Date", min_value=datetime.date.today())
                prod_image = st.file_uploader("Product Image (optional)", type=["png", "jpg", "jpeg"])
                
                if st.button("Submit Product", use_container_width=True):
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
                        st.success("Product submitted")
                        request_rerun()
                    else:
                        st.warning("Please fill all required fields")
            
            # Service Submission
            with tab_serv:
                st.subheader("Offer a Service")
                selected_team_s = st.selectbox("Team", user_teams, format_func=lambda x: x[1], key="serv_team_select")
                serv_title = st.text_input("Service Name")
                serv_desc = st.text_area("Service Description")
                serv_contact = st.text_input("Contact Information")
                serv_deadline = st.date_input("Availability", min_value=datetime.date.today())
                
                if st.button("Submit Service", use_container_width=True):
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
                        st.success("Service submitted")
                        request_rerun()
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
                            st.markdown(f"**{item['title']}**")
                            st.caption(f"Type: {'Product' if item['type'] == 'product' else 'Service'}")
                            
                            # Image display
                            if item.get("image_url"):
                                st.image(item["image_url"], width=300)
                            
                            # Details
                            st.caption(f"By Team: {item['team_title']}")
                            st.write(item["description"])
                            
                            # Deadline
                            if item.get("deadline"):
                                st.write(f"**Target Date**: {item['deadline']}")
                            
                            # Contact
                            st.write(f"**Contact**: {item['contact']}")
                            
                            # Volunteers for services
                            if item["type"] == "service":
                                volunteers = item.get("volunteers", [])
                                st.write(f"**Volunteers**: {len(volunteers)}")
                                if st.session_state["user_uid"] not in volunteers:
                                    if st.button("Join as Volunteer", key=f"join_vol_{item_id}"):
                                        volunteers.append(st.session_state["user_uid"])
                                        db.collection("products_services").document(item_id).update({"volunteers": volunteers})
                                        st.success("You're now a volunteer")
                                        request_rerun()
                                else:
                                    st.info("You're already volunteering for this service")
                            
                            # Owner controls
                            if item["createdBy"] == st.session_state["user_uid"]:
                                if st.button("Delete", key=f"delete_{item_id}", type="secondary"):
                                    delete_product(item_id)
                                    st.success("Item deleted")
                                    request_rerun()
                            
                            st.markdown("</div>", unsafe_allow_html=True)
                            st.markdown("---")

    elif menu == "Stats":
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
        
        # Activity chart placeholder
        st.subheader("Activity Over Time")
        st.line_chart({
            'Ideas': [5, 12, 8, 15, 20, 25, 30],
            'Products': [2, 5, 7, 10, 12, 15, 18],
            'Services': [1, 3, 5, 8, 10, 12, 15]
        })

        # Top teams
        st.subheader("Top Teams by Members")
        teams_data = defaultdict(int)
        posts = db.collection("posts").stream()
        for post in posts:
            data = post.to_dict()
            teams_data[data["title"]] = len(data.get("team", []))
        
        top_teams = sorted(teams_data.items(), key=lambda x: x[1], reverse=True)[:5]
        for team, members in top_teams:
            st.progress(min(members/20, 1.0), text=f"{team}: {members} members")
    
    elif menu == "Admin":
        st.header("Administration Panel")
        st.warning("You have administrative privileges on this platform")
        
        # Create tabs for different admin functions
        admin_tabs = st.tabs(["Project Ideas", "Products & Services", "User Management"])
        
        # Tab 1: Project Ideas Management
        with admin_tabs[0]:
            st.subheader("All Project Ideas")
            all_ideas = db.collection("posts").order_by("createdAt", direction=firestore.Query.DESCENDING).stream()
            idea_count = 0
            
            for idea in all_ideas:
                idea_count += 1
                data = idea.to_dict()
                with st.container():
                    st.markdown(f"**{data['title']}**")
                    st.caption(f"Created by: {data['createdBy']} | Team members: {len(data.get('team', []))}")
                    st.write(data["description"])
                    
                    # Delete button for each idea
                    if st.button("Delete Idea", key=f"del_idea_{idea.id}", type="secondary"):
                        db.collection("posts").document(idea.id).delete()
                        st.success("Idea deleted")
                        request_rerun()
                    
                    st.markdown("---")
            
            if idea_count == 0:
                st.info("No project ideas found")
                
            # Upload new idea as admin
            st.subheader("Create New Idea (Admin)")
            admin_title = st.text_input("Idea Title", key="admin_title")
            admin_desc = st.text_area("Description", key="admin_desc")
            if st.button("Post Idea as Admin", key="admin_post_idea"):
                if admin_title and admin_desc:
                    post_idea(admin_title, admin_desc, "admin")
                    st.success("Admin idea posted")
                    request_rerun()
        
        # Tab 2: Products & Services Management
        with admin_tabs[1]:
            st.subheader("All Products & Services")
            all_items = db.collection("products_services").order_by("createdAt", direction=firestore.Query.DESCENDING).stream()
            item_count = 0
            
            # Filter options
            filter_type = st.selectbox("Filter by Type", ["All", "Products", "Services"])
            
            for item in all_items:
                data = item.to_dict()
                
                # Apply filter
                if filter_type == "Products" and data["type"] != "product":
                    continue
                if filter_type == "Services" and data["type"] != "service":
                    continue
                    
                item_count += 1
                with st.container():
                    st.markdown(f"**{data['title']}**")
                    st.caption(f"Type: {data['type']} | Created by: {data['createdBy']}")
                    st.write(data["description"])
                    
                    if data.get("image_url"):
                        st.image(data["image_url"], width=200)
                    
                    # Delete button for each item
                    if st.button("Delete Item", key=f"del_item_{item.id}", type="secondary"):
                        db.collection("products_services").document(item.id).delete()
                        st.success("Item deleted")
                        request_rerun()
                    
                    st.markdown("---")
            
            if item_count == 0:
                st.info("No products or services found")
                
            # Upload new product/service as admin
            st.subheader("Create New Item (Admin)")
            admin_item_type = st.selectbox("Item Type", ["product", "service"], key="admin_item_type")
            admin_item_title = st.text_input("Item Name", key="admin_item_title")
            admin_item_desc = st.text_area("Description", key="admin_item_desc")
            admin_item_contact = st.text_input("Contact Information", key="admin_item_contact")
            admin_item_deadline = st.date_input("Target Date", min_value=datetime.date.today())
            admin_item_image = st.file_uploader("Item Image (optional)", type=["png", "jpg", "jpeg"])
            
            if st.button("Submit as Admin", key="admin_submit_item"):
                if admin_item_title and admin_item_desc and admin_item_contact:
                    image_url = upload_image_to_firebase(admin_item_image) if admin_item_image else None
                    db.collection("products_services").add({
                        "team_id": "admin",
                        "team_title": "Admin Team",
                        "type": admin_item_type,
                        "title": admin_item_title,
                        "description": admin_item_desc,
                        "contact": admin_item_contact,
                        "deadline": str(admin_item_deadline),
                        "image_url": image_url,
                        "createdBy": "admin",
                        "createdAt": datetime.datetime.utcnow(),
                        "volunteers": []
                    })
                    st.success("Item submitted as admin")
                    request_rerun()
        
        # Tab 3: User Management (Placeholder)
        with admin_tabs[2]:
            st.subheader("User Management")
            st.info("This feature is under development")
            st.write("Future functionality will include:")
            st.write("- Viewing all registered users")
            st.write("- Managing user roles and permissions")
            st.write("- Suspending or deleting user accounts")

st.markdown('</div>', unsafe_allow_html=True)
