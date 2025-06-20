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
    .milestone {
        background: #e6f7ff;
        border-left: 4px solid #0d6efd;
        padding: 10px;
        margin: 10px 0;
        border-radius: 0 8px 8px 0;
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
    # Load Firebase Service Account from secrets
    service_account_json = st.secrets["FIREBASE_SERVICE_ACCOUNT"]
    
    # Parse the JSON string to a dictionary
    key_dict = json.loads(service_account_json)
    
    # Create credentials from the dictionary
    cred = credentials.Certificate(key_dict)
    
    # Get the storage bucket name from project ID
    bucket_name = f"{key_dict['project_id']}.appspot.com"
    
    # Initialize Firebase app with credentials and storage bucket
    firebase_admin.initialize_app(cred, {
        'storageBucket': bucket_name
    })

# Set up Firestore client and API key
db = firestore.client()
FIREBASE_API_KEY = st.secrets["FIREBASE_API_KEY"]

# Get storage bucket explicitly using the bucket name
try:
    # Load Firebase Service Account from secrets again to get bucket name
    service_account_json = st.secrets["FIREBASE_SERVICE_ACCOUNT"]
    key_dict = json.loads(service_account_json)
    bucket_name = f"{key_dict['project_id']}.appspot.com"
    FIREBASE_BUCKET = storage.bucket(bucket_name)
except Exception as e:
    st.error(f"Failed to initialize Firebase Storage: {e}")
    FIREBASE_BUCKET = None

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
def post_idea(title, description, user_uid, deadline, milestones, contact):
    idea_data = {
        "title": title,
        "description": description,
        "createdAt": datetime.datetime.utcnow(),
        "createdBy": user_uid,
        "team": [user_uid],
        "deadline": deadline,
        "contact": contact,
        "status": "Planning",
        "milestones": milestones or []
    }
    return db.collection("posts").add(idea_data)

def update_idea(post_id, new_title, new_description, new_deadline, new_status, new_milestones, new_contact):
    update_data = {
        "title": new_title,
        "description": new_description,
        "deadline": new_deadline,
        "status": new_status,
        "contact": new_contact
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
    return [(pid, p["title"]) for pid, p in posts if user_uid in p["team"]]

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

def add_milestone(post_id, milestone):
    ref = db.collection("posts").document(post_id)
    ref.update({"milestones": firestore.ArrayUnion([milestone])})

def mark_milestone_complete(post_id, milestone_index):
    ref = db.collection("posts").document(post_id)
    doc = ref.get()
    if doc.exists:
        data = doc.to_dict()
        milestones = data.get("milestones", [])
        if milestone_index < len(milestones):
            milestones[milestone_index]["completed"] = True
            ref.update({"milestones": milestones})

# UI starts
st.markdown('<div class="main">', unsafe_allow_html=True)
st.title("UniteSphere - Team Collaboration Platform")

if "id_token" not in st.session_state:
    st.subheader("Login or Sign Up")
    tab1, tab2 = st.tabs(["Login", "Sign Up"])

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
                        st.success("Login successful")
                        request_rerun()
                    else:
                        st.warning("Please verify your email first")
                else:
                    st.error("Login failed. Please check your credentials")

    with tab2:
        email = st.text_input("Email", key="signup_email")
        password = st.text_input("Password", type="password", key="signup_password")
        if st.button("Sign Up", use_container_width=True, key="signup_button"):
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
    if st.sidebar.button("Logout", use_container_width=True, key="logout_button"):
        st.session_state.clear()
        request_rerun()
    
    # Check admin status
    is_admin = st.session_state.get("email") in ADMINS
    menu_options = ["Home", "Submit Idea", "Team Chat", "Products & Services", "Rules", "Stats"]
    if is_admin:
        menu_options.append("Admin")
    
    menu = st.sidebar.selectbox("Menu", menu_options, key="main_menu")

    if menu == "Home":
        st.header("Project Ideas")
        for post_id, post in get_all_posts():
            with st.expander(f"{post['title']} - Team: {len(post['team'])} members | Status: {post.get('status', 'Active')}"):
                st.write(post["description"])
                st.caption(f"Created by: {post['createdBy']}")
                
                # Project details
                if post.get("deadline"):
                    try:
                        deadline_date = datetime.datetime.strptime(post["deadline"], "%Y-%m-%d")
                        days_left = (deadline_date - datetime.datetime.now()).days
                        deadline_status = f"⏰ Deadline: {post['deadline']} ({days_left} days left)"
                        st.write(deadline_status)
                    except:
                        st.write(f"⏰ Deadline: {post['deadline']}")
                
                if post.get("contact"):
                    st.write(f"📞 Contact: {post['contact']}")
                
                # Milestones section
                milestones = post.get("milestones", [])
                if milestones:
                    st.subheader("Project Milestones")
                    for i, milestone in enumerate(milestones):
                        status = "✅" if milestone.get("completed", False) else "⏳"
                        with st.container():
                            st.markdown(f"<div class='milestone'><b>{status} {milestone['name']}</b><br>{milestone.get('description', '')}</div>", 
                                       unsafe_allow_html=True)
                            
                            # Mark as complete button
                            if st.session_state["user_uid"] in post["team"] and not milestone.get("completed", False):
                                if st.button(f"Mark Complete", key=f"complete_{post_id}_{i}"):
                                    mark_milestone_complete(post_id, i)
                                    st.success("Milestone marked as complete!")
                                    request_rerun()
                
                # Join team button
                if st.session_state["user_uid"] not in post["team"]:
                    if st.button("Join Team", key=f"join_{post_id}"):
                        join_team(post_id, st.session_state["user_uid"])
                        st.success("You joined this team")
                        request_rerun()
                
                # Idea owner controls
                if post["createdBy"] == st.session_state["user_uid"]:
                    st.subheader("Manage Your Project")
                    new_title = st.text_input("Edit Title", value=post["title"], key=f"title_{post_id}")
                    new_desc = st.text_area("Edit Description", value=post["description"], key=f"desc_{post_id}")
                    
                    # Deadline and contact
                    col1, col2 = st.columns(2)
                    with col1:
                        try:
                            deadline_value = datetime.datetime.strptime(post.get("deadline", str(datetime.date.today())), "%Y-%m-%d")
                        except:
                            deadline_value = datetime.datetime.now()
                        new_deadline = st.date_input("Edit Deadline", 
                                                    value=deadline_value, 
                                                    key=f"deadline_{post_id}")
                    with col2:
                        new_contact = st.text_input("Edit Contact", value=post.get("contact", ""), key=f"contact_{post_id}")
                    
                    # Status
                    status_options = ["Planning", "In Progress", "Testing", "Completed", "On Hold"]
                    current_status = post.get("status", "Planning")
                    status_index = status_options.index(current_status) if current_status in status_options else 0
                    new_status = st.selectbox("Project Status", status_options, index=status_index, key=f"status_{post_id}")
                    
                    # Milestone management
                    st.subheader("Manage Milestones")
                    new_milestones = []
                    existing_milestones = post.get("milestones", [])
                    
                    # Display existing milestones for editing
                    for i, milestone in enumerate(existing_milestones):
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            name = st.text_input(f"Milestone {i+1} Name", value=milestone["name"], key=f"milestone_name_{post_id}_{i}")
                            desc = st.text_area(f"Description", value=milestone.get("description", ""), key=f"milestone_desc_{post_id}_{i}")
                        with col2:
                            completed = st.checkbox("Completed", value=milestone.get("completed", False), key=f"milestone_complete_{post_id}_{i}")
                        new_milestones.append({"name": name, "description": desc, "completed": completed})
                    
                    # Add new milestone
                    if st.button("Add New Milestone", key=f"add_milestone_{post_id}"):
                        new_milestones.append({"name": "New Milestone", "description": "", "completed": False})
                    
                    # Update button
                    if st.button("Update Project", key=f"update_{post_id}"):
                        update_idea(post_id, new_title, new_desc, str(new_deadline), new_status, new_milestones, new_contact)
                        st.success("Project updated")
                        request_rerun()
                    
                    # Delete button
                    if st.button("Delete Project", key=f"delete_{post_id}", type="secondary"):
                        delete_idea(post_id)
                        st.success("Project deleted")
                        request_rerun()

    elif menu == "Submit Idea":
        st.header("Submit a New Project Idea")
        title = st.text_input("Project Title", key="new_project_title")
        description = st.text_area("Project Description", key="new_project_desc")
        
        col1, col2 = st.columns(2)
        with col1:
            deadline = st.date_input("Project Deadline", min_value=datetime.date.today(), key="new_project_deadline")
        with col2:
            contact = st.text_input("Contact Information", key="new_project_contact")
        
        # Milestones
        st.subheader("Project Milestones")
        milestones = []
        num_milestones = st.slider("Number of Milestones", 0, 10, 3, key="milestone_count")
        
        for i in range(num_milestones):
            st.markdown(f"### Milestone {i+1}")
            name = st.text_input(f"Name", key=f"milestone_name_{i}")
            desc = st.text_area(f"Description", key=f"milestone_desc_{i}")
            milestones.append({"name": name, "description": desc, "completed": False})
        
        if st.button("Submit Project", use_container_width=True, key="submit_project_button"):
            if title and description:
                post_idea(title, description, st.session_state["user_uid"], str(deadline), milestones, contact)
                st.success("Your project has been posted")
                request_rerun()
            else:
                st.warning("Please fill both title and description fields")

    elif menu == "Rules":
        st.header("Community Guidelines", key="rules_header")
        st.markdown("""
        - **Respect others**: Treat all community members with courtesy
        - **No spamming**: Keep content relevant and valuable
        - **Meaningful participation**: Join teams only if you can contribute
        - **Verify information**: Ensure accuracy before sharing
        - **Protect intellectual property**: Always credit sources
        - **Report issues**: Notify admins of any problems or violations
        """, key="rules_content")
        st.info("These guidelines help maintain a productive and respectful environment for everyone.", key="rules_info")

    elif menu == "Team Chat":
        st.header("Team Communication", key="team_chat_header")
        user_posts = [(pid, p["title"]) for pid, p in get_all_posts() if st.session_state["user_uid"] in p["team"]]

        if not user_posts:
            st.info("You need to join a team to access team chat", key="no_teams_info")
        else:
            selected = st.selectbox("Select a team", user_posts, format_func=lambda x: x[1], key="chat_team_select")
            selected_post_id, selected_title = selected

            st.subheader(f"Chat: {selected_title}", key="chat_subheader")
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
                if st.button("Clear Chat", type="secondary", key=f"clear_chat_{selected_post_id}"):
                    st.warning("This feature is currently under development")

    elif menu == "Products & Services":
        st.header("Products & Services Marketplace", key="marketplace_header")
        st.info("This is where completed projects can be offered as products or services", key="marketplace_info")
        
        user_teams = get_user_teams(st.session_state["user_uid"])
        
        if not user_teams:
            st.info("Join or create a team first to post products or services", key="no_teams_marketplace")
        else:
            tab_prod, tab_serv, tab_view = st.tabs(["Post Product", "Offer Service", "Browse Marketplace"])
            
            # Product Submission
            with tab_prod:
                st.subheader("Submit a Completed Product", key="submit_product_header")
                selected_team = st.selectbox("Team", user_teams, format_func=lambda x: x[1], key="prod_team_select")
                prod_title = st.text_input("Product Name", key="prod_title")
                prod_desc = st.text_area("Product Description", key="prod_desc")
                prod_price = st.text_input("Price", key="prod_price")
                prod_contact = st.text_input("Contact Information", key="prod_contact")
                prod_image = st.file_uploader("Product Image", type=["png", "jpg", "jpeg"], key="prod_image")
                
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
                            "createdAt": datetime.datetime.utcnow()
                        })
                        st.success("Product submitted to marketplace")
                        request_rerun()
                    else:
                        st.warning("Please fill all required fields")
            
            # Service Submission
            with tab_serv:
                st.subheader("Offer a Service", key="offer_service_header")
                selected_team_s = st.selectbox("Team", user_teams, format_func=lambda x: x[1], key="serv_team_select")
                serv_title = st.text_input("Service Name", key="serv_title")
                serv_desc = st.text_area("Service Description", key="serv_desc")
                serv_price = st.text_input("Price", key="serv_price")
                serv_contact = st.text_input("Contact Information", key="serv_contact")
                
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
                            "createdBy": st.session_state["user_uid"],
                            "createdAt": datetime.datetime.utcnow(),
                            "volunteers": []
                        })
                        st.success("Service submitted to marketplace")
                        request_rerun()
                    else:
                        st.warning("Please fill all required fields")
            
            # Marketplace
            with tab_view:
                st.subheader("Marketplace", key="browse_marketplace_header")
                items = get_all_products_services()
                
                if not items:
                    st.info("No products or services available", key="no_items_info")
                else:
                    # Filter options
                    filter_type = st.selectbox("Filter by Type", ["All", "Products", "Services"], key="marketplace_filter")
                    
                    # Display items
                    for item_id, item in items:
                        if filter_type == "Products" and item["type"] != "product":
                            continue
                        if filter_type == "Services" and item["type"] != "service":
                            continue
                            
                        with st.container():
                            st.markdown(f"<div class='product-card'>", unsafe_allow_html=True)
                            
                            # Header with type badge
                            st.markdown(f"**{item['title']}**", key=f"item_title_{item_id}")
                            st.caption(f"Type: {'Product' if item['type'] == 'product' else 'Service'}", key=f"item_type_{item_id}")
                            
                            # Image display
                            if item.get("image_url"):
                                st.image(item["image_url"], width=300, key=f"item_image_{item_id}")
                            
                            # Details
                            st.caption(f"By Team: {item['team_title']}", key=f"item_team_{item_id}")
                            st.write(item["description"], key=f"item_desc_{item_id}")
                            
                            # Price
                            if item.get("price"):
                                st.write(f"**Price**: {item['price']}", key=f"item_price_{item_id}")
                            
                            # Contact
                            st.write(f"**Contact**: {item['contact']}", key=f"item_contact_{item_id}")
                            
                            # Volunteers for services
                            if item["type"] == "service":
                                volunteers = item.get("volunteers", [])
                                st.write(f"**Volunteers**: {len(volunteers)}", key=f"item_volunteers_{item_id}")
                                if st.session_state["user_uid"] not in volunteers:
                                    if st.button("Join as Volunteer", key=f"join_vol_{item_id}"):
                                        volunteers.append(st.session_state["user_uid"])
                                        db.collection("products_services").document(item_id).update({"volunteers": volunteers})
                                        st.success("You're now a volunteer")
                                        request_rerun()
                                else:
                                    st.info("You're already volunteering for this service", key=f"already_volunteering_{item_id}")
                            
                            # Owner controls
                            if item["createdBy"] == st.session_state["user_uid"]:
                                if st.button("Delete", key=f"delete_{item_id}", type="secondary"):
                                    delete_product(item_id)
                                    st.success("Item deleted")
                                    request_rerun()
                            
                            st.markdown("</div>", unsafe_allow_html=True)
                            st.markdown("---", key=f"divider_{item_id}")

    elif menu == "Stats":
        st.header("Platform Statistics", key="stats_header")
        total_ideas, total_products, total_services, total_users = count_total_stats()
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"""
            <div class="stats-card">
                <h3>Total Ideas</h3>
                <div class="value">{total_ideas}</div>
            </div>
            """, unsafe_allow_html=True, key="stats_ideas")
            
            st.markdown(f"""
            <div class="stats-card">
                <h3>Products</h3>
                <div class="value">{total_products}</div>
            </div>
            """, unsafe_allow_html=True, key="stats_products")
        
        with col2:
            st.markdown(f"""
            <div class="stats-card">
                <h3>Services</h3>
                <div class="value">{total_services}</div>
            </div>
            """, unsafe_allow_html=True, key="stats_services")
            
            st.markdown(f"""
            <div class="stats-card">
                <h3>Registered Users</h3>
                <div class="value">{total_users}</div>
            </div>
            """, unsafe_allow_html=True, key="stats_users")
        
        # Activity chart placeholder
        st.subheader("Activity Over Time", key="activity_header")
        st.line_chart({
            'Ideas': [5, 12, 8, 15, 20, 25, 30],
            'Products': [2, 5, 7, 10, 12, 15, 18],
            'Services': [1, 3, 5, 8, 10, 12, 15]
        }, key="activity_chart")

        # Top teams
        st.subheader("Top Teams by Members", key="top_teams_header")
        teams_data = defaultdict(int)
        posts = db.collection("posts").stream()
        for post in posts:
            data = post.to_dict()
            teams_data[data["title"]] = len(data.get("team", []))
        
        top_teams = sorted(teams_data.items(), key=lambda x: x[1], reverse=True)[:5]
        for i, (team, members) in enumerate(top_teams):
            st.progress(min(members/20, 1.0), text=f"{team}: {members} members", key=f"team_progress_{i}")
    
    elif menu == "Admin":
        st.header("Administration Panel", key="admin_header")
        st.warning("You have administrative privileges on this platform", key="admin_warning")
        
        # Create tabs for different admin functions
        admin_tabs = st.tabs(["Project Ideas", "Products & Services", "User Management"], key="admin_tabs")
        
        # Tab 1: Project Ideas Management
        with admin_tabs[0]:
            st.subheader("All Project Ideas", key="admin_ideas_header")
            all_ideas = db.collection("posts").order_by("createdAt", direction=firestore.Query.DESCENDING).stream()
            idea_count = 0
            
            for idea in all_ideas:
                idea_count += 1
                data = idea.to_dict()
                with st.container():
                    st.markdown(f"**{data['title']}**", key=f"admin_idea_title_{idea.id}")
                    st.caption(f"Created by: {data['createdBy']} | Team members: {len(data.get('team', []))}", key=f"admin_idea_caption_{idea.id}")
                    st.write(data["description"], key=f"admin_idea_desc_{idea.id}")
                    
                    if data.get("deadline"):
                        st.write(f"**Deadline**: {data['deadline']}", key=f"admin_idea_deadline_{idea.id}")
                    
                    # Delete button for each idea
                    if st.button("Delete Idea", key=f"del_idea_{idea.id}", type="secondary"):
                        db.collection("posts").document(idea.id).delete()
                        st.success("Idea deleted")
                        request_rerun()
                    
                    st.markdown("---", key=f"admin_idea_divider_{idea.id}")
            
            if idea_count == 0:
                st.info("No project ideas found", key="admin_no_ideas")
                
            # Upload new idea as admin
            st.subheader("Create New Idea (Admin)", key="admin_create_idea_header")
            admin_title = st.text_input("Idea Title", key="admin_title")
            admin_desc = st.text_area("Description", key="admin_desc")
            if st.button("Post Idea as Admin", key="admin_post_idea_button"):
                if admin_title and admin_desc:
                    post_idea(admin_title, admin_desc, "admin", str(datetime.date.today()), [], "admin@example.com")
                    st.success("Admin idea posted")
                    request_rerun()
        
        # Tab 2: Products & Services Management
        with admin_tabs[1]:
            st.subheader("All Products & Services", key="admin_items_header")
            all_items = db.collection("products_services").order_by("createdAt", direction=firestore.Query.DESCENDING).stream()
            item_count = 0
            
            # Filter options
            filter_type = st.selectbox("Filter by Type", ["All", "Products", "Services"], key="admin_items_filter")
            
            for item in all_items:
                data = item.to_dict()
                
                # Apply filter
                if filter_type == "Products" and data["type"] != "product":
                    continue
                if filter_type == "Services" and data["type"] != "service":
                    continue
                    
                item_count += 1
                with st.container():
                    st.markdown(f"**{data['title']}**", key=f"admin_item_title_{item.id}")
                    st.caption(f"Type: {data['type']} | Created by: {data['createdBy']}", key=f"admin_item_caption_{item.id}")
                    st.write(data["description"], key=f"admin_item_desc_{item.id}")
                    
                    if data.get("image_url"):
                        st.image(data["image_url"], width=200, key=f"admin_item_image_{item.id}")
                    
                    # Delete button for each item
                    if st.button("Delete Item", key=f"del_item_{item.id}", type="secondary"):
                        db.collection("products_services").document(item.id).delete()
                        st.success("Item deleted")
                        request_rerun()
                    
                    st.markdown("---", key=f"admin_item_divider_{item.id}")
            
            if item_count == 0:
                st.info("No products or services found", key="admin_no_items")
                
            # Upload new product/service as admin
            st.subheader("Create New Item (Admin)", key="admin_create_item_header")
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
                    request_rerun()
        
        # Tab 3: User Management (Placeholder)
        with admin_tabs[2]:
            st.subheader("User Management", key="user_management_header")
            st.info("This feature is under development", key="user_management_info")
            st.write("Future functionality will include:", key="user_management_features")
            st.write("- Viewing all registered users", key="user_management_feature1")
            st.write("- Managing user roles and permissions", key="user_management_feature2")
            st.write("- Suspending or deleting user accounts", key="user_management_feature3")

st.markdown('</div>', unsafe_allow_html=True)
