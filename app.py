# --------------------------------
# IMPORTS
# --------------------------------
import streamlit as st
from database import SessionLocal
from openai import OpenAI
PILOT_MODE = True
from pdf_service import generate_pdf
from email_service import send_email
from auth import authenticator, credentials
from create_ncr import show_create_ncr
from field_mode import show_field_mode
from dashboard import show_dashboard
# --------------------------------
# PAGE CONFIG
# --------------------------------
st.set_page_config(
    page_title="AI NCR Assistant",
    layout="wide")
# --------------------------------
# OPENAI CLIENT
# --------------------------------
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

## Add Login UI
authenticator.login(location="main")
name = st.session_state.get("name")
authentication_status = st.session_state.get("authentication_status")
username = st.session_state.get("username", "unknown")

## Basic Usage Tracking (Foundation for Paid Plans)
if "ncr_count" not in st.session_state:
    st.session_state.ncr_count = 0
# --------------------------------
# MAIN APP
# --------------------------------

if authentication_status:
    st.sidebar.metric("NCRs Created (Session)", st.session_state.ncr_count)

    db = SessionLocal()

    try:

        ## Capture Role After Login

        user_data = credentials["usernames"].get(username)

        if not user_data:
            st.error("Invalid user configuration")
            st.stop()

        role = user_data.get("role") or "engineer"

        ## Role-Based UI Control
        # 👷 Engineer View
        if role == "engineer":
            allowed_menu = ["Create NCR", "Field Mode"]

        elif role == "qa":
            allowed_menu = ["Dashboard", "Field Mode"]

        elif role == "admin":
            allowed_menu = ["Create NCR", "Field Mode", "Dashboard"]

        authenticator.logout("Logout", "sidebar")
        st.sidebar.success(f"Welcome {name}")

        st.title("🏗 AI-Powered NCR Assistant")

        
        previous_menu = st.session_state.get("menu")

        if previous_menu not in allowed_menu:
            previous_menu = allowed_menu[0]

        index = allowed_menu.index(previous_menu) if previous_menu in allowed_menu else 0

        menu = st.sidebar.selectbox(
            "Menu",
            allowed_menu,
            index=index
        )

        st.session_state.menu = menu

        # CREATE NCR
        if menu == "Create NCR":

            show_create_ncr(
                db=db,
                username=username                
            )

        # Build Field Mode UI
        elif menu == "Field Mode":

            show_field_mode(
                db=db,
                username=username                
            )

        # DASHBOARD
        elif menu == "Dashboard":
            show_dashboard(db, role, client)

    finally:
        
        db.close()

elif authentication_status == False:
    st.error("Incorrect username/password")

elif authentication_status == None:
    st.warning("Please login")