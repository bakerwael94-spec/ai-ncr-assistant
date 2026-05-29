# --------------------------------
# IMPORTS
# --------------------------------
import streamlit as st
from database import SessionLocal, NCR
import pandas as pd
import streamlit_authenticator as stauth
import matplotlib.pyplot as plt
from openai import OpenAI
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from PIL import Image
import base64
import io
import os
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
PILOT_MODE = True
    
# --------------------------------
# PAGE CONFIG
# --------------------------------
st.set_page_config(
    page_title="AI NCR Assistant",
    layout="wide"
)

# --------------------------------
# OPENAI CLIENT
# --------------------------------
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# --------------------------------
# DATABASE SESSION
# --------------------------------
db = SessionLocal()

# --------------------------------
# PDF FUNCTION
# --------------------------------

def generate_pdf(df):

    pdf_file = "NCR_Report.pdf"

    doc = SimpleDocTemplate(pdf_file)

    styles = getSampleStyleSheet()

    elements = []

    title = Paragraph("AI NCR Report", styles['Title'])

    elements.append(title)
    elements.append(Spacer(1, 12))

    for _, row in df.iterrows():

        text = f"""
        <b>ID:</b> {row['ID']}<br/>
        <b>Project:</b> {row['Project']}<br/>
        <b>Location:</b> {row['Location']}<br/>
        <b>Discipline:</b> {row['Discipline']}<br/>
        <b>Status:</b> {row['Status']}<br/>
        <b>Description:</b> {row['Description']}<br/><br/>
        """

        paragraph = Paragraph(text, styles['BodyText'])

        elements.append(paragraph)
        elements.append(Spacer(1, 12))

    doc.build(elements)

    return pdf_file

# --------------------------------
# Create Email Function
# --------------------------------

def send_email(subject, body, to_email):

    from_email = "bakerwael94@gmail.com"

    app_password = "mign ebwp utdp dtuw"

    msg = MIMEMultipart()

    msg["From"] = from_email

    msg["To"] = to_email

    msg["Subject"] = subject

    msg.attach(MIMEText(body, "plain"))

    try:

        server = smtplib.SMTP("smtp.gmail.com", 587)

        server.starttls()

        server.login(from_email, app_password)

        server.send_message(msg)

        server.quit()

        return True

    except Exception as e:

        st.error(f"Email Error: {e}")

        return False

# --------------------------------
# AUTHENTICATION
# --------------------------------

credentials = {
    "usernames": {
        "qa": {
            "name": "QA Engineer",
            "password": "1234"
        },
        "pm": {
            "name": "Project Manager",
            "password": "1234"
        }
    }
}

## Create Authenticator

authenticator = stauth.Authenticate(
    credentials,
    "ncr_app",
    "random_signature_key",
    cookie_expiry_days=1
)

## Add Login UI
authenticator.login(location="main")
name = st.session_state.get("name")
authentication_status = st.session_state.get("authentication_status")
username = st.session_state.get("username")

## Add Session State Variables

if "ai_generated_text" not in st.session_state:
    st.session_state.ai_generated_text = ""

if "ai_discipline" not in st.session_state:
    st.session_state.ai_discipline = "Civil"

# --------------------------------
# MAIN APP
# --------------------------------

