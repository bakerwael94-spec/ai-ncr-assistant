import streamlit as st
import os
import io
import base64

from datetime import datetime
from PIL import Image

from database import NCR
from services.ai_service import analyze_image
from services.email_service import send_email


def show_create_ncr(db, username):

    ## Add Session State Variables

    if "ai_generated_text" not in st.session_state:
        st.session_state.ai_generated_text = ""

    if "ai_discipline" not in st.session_state:
        st.session_state.ai_discipline = "Civil"

    

    st.subheader("Create New NCR")

    company = st.text_input("Company Name")

        

    # -----------------------------
    # BASIC NCR FIELDS
    # -----------------------------

    project = st.text_input("Project Name")
    location = st.text_input("Location")

    # Add Email Field in Create NCR
    notification_email = st.text_input(
        "Notification Email"
    )

    
    discipline_options = ["Civil", "Architectural", "MEP"]

    default_index = discipline_options.index(
        st.session_state.ai_discipline
    )

    discipline = st.selectbox(
        "Discipline",
        discipline_options,
        index=default_index
    )

    # AI-generated or manual description
    description = st.text_area(
        "Issue Description",
        value=st.session_state.ai_generated_text,
        height=250
    )

    # -----------------------------
    # IMAGE UPLOAD (SINGLE SOURCE OF TRUTH)
    # -----------------------------

    st.subheader("📷 Upload Site Photo")

    uploaded_file = st.file_uploader(
        "Upload defect image",
        type=["png", "jpg", "jpeg"]
    )

    image_path = None
    

    ## Show Image Preview
    if uploaded_file is not None:
        st.image(uploaded_file, caption="Uploaded Image", use_container_width=True)

        # Save image immediately (NO extra button needed)

        os.makedirs("uploads", exist_ok=True)
        unique_name = f"{datetime.now().timestamp()}_{uploaded_file.name}"
        file_path = f"uploads/{unique_name}"

        image = Image.open(uploaded_file)
        image.save(file_path)

        image_path = file_path


    ## Create AI Auto-NCR Button

    if st.button("🔍 Generate Full AI NCR"):

        if uploaded_file is not None:

            image = Image.open(uploaded_file)

            buffer = io.BytesIO()
            image.save(buffer, format="PNG")

            base64_image = base64.b64encode(
                buffer.getvalue()
            ).decode("utf-8")

            result = analyze_image(base64_image)

            st.session_state.ai_generated_text = result

            # Simple discipline detection
            result_lower = result.lower()

            if "mep" in result_lower:
                st.session_state.ai_discipline = "MEP"

            elif "architectural" in result_lower:
                st.session_state.ai_discipline = "Architectural"

            else:
                st.session_state.ai_discipline = "Civil"

            st.success("AI NCR Generated")

            st.rerun()

    # -----------------------------
    # SAVE NCR BUTTON
    # -----------------------------
    st.markdown("---")

    if st.button("💾 Save NCR"):

        new_ncr = NCR(
            company=company,
            project=project,
            location=location,
            discipline=discipline,
            description=description,
            status="Open",
            image_path=image_path,
            created_by=username
        )

        db.add(new_ncr)
        db.commit()
        st.session_state.ncr_count += 1


        # Send Email After NCR Creation

        email_subject = f"NCR Created - {project}"

        email_body = f"""
        A new NCR has been created.

        Project: {project}
        Location: {location}
        Discipline: {discipline}

        Description:
        {description}

        Status: Open
        """




        email_sent = None

        if notification_email and notification_email.strip():
            email_sent = send_email(email_subject, email_body, notification_email)

            if email_sent:
                st.success("Email notification sent!")

                

        st.success("✅ NCR Saved Successfully!")

        # reset AI buffer (optional)
        st.session_state["ai_description"] = ""