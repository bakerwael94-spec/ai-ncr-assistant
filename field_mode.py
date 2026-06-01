import streamlit as st
import os
import io
import base64

from datetime import datetime
from PIL import Image

from database import NCR
from ai_service import analyze_image


def show_field_mode(db, username):

    st.title("📱 Field NCR Mode (Fast Entry)")

    project = st.text_input("Project")
    location = st.text_input("Location")
    uploaded_file = st.file_uploader("Photo", type=["jpg", "png", "jpeg"])


    image_path = None

    if uploaded_file:

        os.makedirs("uploads", exist_ok=True)

        unique_name = (
            f"{datetime.now().timestamp()}_{uploaded_file.name}"
        )

        image_path = f"uploads/{unique_name}"

        image = Image.open(uploaded_file)

        image.save(image_path)

    # AI AUTO ANALYSIS (CORE VALUE)

    if uploaded_file and st.button("Generate AI NCR"):


        image = Image.open(uploaded_file)

        buffer = io.BytesIO()
        image.save(buffer, format="PNG")

        base64_image = base64.b64encode(buffer.getvalue()).decode()

        ai_output = analyze_image(base64_image)

        st.session_state.ai_output = ai_output

        st.success("AI NCR Generated")

    # SHOW RESULT + CONFIRM BUTTON
    if st.session_state.get("ai_output"):

        st.subheader("🧠 AI Suggested NCR")

        st.write(st.session_state.ai_output)

        # FEEDBACK
        feedback = st.text_area("Optional Feedback")

        if st.button("Save NCR"):

            new_ncr = NCR(
                company="Pilot Project",
                project=project,
                location=location,
                discipline="Auto",
                description=st.session_state.ai_output,
                status="Open",
                created_by=username,
                image_path=image_path
            )

            db.add(new_ncr)
            db.commit()
            st.session_state.ncr_count += 1
            
            st.session_state.last_feedback = feedback
            st.session_state.ai_output = ""

            st.success("NCR Saved Successfully!")







