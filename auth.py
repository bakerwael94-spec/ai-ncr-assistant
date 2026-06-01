# auth.py

import streamlit_authenticator as stauth


credentials = {
    "usernames": {
        "engineer1": {
            "name": "Site Engineer",
            "password": "1234",
            "role": "engineer"
        },
        "qa1": {
            "name": "QA Manager",
            "password": "1234",
            "role": "qa"
        },
        "admin": {
            "name": "Admin",
            "password": "1234",
            "role": "admin"
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

