import os
import urllib.parse

import streamlit as st

from database import get_business_config, init_db

# Initialize the database on load
init_db()

# --- CONFIGURATION ---
TIKTOK_CLIENT_KEY = os.getenv("TIKTOK_CLIENT_KEY", "")


def _resolve_tiktok_redirect_uri() -> str:
    backend_public_url = os.getenv("BACKEND_PUBLIC_URL", "").strip()
    if backend_public_url:
        return f"{backend_public_url.rstrip('/')}/oauth/tiktok/callback"
    return os.getenv("TIKTOK_REDIRECT_URI") or "http://localhost:8000/oauth/tiktok/callback"


# --- HELPER FUNCTIONS ---
def get_tiktok_auth_url(user_email: str | None = None):
    base_url = "https://www.tiktok.com/v2/auth/authorize/"
    state = user_email or st.session_state.get("user_email") or "saintvellian_auth"
    params = {
        "client_key": TIKTOK_CLIENT_KEY,
        "scope": "user.info.basic,video.list,item.comment.reply",
        "response_type": "code",
        "redirect_uri": _resolve_tiktok_redirect_uri(),
        "state": state,
    }
    return f"{base_url}?{urllib.parse.urlencode(params)}"


# --- STREAMLIT UI ---
st.set_page_config(page_title="Saintvellian AI | Onboarding", layout="wide")

st.title("🚀 Saintvellian AI Business Dashboard")
st.markdown("---")

# Use tabs to separate "Onboarding" from "Live Monitoring"
tab1, tab2 = st.tabs(["🆕 Client Onboarding", "📊 Live Activity"])

with tab1:
    st.header("Register New Business")

    with st.form("onboarding_form"):
        col1, col2 = st.columns(2)

        with col1:
            name = st.text_input("Business Name", placeholder="e.g. Nairobi Car Dealership")
            phone_id = st.text_input("WhatsApp Phone Number ID (15 digits)")
            ai_key = st.text_input("AI API Key", type="password")

        with col2:
            token = st.text_input("WhatsApp Access Token", type="password")
            prompt = st.text_area("AI Persona (System Prompt)", placeholder="You are a helpful assistant for...")

        submitted = st.form_submit_button("Complete Onboarding")

        if submitted:
            if name and phone_id and token:
                st.success(f"✅ Business '{name}' registered successfully!")
            else:
                st.error("Please fill in the required fields (Name, Phone ID, Token).")

    st.markdown("---")
    st.header("🔗 Platform Connections")
    st.write("Link this business to other social platforms:")

    c1, c2, c3 = st.columns(3)
    with c1:
        auth_url = get_tiktok_auth_url()
        st.link_button("🎵 Connect TikTok", auth_url)
    with c2:
        st.button("📘 Connect Facebook (Coming Soon)", disabled=True)
    with c3:
        st.button("📸 Connect Instagram (Coming Soon)", disabled=True)

with tab2:
    st.header("Recent AI Interactions")
    st.info("Live feed will appear here once interactions begin.")

    if st.button("Refresh Data"):
        st.rerun()
