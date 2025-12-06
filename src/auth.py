import streamlit as st
import requests
import urllib.parse
import os
from typing import List

# Constants
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USER_INFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"

def get_config():
    """Get auth config from secrets."""
    if "google_auth" not in st.secrets:
        st.error("Missing [google_auth] section in .streamlit/secrets.toml")
        st.stop()
    return st.secrets["google_auth"]

def mock_login():
    """Simulate login for testing/demo purposes."""
    st.markdown("### 🛠️ Mock Login Mode")
    st.info("OAuth credentials are not configured or `mock_mode = true`.")
    
    email = st.text_input("Enter Email for testing", value="admin@bloq.it")
    if st.button("Simulate Login"):
        st.session_state["username"] = email
        st.session_state["email"] = email
        st.session_state["authentication_status"] = True
        st.rerun()

def check_authentication():
    """
    Main authentication flow.
    Returns True if authenticated, else handles the login flow and returns False.
    """
    if "authentication_status" not in st.session_state:
        st.session_state["authentication_status"] = None

    if st.session_state["authentication_status"]:
        return True

    # Check for Mock Mode
    config = get_config()
    if config.get("mock_mode", False):
        mock_login()
        return False

    # Check for OAuth Code in URL
    if "code" in st.query_params:
        code = st.query_params["code"]
        exchange_token(code)
        # Clear query params to clean URL
        st.query_params.clear()
        st.rerun()
        return False # Rerun will re-enter with auth status True

    # Show Login Button
    login_button()
    return False

def login_button():
    """Render the 'Sign in with Google' button."""
    config = get_config()
    
    params = {
        "client_id": config["client_id"],
        "redirect_uri": config["redirect_uri"],
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "online"
    }
    auth_url = f"{GOOGLE_AUTH_URL}?{urllib.parse.urlencode(params)}"
    
    # New UI Layout
    col1, col2 = st.columns([1, 1])
    
    with col1:
        # Product Image
        if os.path.exists("assets/locker_hero.jpg"):
            st.image("assets/locker_hero.jpg", use_container_width=True)
        else:
            # Fallback if image copy failed
            st.info("Product image not found.")
            
    with col2:
        st.markdown("<div style='height: 50px'></div>", unsafe_allow_html=True) # Spacer
        st.markdown("# D&M Diagnostic Dashboard")
        st.markdown("### Secure Access")
        st.markdown("Please sign in with your authorized Google account to access the dashboard.")
        
        st.markdown(f"""
            <a href="{auth_url}" target="_self" style="text-decoration:none;">
                <div style="
                    display: flex;
                    align-items: center;
                    justify_content: center;
                    background-color: white;
                    color: #3c4043;
                    border: 1px solid #dadce0;
                    border-radius: 4px;
                    padding: 10px 24px;
                    font-family: 'Google Sans', arial, sans-serif;
                    font-weight: 500;
                    cursor: pointer;
                    box-shadow: 0 1px 2px 0 rgba(60,64,67,0.3), 0 1px 3px 1px rgba(60,64,67,0.15);
                    width: 100%;
                    max-width: 300px;
                    margin-top: 20px;
                ">
                    <img src="https://upload.wikimedia.org/wikipedia/commons/5/53/Google_%22G%22_Logo.svg" 
                         style="width: 18px; height: 18px; margin-right: 12px;">
                    Sign in with Google
                </div>
            </a>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        st.caption("🔒 Authorized Access Only")

def exchange_token(code: str):
    """Exchange auth code for access token and user info."""
    config = get_config()
    
    try:
        # 1. Get Token
        data = {
            "code": code,
            "client_id": config["client_id"],
            "client_secret": config["client_secret"],
            "redirect_uri": config["redirect_uri"],
            "grant_type": "authorization_code"
        }
        r = requests.post(GOOGLE_TOKEN_URL, data=data)
        r.raise_for_status()
        tokens = r.json()
        
        # 2. Get User Info
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}
        user_info = requests.get(GOOGLE_USER_INFO_URL, headers=headers).json()
        
        # 3. Store Session
        st.session_state["username"] = user_info.get("email")
        st.session_state["email"] = user_info.get("email")
        st.session_state["user_info"] = user_info
        st.session_state["authentication_status"] = True
        
    except Exception as e:
        st.error(f"Authentication Failed: {str(e)}")
        st.session_state["authentication_status"] = False

import sys

# Add src to path to import GoogleSheetsClient if needed, 
# though usually it's in the same package context if running from root.
# We'll import it assuming it's available in python path or relatively.
# If running via streamlit run src/dashboard.py, src is in path probably?
# Let's adjust sys path to be safe
sys.path.insert(0, os.path.dirname(__file__))
from google_sheets_client import GoogleSheetsClient

# ... existing imports ...

@st.cache_data(ttl=600)  # Cache for 10 minutes
def get_permissions_from_sheet() -> dict:
    """Fetch user permissions from Google Sheet."""
    try:
        client = GoogleSheetsClient()
        return client.get_user_permissions_map()
    except Exception as e:
        print(f"Error fetching permissions: {e}")
        return {}

def get_user_permissions(email: str) -> List[str]:
    """
    Get list of accessible countries for the user email.
    Prioritizes Google Sheet -> Fallback to secrets.toml.
    """
    # 1. Check Google Sheet (Dynamic)
    sheet_permissions = get_permissions_from_sheet()
    if email in sheet_permissions:
        return sheet_permissions[email]
        
    # 2. Fallback to Secrets (Static)
    if "permissions" in st.secrets:
        # Check for exact match
        if email in st.secrets["permissions"]:
            return st.secrets["permissions"][email]
            
    return []

def logout():
    """Log out the current user."""
    st.session_state.clear()
    st.query_params.clear()
    st.rerun()