if authentication_status:

    authenticator.logout("Logout", "sidebar")
    st.sidebar.success(f"Welcome {name}")


    st.title("🏗 AI-Powered NCR Assistant")

    menu = st.sidebar.selectbox(
        "Menu",
        ["Create NCR", "Field Mode", "Dashboard"]
    )

   

    # CREATE NCR
    if menu == "Create NCR":

        # Add Email Field in Create NCR
        notification_email = st.text_input(
            "Notification Email"
        )

        st.subheader("Create New NCR")

        company = st.text_input("Company Name")

        # -----------------------------
        # BASIC NCR FIELDS
        # -----------------------------

        project = st.text_input("Project Name")
        location = st.text_input("Location")
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
        base64_image = None

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

            # Prepare for AI
            buffer = io.BytesIO()
            image.save(buffer, format="PNG")
            base64_image = base64.b64encode(buffer.getvalue()).decode("utf-8")


        ## Create AI Auto-NCR Button

        if st.button("🔍 Generate Full AI NCR"):

            if uploaded_file is not None:

                image = Image.open(uploaded_file)

                buffer = io.BytesIO()
                image.save(buffer, format="PNG")

                base64_image = base64.b64encode(
                    buffer.getvalue()
                ).decode("utf-8")

                prompt = """
        You are a senior construction QA/QC engineer.

        Analyze this construction image and generate:

        1. Suggested discipline
        2. Professional NCR description
        3. Root cause
        4. Corrective action

        Return clearly formatted response.
        """

                response = client.chat.completions.create(
                    model="gpt-4.1-mini",
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": prompt
                                },
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/png;base64,{base64_image}"
                                    }
                                }
                            ]
                        }
                    ]
                )

                result = response.choices[0].message.content

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

            if notification_email:

                email_sent = send_email(
                    email_subject,
                    email_body,
                    notification_email
            )

            if email_sent:
                st.success("Email notification sent!")
                

            st.success("✅ NCR Saved Successfully!")

            # reset AI buffer (optional)
            st.session_state["ai_description"] = ""

    # Build Field Mode UI
    if menu == "Field Mode":

        st.title("📱 Field NCR Mode (Fast Entry)")

        project = st.text_input("Project")
        location = st.text_input("Location")
        uploaded_file = st.file_uploader("Photo", type=["jpg", "png", "jpeg"])

        # AI AUTO ANALYSIS (CORE VALUE)

        if uploaded_file and st.button("Generate AI NCR"):


            image = Image.open(uploaded_file)

            buffer = io.BytesIO()
            image.save(buffer, format="PNG")

            base64_image = base64.b64encode(buffer.getvalue()).decode()

            prompt = """
        You are a construction QA/QC inspector.

        From this image generate:
        1. Discipline
        2. Defect type
        3. NCR description
        4. Root cause
        5. Corrective action
        Return structured text.
        """

            response = client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {
                            "url": f"data:image/png;base64,{base64_image}"
                        }}
                    ]
                }]
            )

            ai_output = response.choices[0].message.content

            st.session_state.ai_output = ai_output

            st.success("AI NCR Generated")

        # Add “One Click Submit NCR”

        if st.button("🚀 Submit NCR (Auto AI)"):

            if uploaded_file is None:
                st.error("Please upload a photo")
            else:
                st.success("Processing NCR...")

        # SHOW RESULT + CONFIRM BUTTON

        if "ai_output" in st.session_state:

            st.subheader("🧠 AI Suggested NCR")

            st.write(st.session_state.ai_output)
            # FEEDBACK
            feedback = st.text_area("Optional Feedback (for improvement)")

            if st.button("Save NCR"):

                new_ncr = NCR(
                    project=project,
                    location=location,
                    discipline="Auto",
                    description=st.session_state.ai_output,
                    status="Open"
                )

                db.add(new_ncr)
                db.commit()
                st.session_state.last_feedback = feedback

                st.success("NCR Saved Successfully!")
        


    # DASHBOARD
    elif menu == "Dashboard":

        st.title("🏗 AI NCR Intelligence Dashboard")

        # ----------------------------
        # 1. LOAD DATA FIRST
        # ----------------------------
        ncrs_all = db.query(NCR).all()

        data = []

        for ncr in ncrs_all:
            data.append({
                "ID": ncr.id,
                "Company": ncr.company,
                "Project": ncr.project,
                "Location": ncr.location,
                "Discipline": ncr.discipline,
                "Description": ncr.description,
                "Status": ncr.status,
                "Created By": ncr.created_by,
                "Image": ncr.image_path,
                ## Show Approval Data in Dashboard
                "Approver": ncr.approver,
                "Approval Comment": ncr.approval_comment
            })

        # SAFE DATAFRAME CREATION
        if len(data) > 0:
            df_all = pd.DataFrame(data)

        else:
            df_all = pd.DataFrame(columns=[
                "ID",
                "Company",
                "Project",
                "Location",
                "Discipline",
                "Description",
                "Status",
                "Created By",
                "Image"
            ])


        ## 🔥 PROJECT FILTER

        projects = ["All"] + sorted(
            df_all["Project"].dropna().unique().tolist()
        )

        selected_project = st.selectbox(
            "Filter by Project",
            projects
        )

        # ----------------------------
        # 2. FILTER
        # ----------------------------

        filter_status = st.selectbox(
            "Filter by Status",
            ["All", "Open", "Under Review", "Corrected", "Closed"]
        )

        if filter_status == "All":
            df = df_all
        else:
            df = df_all[df_all["Status"] == filter_status]


        if selected_project != "All":
            df = df[df["Project"] == selected_project]


        # ----------------------------
        # 3. KPIs
        # ----------------------------

        st.subheader("📊 NCR Key Metrics")

        total = len(df_all)
        open_ncr = len(df_all[df_all["Status"] == "Open"])
        closed_ncr = len(df_all[df_all["Status"] == "Closed"])
        under_review = len(df_all[df_all["Status"] == "Under Review"])

        col1, col2, col3, col4 = st.columns(4)

        col1.metric("Total NCRs", total)
        col2.metric("Open", open_ncr)
        col3.metric("Under Review", under_review)
        col4.metric("Closed", closed_ncr)

        # ----------------------------
        # 4. CHARTS
        # ----------------------------

        st.subheader("📊 NCR Status Distribution")

        status_counts = df_all["Status"].value_counts()
        fig, ax = plt.subplots()
        ax.bar(status_counts.index, status_counts.values)
        st.pyplot(fig)

        st.subheader("🏗 NCR by Discipline")

        disc_counts = df_all["Discipline"].value_counts()
        fig2, ax2 = plt.subplots()
        ax2.bar(disc_counts.index, disc_counts.values)
        st.pyplot(fig2)

        # ----------------------------
        # 4. AI Insights Section
        # ----------------------------

        st.subheader("🧠 AI Project Insights")

        if st.button("Generate AI Insights"):

            ncr_summary = ""

            for _, row in df_all.iterrows():

                ncr_summary += f"""
                Discipline: {row['Discipline']}
                Status: {row['Status']}
                Description: {row['Description']}
                """

            prompt = f"""
            You are a senior construction QA/QC manager.

            Analyze these NCR records and provide:

            1. Most common issues
            2. Quality performance observations
            3. Risk observations
            4. Recommendations to management

            NCR Data:
            {ncr_summary}

            Keep response professional and concise.
            """

            response = client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            insights = response.choices[0].message.content

            st.success("AI Insights Generated")

            st.write(insights)

        # ----------------------------
        # 5. TABLE
        # ----------------------------

        st.subheader("📋 NCR Records")
        
        if len(df) == 0:
            st.warning("No NCR records found.")
        else:
            st.dataframe(df, use_container_width=True)
        
        # ----------------------------
        # 6. PDF Export
        # ----------------------------

        st.subheader("📄 Export Report")

        if st.button("Generate PDF Report"):

            pdf_path = generate_pdf(df)

            with open(pdf_path, "rb") as file:

                st.download_button(
                    label="Download NCR PDF Report",
                    data=file.read(),
                    file_name="NCR_Report.pdf",
                    mime="application/pdf"
                )

        # ----------------------------
        # 6. UPDATE STATUS
        # ----------------------------

        st.subheader("🔧 Update NCR Status")

        if len(df_all) > 0:

            ncr_ids = df_all["ID"].tolist()

            selected_id = st.selectbox("Select NCR ID", ncr_ids)

            new_status = st.selectbox(
                "Change Status",
                ["Open", "Under Review", "Corrected", "Closed"]
            )

            if st.button("Update Status"):

                ncr = db.query(NCR).filter(NCR.id == selected_id).first()

                if ncr:
                    ncr.status = new_status
                    db.commit()
                    st.success("Status Updated Successfully!")


        # ----------------------------
        # 6. Add Approval Section in Dashboard
        # ----------------------------

        st.subheader("✅ Approval Workflow")

        approval_comment = st.text_area(
            "Approval Comment"
        )

        approver_name = st.text_input(
            "Approver Name"
        )

        approval_status = st.selectbox(
            "Approval Decision",
            ["Approved", "Rejected", "Closed"]
        )

        # ----------------------------
        # 6. Save Approval
        # ----------------------------

        if st.button("Submit Approval"):

            ncr = db.query(NCR).filter(
                NCR.id == selected_id
            ).first()

            if ncr:

                ncr.status = approval_status

                ncr.approver = approver_name

                ncr.approval_comment = approval_comment

                db.commit()

                st.success("Approval Submitted Successfully!")

elif authentication_status == False:
    st.error("Incorrect username/password")

elif authentication_status == None:
    st.warning("Please login")