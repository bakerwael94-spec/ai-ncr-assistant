import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

from database import NCR
from services.pdf_service import generate_pdf


def show_dashboard(db, role, client):

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
            "Image",
            "Approver",
            "Approval Comment"
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

    if role in ["qa", "admin"]:

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


        if st.button("Submit Approval"):

            ncr = db.query(NCR).filter(NCR.id == selected_id).first()

            if ncr:

                ncr.status = approval_status
                ncr.approver = approver_name
                ncr.approval_comment = approval_comment

                db.commit()

                st.success("Approval Updated Successfully!")

    else:

        st.warning("You do not have permission to approve NCRs")
