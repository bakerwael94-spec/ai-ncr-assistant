# email_service.py

import streamlit as st
import smtplib

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart




def send_email(subject, body, to_email):

    from_email = st.secrets["EMAIL_ADDRESS"]
    app_password = st.secrets["EMAIL_PASSWORD"]

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