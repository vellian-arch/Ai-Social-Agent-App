import main
import streamlit as st
import pandas as pd
import requests
import base64
import os
from datetime import datetime
import time
import random
import math
import uuid
from pathlib import Path
from textwrap import dedent
from urllib.parse import urlencode
from streamlit_option_menu import option_menu

_STREAMLIT_RERUN = getattr(st, "rerun", None)
_STREAMLIT_EXPERIMENTAL_RERUN = getattr(st, "experimental_rerun", None)


def rerun_app():
    if callable(_STREAMLIT_RERUN):
        return _STREAMLIT_RERUN()
    if callable(_STREAMLIT_EXPERIMENTAL_RERUN):
        return _STREAMLIT_EXPERIMENTAL_RERUN()
    raise RuntimeError("Streamlit rerun is not available in this environment.")


st.rerun = rerun_app

# =============================================================================
# CONFIGURATION
# =============================================================================
APP_ICON_PATH = Path(__file__).resolve().parent / "assets" / "social_ai_agent_logo.svg"
st.set_page_config(
    page_title="Social Ai Agent",
    page_icon=str(APP_ICON_PATH),
    layout="wide",
    initial_sidebar_state="expanded"
)

# Backend API base URL
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
FRONTEND_APP_URL = os.getenv("FRONTEND_APP_URL", "http://localhost:8501")
BACKEND_DOC_URL = API_BASE_URL if not API_BASE_URL.startswith(("http://localhost", "http://127.0.0.1")) else "Configured backend URL"
UPLOADS_DIR = Path(__file__).resolve().parents[3] / "uploads"

# Initialize session state
if "current_page" not in st.session_state:
    st.session_state.current_page = "Dashboard"
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "theme" not in st.session_state:
    st.session_state.theme = "dark"
if "language" not in st.session_state:
    st.session_state.language = "en"
if "user_name" not in st.session_state:
    st.session_state.user_name = ""
if "user_email" not in st.session_state:
    st.session_state.user_email = ""
if "user_role" not in st.session_state:
    st.session_state.user_role = ""
if "subscription_status" not in st.session_state:
    st.session_state.subscription_status = "inactive"
if "platform_status" not in st.session_state:
    st.session_state.platform_status = {
        "TikTok": "Available",
        "YouTube": "Available",
        "WhatsApp": "Available",
        "Telegram": "Available",
        "Facebook": "Available",
        "Instagram": "Available"
    }
if "notifications" not in st.session_state:
    st.session_state.notifications = []
if "leads_count" not in st.session_state:
    st.session_state.leads_count = 156
if "conversations_count" not in st.session_state:
    st.session_state.conversations_count = 89
if "products" not in st.session_state:
    st.session_state.products = []
if "product_memory" not in st.session_state:
    st.session_state.product_memory = {}
if "media_items" not in st.session_state:
    st.session_state.media_items = []  # For TikTok/Instagram/Facebook videos/photos
if "platform_conversations" not in st.session_state:
    st.session_state.platform_conversations = {
        "WhatsApp": [],
        "TikTok": [],
        "YouTube": [],
        "Telegram": [],
        "Facebook": [],
        "Instagram": []
    }
if "youtube_videos" not in st.session_state:
    st.session_state.youtube_videos = []  # YouTube videos with comments
if "selected_chat" not in st.session_state:
    st.session_state.selected_chat = None
if "selected_platform" not in st.session_state:
    st.session_state.selected_platform = "WhatsApp"
if "clients" not in st.session_state:
    st.session_state.clients = []
if "billing_info" not in st.session_state:
    st.session_state.billing_info = {
        "plan": None,
        "plan_key": "",
        "platforms": [],
        "status": "Inactive",
        "next_billing": None,
        "payment_method": None,
        "paypal_order_id": "",
        "paypal_payment_link": "",
        "paystack_session_id": "",
        "paystack_payment_link": "",
        "dodo_payment_id": "",
        "dodo_payment_link": "",
    }
if "doc_section" not in st.session_state:
    st.session_state.doc_section = "Getting Started"
if "typing_status" not in st.session_state:
    st.session_state.typing_status = {}
if "chat_search_input" not in st.session_state:
    st.session_state.chat_search_input = ""
if "platform_filter" not in st.session_state:
    st.session_state.platform_filter = "All"
if "chat_product" not in st.session_state:
    st.session_state.chat_product = "None"
if "reply_input" not in st.session_state:
    st.session_state.reply_input = ""
if "show_register" not in st.session_state:
    st.session_state.show_register = False
if "show_forgot_password" not in st.session_state:
    st.session_state.show_forgot_password = False
if "reset_email" not in st.session_state:
    st.session_state.reset_email = ""
if "show_landing" not in st.session_state:
    st.session_state.show_landing = True
if "profile_name" not in st.session_state:
    st.session_state.profile_name = ""
if "profile_phone" not in st.session_state:
    st.session_state.profile_phone = "+1 (555) 123-4567"
if "profile_company" not in st.session_state:
    st.session_state.profile_company = "AI Solutions Inc."
if "profile_timezone" not in st.session_state:
    st.session_state.profile_timezone = "UTC-5 (EST)"
if "profile_country" not in st.session_state:
    st.session_state.profile_country = "Global / Other"
if "profile_country_source" not in st.session_state:
    st.session_state.profile_country_source = "auto"
if "email_alerts" not in st.session_state:
    st.session_state.email_alerts = True
if "push_notifications" not in st.session_state:
    st.session_state.push_notifications = True
if "sms_alerts" not in st.session_state:
    st.session_state.sms_alerts = False
if "daily_summary" not in st.session_state:
    st.session_state.daily_summary = True
if "weekly_report" not in st.session_state:
    st.session_state.weekly_report = False
if "system_updates" not in st.session_state:
    st.session_state.system_updates = True
if "refresh_rate" not in st.session_state:
    st.session_state.refresh_rate = 60
if "timeout" not in st.session_state:
    st.session_state.timeout = 30
if "cache_size" not in st.session_state:
    st.session_state.cache_size = 500
if "selected_platforms" not in st.session_state:
    st.session_state.selected_platforms = []
if "api_cache" not in st.session_state:
    st.session_state.api_cache = {}
if "platform_credentials_loaded_at" not in st.session_state:
    st.session_state.platform_credentials_loaded_at = 0.0


def ensure_session_state():
    defaults = {
        "current_page": "Dashboard",
        "logged_in": False,
        "theme": "dark",
        "language": "en",
        "user_name": "",
        "user_email": "",
        "user_role": "",
        "subscription_status": "inactive",
        "auth_token": "",
        "platform_status": {
            "TikTok": "Available",
            "YouTube": "Available",
            "WhatsApp": "Available",
            "Telegram": "Available",
            "Facebook": "Available",
            "Instagram": "Available",
        },
        "notifications": [],
        "leads_count": 156,
        "conversations_count": 89,
        "products": [],
        "product_memory": {},
        "media_items": [],
        "platform_conversations": {
            "WhatsApp": [],
            "TikTok": [],
            "YouTube": [],
            "Telegram": [],
            "Facebook": [],
            "Instagram": [],
        },
        "platform_credentials": {},
        "youtube_videos": [],
        "clients": [],
        "billing_info": {
            "plan": None,
            "plan_key": "",
            "platforms": [],
            "status": "Inactive",
            "next_billing": None,
            "payment_method": None,
            "dodo_payment_id": "",
            "dodo_payment_link": "",
            "paypal_order_id": "",
            "paypal_payment_link": "",
            "paystack_session_id": "",
            "paystack_payment_link": "",
        },
        "doc_section": "Getting Started",
        "typing_status": {},
        "show_register": False,
        "show_forgot_password": False,
        "show_landing": True,
        "reset_email": "",
        "selected_platforms": [],
        "chat_search_input": "",
        "reply_input": "",
        "chat_product": "None",
        "platform_filter": "All",
        "selected_chat": None,
        "selected_platform": "WhatsApp",
        "profile_name": "",
        "profile_phone": "+1 (555) 123-4567",
        "profile_company": "AI Solutions Inc.",
        "profile_timezone": "UTC-5 (EST)",
        "profile_country": "Global / Other",
        "profile_country_source": "auto",
        "email_alerts": True,
        "push_notifications": True,
        "sms_alerts": False,
        "daily_summary": True,
        "weekly_report": False,
        "system_updates": True,
        "refresh_rate": 60,
        "timeout": 30,
        "cache_size": 500,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            if isinstance(value, list):
                st.session_state[key] = value.copy()
            elif isinstance(value, dict):
                st.session_state[key] = value.copy()
            else:
                st.session_state[key] = value

# =============================================================================
# PLATFORM PRICING
# =============================================================================
PLATFORM_PRICES = {
    1: 30,   # 1 platform
    2: 50,   # 2 platforms
    3: 80,   # 3 platforms
    4: 100,  # 4 platforms
    5: 120,  # 5 platforms
    6: 130   # All 6 platforms
}

PLATFORM_LIST = ["WhatsApp", "TikTok", "YouTube", "Telegram", "Facebook", "Instagram"]

PAYSTACK_SUPPORTED_COUNTRIES = {
    "algeria",
    "angola",
    "benin",
    "botswana",
    "burkina faso",
    "burundi",
    "cabo verde",
    "cameroon",
    "central african republic",
    "chad",
    "comoros",
    "cote d'ivoire",
    "democratic republic of the congo",
    "djibouti",
    "egypt",
    "equatorial guinea",
    "eritrea",
    "eswatini",
    "ethiopia",
    "gabon",
    "gambia",
    "ghana",
    "guinea",
    "guinea-bissau",
    "kenya",
    "lesotho",
    "liberia",
    "libya",
    "madagascar",
    "malawi",
    "mali",
    "mauritania",
    "mauritius",
    "morocco",
    "mozambique",
    "namibia",
    "niger",
    "nigeria",
    "republic of the congo",
    "rwanda",
    "sao tome and principe",
    "senegal",
    "seychelles",
    "sierra leone",
    "somalia",
    "south africa",
    "south sudan",
    "sudan",
    "tanzania",
    "togo",
    "tunisia",
    "uganda",
    "zambia",
    "zimbabwe",
}

COUNTRY_OPTIONS = [
    "Global / Other",
    "Nigeria",
    "Ghana",
    "Kenya",
    "South Africa",
    "Egypt",
    "Morocco",
    "Rwanda",
    "Uganda",
    "Tanzania",
    "Zambia",
    "Zimbabwe",
    "Senegal",
    "Cameroon",
    "Cote d'Ivoire",
    "Algeria",
    "Botswana",
    "Benin",
    "Burkina Faso",
    "Burundi",
    "Cabo Verde",
    "Chad",
    "Comoros",
    "Democratic Republic of the Congo",
    "Republic of the Congo",
    "Djibouti",
    "Equatorial Guinea",
    "Eritrea",
    "Eswatini",
    "Ethiopia",
    "Gabon",
    "Gambia",
    "Guinea",
    "Guinea-Bissau",
    "Lesotho",
    "Liberia",
    "Libya",
    "Madagascar",
    "Malawi",
    "Mali",
    "Mauritania",
    "Mauritius",
    "Mozambique",
    "Namibia",
    "Niger",
    "Sao Tome and Principe",
    "Seychelles",
    "Sierra Leone",
    "Somalia",
    "South Sudan",
    "Sudan",
    "Tunisia",
]


def _normalize_country_name(value: str) -> str:
    return (value or "").strip().lower()


def is_paystack_supported_country(country: str) -> bool:
    normalized = _normalize_country_name(country)
    if not normalized or normalized in {"global / other", "global", "other"}:
        return False
    return normalized in PAYSTACK_SUPPORTED_COUNTRIES


def get_billing_country() -> str:
    country = (st.session_state.get("profile_country") or "").strip()
    return country or "Global / Other"


def get_available_payment_rails(
    country: str | None = None,
    *,
    paypal_live: bool = False,
    dodo_live: bool = False,
    paystack_live: bool = False,
) -> list[str]:
    selected_country = country or get_billing_country()
    rails: list[str] = []
    if paypal_live:
        rails.append("PayPal")
    if dodo_live:
        rails.append("Dodo")
    if paystack_live and is_paystack_supported_country(selected_country):
        rails.append("Paystack")
    return rails


def normalize_country_option(value: str) -> str:
    normalized = _normalize_country_name(value)
    for option in COUNTRY_OPTIONS:
        if _normalize_country_name(option) == normalized:
            return option
    return "Global / Other"


def sync_billing_country_from_backend(force: bool = False) -> str:
    if st.session_state.get("profile_country_source") == "manual" and not force:
        return st.session_state.get("profile_country", "Global / Other")
    payload = api_get("/api/deployment/country") or {}
    detected_country = normalize_country_option(payload.get("country", ""))
    if detected_country != "Global / Other":
        st.session_state.profile_country = detected_country
        st.session_state.profile_country_source = "auto"
    return st.session_state.get("profile_country", "Global / Other")

PLATFORM_CONNECTION_FIELDS = {
    "WhatsApp": [
        ("phone_id", "Phone Number ID", "Enter the WhatsApp Business phone number ID"),
        ("whatsapp_token", "Access Token", "Paste the WhatsApp Cloud API access token"),
    ],
    "TikTok": [
        ("tiktok_open_id", "Open ID", "Enter the TikTok business open_id"),
        ("tiktok_access_token", "Access Token", "Paste the TikTok access token"),
        ("tiktok_refresh_token", "Refresh Token", "Paste the TikTok refresh token"),
        ("tiktok_shop_id", "Shop ID", "Optional if TikTok Shop is connected"),
    ],
    "YouTube": [
        ("youtube_channel_id", "Channel ID", "Enter the YouTube channel ID"),
        ("youtube_token", "Access Token", "Paste the Google access token"),
        ("youtube_refresh_token", "Refresh Token", "Paste the Google refresh token"),
    ],
    "Telegram": [
        ("telegram_bot_token", "Bot Token", "Paste the token from BotFather"),
    ],
    "Facebook": [
        ("fb_page_id", "Page ID", "Enter the Facebook Page ID"),
        ("fb_page_token", "Page Access Token", "Paste the Facebook Page access token"),
    ],
    "Instagram": [
        ("fb_page_id", "Linked Page ID", "Enter the Facebook Page ID linked to the Instagram business account"),
        ("fb_page_token", "Page Access Token", "Paste the Page access token for Instagram messaging"),
    ],
}

# =============================================================================
# BACKEND API HELPER FUNCTIONS
# =============================================================================
def api_get(endpoint):
    try:
        headers = {}
        if st.session_state.get("auth_token"):
            headers["Authorization"] = f"Bearer {st.session_state.auth_token}"
        cacheable = endpoint.startswith(("/api/products", "/api/clients", "/api/media", "/api/youtube/videos", "/api/conversations/", "/api/platform-connections", "/api/admin/", "/api/deployment/check", "/api/deployment/country", "/health", "/api/billing/plans"))
        cache_key = (API_BASE_URL, endpoint, st.session_state.get("auth_token", ""))
        cached = st.session_state.api_cache.get(cache_key)
        ttl = 3600 if endpoint.startswith("/api/deployment/country") else 30 if endpoint.startswith(("/api/admin/", "/api/deployment/check", "/health", "/api/billing/plans")) else 15 if endpoint.startswith(("/api/products", "/api/clients", "/api/media", "/api/youtube/videos", "/api/conversations/", "/api/platform-connections")) else 10
        if cacheable and cached and (time.time() - cached["ts"] < ttl):
            return cached["data"]
        response = requests.get(f"{API_BASE_URL}{endpoint}", headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if cacheable:
                st.session_state.api_cache[cache_key] = {"ts": time.time(), "data": data}
            return data
        else:
            return None
    except:
        return None

def api_post(endpoint, data):
    try:
        headers = {}
        if st.session_state.get("auth_token"):
            headers["Authorization"] = f"Bearer {st.session_state.auth_token}"
        response = requests.post(f"{API_BASE_URL}{endpoint}", json=data, headers=headers, timeout=10)
        if response.status_code == 200:
            st.session_state.api_cache = {}
            return response.json()
        else:
            return None
    except:
        return None

def api_post_verbose(endpoint, data):
    try:
        headers = {}
        if st.session_state.get("auth_token"):
            headers["Authorization"] = f"Bearer {st.session_state.auth_token}"
        response = requests.post(f"{API_BASE_URL}{endpoint}", json=data, headers=headers, timeout=10)
        if response.status_code == 200:
            st.session_state.api_cache = {}
            return {"ok": True, "data": response.json()}
        try:
            payload = response.json()
            detail = payload.get("detail") or payload.get("message") or payload.get("error") or response.text
        except Exception:
            detail = response.text
        return {"ok": False, "status_code": response.status_code, "error": detail}
    except Exception as exc:
        return {"ok": False, "status_code": 0, "error": str(exc)}


def api_delete(endpoint):
    try:
        headers = {}
        if st.session_state.get("auth_token"):
            headers["Authorization"] = f"Bearer {st.session_state.auth_token}"
        response = requests.delete(f"{API_BASE_URL}{endpoint}", headers=headers, timeout=10)
        if response.status_code == 200:
            st.session_state.api_cache = {}
            return response.json()
        return None
    except:
        return None

def get_backend_status():
    data = api_get("/health")
    if data and data.get("status") == "ok":
        return "Online", data
    return "Offline", None

def get_theme_tokens():
    ensure_session_state()
    current_theme = st.session_state.get("theme", "dark")
    if current_theme == "dark":
        return {
            "bg": "#101827",
            "card": "#182235",
            "card_alt": "#22314b",
            "text": "#f3f6fb",
            "muted": "#bfd0e6",
            "border": "#30435f",
            "primary": "#79b9f2",
            "secondary": "#b9def8",
            "accent": "#f97316",
            "input": "#132033",
            "sidebar": "#142033",
            "chat": "#1b2940",
            "own_message": "linear-gradient(135deg, #79b9f2, #f97316)",
            "other_message": "#273754",
            "video": "#21304a",
        }
    if current_theme == "blue":
        return {
            "bg": "#dff1fb",
            "card": "#ffffff",
            "card_alt": "#eef8ff",
            "text": "#163a70",
            "muted": "#5173a1",
            "border": "#b7d5ea",
            "primary": "#6fb6f0",
            "secondary": "#b9def8",
            "accent": "#f97316",
            "input": "#f7fcff",
            "sidebar": "#d9eefc",
            "chat": "#f3fbff",
            "own_message": "linear-gradient(135deg, #6fb6f0, #f97316)",
            "other_message": "#e8f5fd",
            "video": "#eaf6fe",
        }
    return {
        "bg": "#fce3b6",
        "card": "#ffffff",
        "card_alt": "#fff4de",
        "text": "#173c73",
        "muted": "#5c6f91",
        "border": "#e7c98f",
        "primary": "#6fb6f0",
        "secondary": "#b9def8",
        "accent": "#f97316",
        "input": "#fffaf1",
        "sidebar": "#fce6bf",
        "chat": "#fff7e8",
        "own_message": "linear-gradient(135deg, #6fb6f0, #f97316)",
        "other_message": "#f8ecd5",
        "video": "#fff1d8",
    }


def render_table_card(title, subtitle, dataframe, empty_text, height=320, columns=None, page_size=None, page_key=None):
    theme = get_theme_tokens()
    st.markdown(
        f"""
        <div style='background:{theme["card"]}; border:1px solid {theme["border"]}; border-radius:22px; padding:18px 18px 12px 18px; margin-bottom:14px; box-shadow:0 14px 34px rgba(0,0,0,0.04);'>
            <div style='display:flex; justify-content:space-between; gap:14px; align-items:flex-start; flex-wrap:wrap; margin-bottom:12px;'>
                <div>
                    <div style='font-size:1rem; font-weight:700; color:{theme["text"]}; margin-bottom:4px;'>{title}</div>
                    <div style='font-size:0.88rem; color:{theme["muted"]}; line-height:1.5;'>{subtitle}</div>
                </div>
                <div style='font-size:0.74rem; text-transform:uppercase; letter-spacing:0.14em; color:{theme["primary"]}; border:1px solid {theme["border"]}; border-radius:999px; padding:7px 12px; background:{theme["card_alt"]};'>
                    Dashboard Table
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if dataframe is None or dataframe.empty:
        st.info(empty_text)
        return
    if columns:
        visible = [column for column in columns if column in dataframe.columns]
        dataframe = dataframe[visible] if visible else dataframe
    if page_size and len(dataframe) > page_size:
        state_key = f"{page_key or title}_page"
        if state_key not in st.session_state:
            st.session_state[state_key] = 1
        total_pages = max(1, math.ceil(len(dataframe) / page_size))
        current_page = min(max(int(st.session_state[state_key]), 1), total_pages)
        start = (current_page - 1) * page_size
        end = start + page_size
        page_df = dataframe.iloc[start:end]
        nav_left, nav_mid, nav_right = st.columns([1, 2, 1])
        with nav_left:
            if st.button("◀ Prev", key=f"{state_key}_prev", use_container_width=True, disabled=current_page <= 1):
                st.session_state[state_key] = current_page - 1
                st.rerun()
        with nav_mid:
            st.caption(f"Showing {start + 1}-{min(end, len(dataframe))} of {len(dataframe)} rows")
        with nav_right:
            if st.button("Next ▶", key=f"{state_key}_next", use_container_width=True, disabled=current_page >= total_pages):
                st.session_state[state_key] = current_page + 1
                st.rerun()
        dataframe = page_df
    st.dataframe(dataframe, use_container_width=True, hide_index=True, height=height)

def enrich_product(product):
    enriched = dict(product)
    enriched.setdefault("category", "General")
    enriched.setdefault("price", enriched.get("price", "0"))
    enriched.setdefault("tags", enriched.get("tags", ""))
    enriched.setdefault("media_url", enriched.get("media_url", ""))
    enriched.setdefault("sku", f"SYNC-{abs(hash(enriched.get('name', 'ITEM'))) % 100000:05d}")
    enriched.setdefault(
        "ai_notes",
        ai_analyze_product(enriched.get("name", "Product"), enriched.get("description", "")),
    )
    enriched.setdefault("inquiries", 0)
    return enriched

def get_message_body(message):
    return message.get("message") or message.get("text") or ""


def normalize_message(message):
    normalized = dict(message or {})
    sender = (normalized.get("sender") or "customer").lower()
    if sender == "ai":
        sender = "agent"
    normalized["sender"] = sender
    normalized["message"] = get_message_body(normalized)
    normalized["time"] = normalized.get("time") or datetime.now().strftime("%I:%M %p")
    normalized["read"] = bool(normalized.get("read", sender != "customer"))
    return normalized


def derive_conversation_preview(messages):
    if not messages:
        return "No messages yet."
    return get_message_body(messages[-1]) or "No messages yet."


def parse_display_time(value):
    text = (value or "").strip()
    if not text:
        return datetime.min
    for fmt in ("%I:%M %p", "%H:%M", "%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    return datetime.min


def conversation_sort_key(conversation):
    parsed = parse_display_time(conversation.get("time"))
    return (
        -int(conversation.get("unread", 0) or 0),
        0 if conversation.get("status") == "new" else 1,
        -parsed.toordinal(),
        -parsed.hour,
        -parsed.minute,
        -parsed.second,
    )


def safe_int(value, default=0):
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def normalize_conversation(conversation, platform):
    normalized = dict(conversation or {})
    normalized["platform"] = platform
    normalized["messages"] = [normalize_message(msg) for msg in normalized.get("messages", [])]
    normalized["id"] = normalized.get("id") or f"{platform.lower()}-{abs(hash(normalized.get('name', 'chat')))%100000}"
    normalized["name"] = normalized.get("name") or f"{platform} Customer"
    normalized["avatar"] = normalized.get("avatar") or "👤"
    normalized["customer"] = normalized.get("customer") or normalized.get("email") or "Direct message"
    normalized["message"] = normalized.get("message") or derive_conversation_preview(normalized["messages"])
    normalized["time"] = normalized.get("time") or (
        normalized["messages"][-1]["time"] if normalized["messages"] else datetime.now().strftime("%I:%M %p")
    )
    normalized["unread"] = int(normalized.get("unread", 0) or 0)
    normalized["status"] = (normalized.get("status") or ("new" if normalized["unread"] else "warm")).lower()
    return normalized


def sync_conversation_to_session(updated_conversation):
    platform = updated_conversation.get("platform")
    if not platform:
        return

    conversations = st.session_state.platform_conversations.get(platform, [])
    for index, existing in enumerate(conversations):
        if existing.get("id") == updated_conversation.get("id"):
            conversations[index] = updated_conversation
            break
    else:
        conversations.append(updated_conversation)

    st.session_state.platform_conversations[platform] = conversations


def append_message_to_conversation(conversation, sender, body):
    if not body.strip():
        return conversation

    normalized = normalize_conversation(conversation, conversation["platform"])
    normalized.setdefault("messages", [])
    normalized["messages"].append(
        normalize_message(
            {
                "sender": sender,
                "message": body.strip(),
                "time": datetime.now().strftime("%I:%M %p"),
                "read": sender != "customer",
            }
        )
    )
    normalized["message"] = body.strip()[:70] + ("..." if len(body.strip()) > 70 else "")
    normalized["time"] = normalized["messages"][-1]["time"]
    if sender == "customer":
        normalized["status"] = "new"
        normalized["unread"] = normalized.get("unread", 0) + 1
    else:
        normalized["status"] = "replied"
        normalized["unread"] = 0
    return normalized

def save_uploaded_file(uploaded_file):
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    safe_name = Path(uploaded_file.name).name
    file_path = UPLOADS_DIR / f"{uuid.uuid4().hex}_{safe_name}"
    file_path.write_bytes(uploaded_file.getbuffer())
    return str(file_path)

def load_products_from_backend():
    if st.session_state.logged_in and st.session_state.user_email:
        data = api_get("/api/products")
        if data and "products" in data:
            products = [enrich_product(p) for p in data["products"]]
            st.session_state.products = products
            st.session_state.product_memory = {p["name"]: p for p in products}

def load_clients_from_backend():
    if st.session_state.logged_in and st.session_state.user_email:
        data = api_get("/api/clients")
        if data and "clients" in data:
            st.session_state.clients = data["clients"]

def load_media_from_backend():
    """Load TikTok/Instagram/Facebook media"""
    if st.session_state.logged_in and st.session_state.user_email:
        data = api_get("/api/media")
        if data and "media" in data:
            st.session_state.media_items = data["media"]

def load_youtube_videos_from_backend():
    """Load YouTube videos with comments"""
    if st.session_state.logged_in and st.session_state.user_email:
        data = api_get("/api/youtube/videos")
        if data and "videos" in data:
            st.session_state.youtube_videos = data["videos"]

def load_platform_conversations():
    """Load conversations from all platforms"""
    if st.session_state.logged_in and st.session_state.user_email:
        for platform in PLATFORM_LIST:
            data = api_get(f"/api/conversations/{platform.lower()}")
            if data and "conversations" in data:
                st.session_state.platform_conversations[platform] = data["conversations"]


def has_required_platform_credentials(platform, credentials):
    platform_fields = PLATFORM_CONNECTION_FIELDS.get(platform, [])
    required_fields = [name for name, _, _ in platform_fields[:]]
    optional_fields = {"tiktok_shop_id"}
    return all((credentials.get(field) or "").strip() for field in required_fields if field not in optional_fields)


def get_connection_health_label(platform, credentials):
    if not has_required_platform_credentials(platform, credentials):
        return "Credentials missing"
    if platform == "YouTube":
        return "Auto-refresh ready" if (credentials.get("youtube_refresh_token") or "").strip() else "Manual reconnect risk"
    if platform == "TikTok":
        return "Auto-refresh ready" if (credentials.get("tiktok_refresh_token") or "").strip() else "Manual reconnect risk"
    if platform in {"Facebook", "Instagram", "WhatsApp"}:
        return "Connected"
    if platform == "Telegram":
        return "Bot token saved"
    return "Connected"


def load_platform_credentials_from_backend(force=False):
    if not st.session_state.logged_in or not st.session_state.user_email:
        return
    if not force and (time.time() - float(st.session_state.get("platform_credentials_loaded_at", 0.0))) < 20:
        return
    data = api_get("/api/platform-connections")
    if not data or "connections" not in data:
        return
    raw_credentials = data["connections"]
    connection_map = {}
    for platform in PLATFORM_LIST:
        fields = PLATFORM_CONNECTION_FIELDS.get(platform, [])
        connection_map[platform] = {field: raw_credentials.get(field, "") for field, _, _ in fields}
        st.session_state.platform_status[platform] = "Connected" if has_required_platform_credentials(platform, connection_map[platform]) else "Available"
    st.session_state.platform_credentials = connection_map
    st.session_state.platform_credentials_loaded_at = time.time()


def log_admin_event(event_type, entity_type, entity_label="", platform="", details=""):
    if not st.session_state.get("logged_in") or not st.session_state.get("user_email"):
        return False
    payload = {
        "user_email": st.session_state.user_email,
        "event_type": event_type,
        "entity_type": entity_type,
        "entity_label": entity_label,
        "platform": platform,
        "details": details,
    }
    result = api_post("/api/admin/events", payload)
    return bool(result and result.get("status") == "success")


def sync_platform_conversations_to_backend(platform):
    if not st.session_state.get("logged_in") or not st.session_state.get("user_email"):
        return False
    conversations = st.session_state.platform_conversations.get(platform, [])
    normalized = [normalize_conversation(conversation, platform) for conversation in conversations]
    payload = {
        "user_email": st.session_state.user_email,
        "conversations": normalized,
    }
    result = api_post(f"/api/conversations/{platform.lower()}", payload)
    return bool(result and result.get("status") == "success")


def send_live_message_to_backend(conversation, message_text):
    normalized = normalize_conversation(conversation, conversation.get("platform", "WhatsApp"))
    payload = {
        "platform": normalized["platform"],
        "conversation_id": normalized["id"],
        "recipient_id": normalized.get("customer", ""),
        "customer_ref": normalized.get("customer", ""),
        "customer_name": normalized.get("name", ""),
        "avatar": normalized.get("avatar", "👤"),
        "message": message_text,
        "allow_demo_fallback": True,
    }
    return api_post("/api/messages/send", payload)

# =============================================================================
# 2 LANGUAGE SUPPORT
# =============================================================================
translations = {
    "en": {
        "app_name": "Social Ai Agent",
        "dashboard": "Dashboard",
        "analytics": "Analytics",
        "connections": "Connections",
        "settings": "Settings",
        "docs": "Docs",
        "welcome": "Welcome back",
        "welcome_message": "Welcome back, {name}!",
        "total_leads": "Total Leads",
        "hot_leads": "Hot Leads",
        "active_platforms": "Active Platforms",
        "conversion_rate": "Conversion Rate",
        "platform_distribution": "Platform Distribution",
        "lead_distribution": "Lead Distribution",
        "recent_leads": "Recent Leads",
        "platform_status": "Platform Status",
        "connect_platforms": "Connect Your Platforms",
        "connected": "Connected",
        "pending": "Pending",
        "available": "Available",
        "connect": "Connect",
        "disconnect": "Disconnect",
        "save_settings": "Save Settings",
        "logout": "Logout",
        "email": "Email",
        "password": "Password",
        "login": "Login",
        "login_button": "Login",
        "register_button": "Register",
        "logging_in": "Logging in...",
        "login_success": "Login successful! Welcome {name}.",
        "login_error": "Invalid email or password. Please try again.",
        "register_success": "Registration successful! Please login.",
        "register_error": "Registration failed. Email may already exist.",
        "profile": "Profile",
        "notifications": "Notifications",
        "system": "System",
        "theme": "Theme",
        "language": "Language",
        "dark": "Dark",
        "light": "Light",
        "hot": "Hot",
        "warm": "Warm",
        "cold": "Cold",
        "search": "Search",
        "refresh": "Refresh",
        "help": "Help",
        "about": "About",
        "version": "v3.0",
        "operator": "Operator",
        "conversations": "Conversations",
        "platform": "Platform",
        "customer": "Customer",
        "message": "Message",
        "score": "Score",
        "time": "Time",
        "connecting": "Connecting...",
        "connected_success": "Connected to {platform} successfully!",
        "disconnected_success": "Disconnected from {platform}",
        "connection_failed": "Connection failed. Please try again.",
        "profile_settings": "Profile Settings",
        "notification_settings": "Notification Settings",
        "system_settings": "System Settings",
        "company": "Company",
        "role": "Role",
        "save_changes": "Save Changes",
        "cancel": "Cancel",
        "confirm": "Confirm",
        "delete": "Delete",
        "edit": "Edit",
        "add": "Add",
        "remove": "Remove",
        "upload": "Upload",
        "download": "Download",
        "filter": "Filter",
        "sort": "Sort",
        "view": "View",
        "details": "Details",
        "summary": "Summary",
        "reports": "Reports",
        "onboard_client": "Onboard",
        "media_center": "Media",
        "product_memory": "Memory",
        "live_chat": "Live Chat",
        "whatsapp": "WhatsApp",
        "upload_product": "Upload Product",
        "product_name": "Product Name",
        "product_description": "Description",
        "product_price": "Price",
        "product_category": "Category",
        "ai_suggestions": "AI Suggestions",
        "select_product": "Select Product",
        "send_reply": "Send Reply",
        "type_message": "Type message...",
        "customer_chat": "Customer Chat",
        "active_chats": "Active Chats",
        "memory_updated": "Product memory updated",
        "ai_analyzing": "AI analyzing...",
        "suggested_reply": "Suggested Reply",
        "features": "Features",
        "integrations": "Integrations",
        "support": "Support",
        "faq": "FAQ",
        "api_docs": "API Docs",
        "webhooks": "Webhooks",
        "rate_limits": "Rate Limits",
        "authentication": "Auth",
        "errors": "Errors",
        "changelog": "Changes",
        "billing": "Billing",
        "plan": "Plan",
        "payment": "Payment",
        "invoice": "Invoice",
        "subscription": "Subscription",
        "unread": "unread",
        "type_here": "Type your message here...",
        "send": "Send",
        "attach": "Attach",
        "emoji": "Emoji",
        "online": "Online",
        "offline": "Offline",
        "last_seen": "Last seen",
        "today": "Today",
        "yesterday": "Yesterday",
        "new_user": "New User?",
        "register_here": "Register here",
        "videos": "Videos",
        "photos": "Photos",
        "comments": "Comments",
        "replied": "Replied",
        "media_gallery": "Media Gallery",
        "youtube_videos": "YouTube Videos",
        "ai_responses": "AI Responses",
        "platform_conversations": "Platform Conversations"
    },
    "es": {
        "app_name": "Social Ai Agent",
        "dashboard": "Panel",
        "analytics": "Análisis",
        "connections": "Conexiones",
        "settings": "Ajustes",
        "docs": "Docs",
        "welcome": "Bienvenido",
        "welcome_message": "¡Bienvenido, {name}!",
        "total_leads": "Total Leads",
        "hot_leads": "Leads Calientes",
        "active_platforms": "Plataformas",
        "conversion_rate": "Tasa Conv.",
        "platform_distribution": "Distribución",
        "lead_distribution": "Distribución Leads",
        "recent_leads": "Leads Recientes",
        "platform_status": "Estado",
        "connect_platforms": "Conectar",
        "connected": "Conectado",
        "pending": "Pendiente",
        "available": "Disponible",
        "connect": "Conectar",
        "disconnect": "Desconectar",
        "save_settings": "Guardar",
        "logout": "Salir",
        "email": "Email",
        "password": "Contraseña",
        "login": "Entrar",
        "login_button": "Entrar",
        "register_button": "Registrar",
        "logging_in": "Entrando...",
        "login_success": "¡Bienvenido {name}!",
        "login_error": "Email o contraseña inválidos",
        "register_success": "¡Registro exitoso! Por favor inicia sesión.",
        "register_error": "Error en registro. El email puede existir.",
        "profile": "Perfil",
        "notifications": "Notif.",
        "system": "Sistema",
        "theme": "Tema",
        "language": "Idioma",
        "dark": "Oscuro",
        "light": "Claro",
        "hot": "Caliente",
        "warm": "Tibio",
        "cold": "Frío",
        "search": "Buscar",
        "refresh": "Actualizar",
        "help": "Ayuda",
        "about": "Info",
        "version": "v3.0",
        "operator": "Operador",
        "conversations": "Charlas",
        "platform": "Plataforma",
        "customer": "Cliente",
        "message": "Mensaje",
        "score": "Score",
        "time": "Hora",
        "connecting": "Conectando...",
        "connected_success": "Conectado a {platform}!",
        "disconnected_success": "Desconectado de {platform}",
        "connection_failed": "Conexión fallida",
        "profile_settings": "Perfil",
        "notification_settings": "Notificaciones",
        "system_settings": "Sistema",
        "company": "Empresa",
        "role": "Rol",
        "save_changes": "Guardar",
        "cancel": "Cancelar",
        "confirm": "Confirmar",
        "delete": "Eliminar",
        "edit": "Editar",
        "add": "Agregar",
        "remove": "Quitar",
        "upload": "Subir",
        "download": "Bajar",
        "filter": "Filtrar",
        "sort": "Ordenar",
        "view": "Ver",
        "details": "Detalles",
        "summary": "Resumen",
        "reports": "Informes",
        "onboard_client": "Registrar",
        "media_center": "Media",
        "product_memory": "Memoria",
        "live_chat": "Chat",
        "whatsapp": "WhatsApp",
        "upload_product": "Subir Producto",
        "product_name": "Producto",
        "product_description": "Descripción",
        "product_price": "Precio",
        "product_category": "Categoría",
        "ai_suggestions": "Sugerencias IA",
        "select_product": "Seleccionar",
        "send_reply": "Enviar",
        "type_message": "Escribe...",
        "customer_chat": "Chat Cliente",
        "active_chats": "Chats Activos",
        "memory_updated": "Memoria actualizada",
        "ai_analyzing": "IA analizando...",
        "suggested_reply": "Respuesta IA",
        "features": "Caract.",
        "integrations": "Integrac.",
        "support": "Soporte",
        "faq": "FAQ",
        "api_docs": "API",
        "webhooks": "Webhooks",
        "rate_limits": "Límites",
        "authentication": "Auth",
        "errors": "Errores",
        "changelog": "Cambios",
        "billing": "Facturación",
        "plan": "Plan",
        "payment": "Pago",
        "invoice": "Factura",
        "subscription": "Suscripción",
        "unread": "no leídos",
        "type_here": "Escribe tu mensaje aquí...",
        "send": "Enviar",
        "attach": "Adjuntar",
        "emoji": "Emoji",
        "online": "En línea",
        "offline": "Desconectado",
        "last_seen": "Visto",
        "today": "Hoy",
        "yesterday": "Ayer",
        "new_user": "¿Nuevo Usuario?",
        "register_here": "Regístrate aquí",
        "videos": "Videos",
        "photos": "Fotos",
        "comments": "Comentarios",
        "replied": "Respondido",
        "media_gallery": "Galería de Medios",
        "youtube_videos": "Videos de YouTube",
        "ai_responses": "Respuestas IA",
        "platform_conversations": "Conversaciones de Plataforma"
    }
}

def locale_pack(**overrides):
    pack = translations["en"].copy()
    pack["app_name"] = "Social Ai Agent"
    pack.update(overrides)
    return pack

LANGUAGE_META = {
    "en": {"label": "English", "flag": "🇺🇸"},
    "es": {"label": "Español", "flag": "🇪🇸"},
    "fr": {"label": "Français", "flag": "🇫🇷"},
    "de": {"label": "Deutsch", "flag": "🇩🇪"},
    "pt": {"label": "Português", "flag": "🇵🇹"},
    "it": {"label": "Italiano", "flag": "🇮🇹"},
    "hi": {"label": "हिन्दी", "flag": "🇮🇳"},
    "ar": {"label": "العربية", "flag": "🇸🇦"},
    "zh": {"label": "中文", "flag": "🇨🇳"},
    "ja": {"label": "日本語", "flag": "🇯🇵"},
    "tr": {"label": "Türkçe", "flag": "🇹🇷"},
    "ru": {"label": "Русский", "flag": "🇷🇺"},
    "sw": {"label": "Kiswahili", "flag": "🇰🇪"},
    "id": {"label": "Bahasa Indonesia", "flag": "🇮🇩"},
}

LANGUAGE_CODES = list(LANGUAGE_META.keys())
translations.update({
    "fr": locale_pack(
        dashboard="Tableau de bord",
        analytics="Analytique",
        connections="Connexions",
        settings="Paramètres",
        docs="Docs",
        welcome="Bienvenue",
        welcome_message="Bon retour, {name} !",
        language="Langue",
        logout="Déconnexion",
        login_button="Connexion",
        register_button="Créer un compte",
        billing="Facturation",
        support="Support",
        profile="Profil",
        system="Système",
        help="Aide",
        search="Rechercher",
        refresh="Actualiser",
        save_changes="Enregistrer les modifications",
        cancel="Annuler",
        confirm="Confirmer",
        delete="Supprimer",
        edit="Modifier",
        upload="Téléverser",
        download="Télécharger",
        features="Fonctionnalités",
        integrations="Intégrations",
        subscription="Abonnement",
        payment="Paiement",
        media_center="Médias",
        live_chat="Chat en direct",
        product_memory="Mémoire produit",
        onboard_client="Onboarding",
        new_user="Nouvel utilisateur ?",
        register_here="Inscrivez-vous ici",
        platform_conversations="Conversations de plateforme",
    ),
    "de": locale_pack(
        dashboard="Dashboard",
        analytics="Analysen",
        connections="Verbindungen",
        settings="Einstellungen",
        docs="Doku",
        welcome="Willkommen",
        welcome_message="Willkommen zurück, {name}!",
        language="Sprache",
        logout="Abmelden",
        login_button="Anmelden",
        register_button="Registrieren",
        billing="Abrechnung",
        support="Support",
        profile="Profil",
        system="System",
        help="Hilfe",
        search="Suchen",
        refresh="Aktualisieren",
        save_changes="Änderungen speichern",
        cancel="Abbrechen",
        confirm="Bestätigen",
        delete="Löschen",
        edit="Bearbeiten",
        upload="Hochladen",
        download="Herunterladen",
        features="Funktionen",
        integrations="Integrationen",
        subscription="Abo",
        payment="Zahlung",
        media_center="Medien",
        live_chat="Live-Chat",
        product_memory="Produktgedächtnis",
        onboard_client="Onboarding",
        new_user="Neuer Benutzer?",
        register_here="Hier registrieren",
        platform_conversations="Plattformgespräche",
    ),
    "pt": locale_pack(
        dashboard="Painel",
        analytics="Análises",
        connections="Conexões",
        settings="Configurações",
        docs="Docs",
        welcome="Bem-vindo",
        welcome_message="Bem-vindo de volta, {name}!",
        language="Idioma",
        logout="Sair",
        login_button="Entrar",
        register_button="Registrar",
        billing="Cobrança",
        support="Suporte",
        profile="Perfil",
        system="Sistema",
        help="Ajuda",
        search="Pesquisar",
        refresh="Atualizar",
        save_changes="Salvar alterações",
        cancel="Cancelar",
        confirm="Confirmar",
        delete="Excluir",
        edit="Editar",
        upload="Enviar",
        download="Baixar",
        features="Recursos",
        integrations="Integrações",
        subscription="Assinatura",
        payment="Pagamento",
        media_center="Mídia",
        live_chat="Chat ao vivo",
        product_memory="Memória do produto",
        onboard_client="Onboarding",
        new_user="Novo usuário?",
        register_here="Cadastre-se aqui",
        platform_conversations="Conversas da plataforma",
    ),
    "it": locale_pack(
        dashboard="Cruscotto",
        analytics="Analisi",
        connections="Connessioni",
        settings="Impostazioni",
        docs="Documenti",
        welcome="Benvenuto",
        welcome_message="Bentornato, {name}!",
        language="Lingua",
        logout="Esci",
        login_button="Accedi",
        register_button="Registrati",
        billing="Fatturazione",
        support="Supporto",
        profile="Profilo",
        system="Sistema",
        help="Aiuto",
        search="Cerca",
        refresh="Aggiorna",
        save_changes="Salva modifiche",
        cancel="Annulla",
        confirm="Conferma",
        delete="Elimina",
        edit="Modifica",
        upload="Carica",
        download="Scarica",
        features="Funzionalità",
        integrations="Integrazioni",
        subscription="Abbonamento",
        payment="Pagamento",
        media_center="Media",
        live_chat="Chat live",
        product_memory="Memoria prodotto",
        onboard_client="Onboarding",
        new_user="Nuovo utente?",
        register_here="Registrati qui",
        platform_conversations="Conversazioni della piattaforma",
    ),
    "hi": locale_pack(
        dashboard="डैशबोर्ड",
        analytics="विश्लेषण",
        connections="कनेक्शन",
        settings="सेटिंग्स",
        docs="दस्तावेज़",
        welcome="स्वागत है",
        welcome_message="फिर से स्वागत है, {name}!",
        language="भाषा",
        logout="लॉग आउट",
        login_button="लॉग इन",
        register_button="रजिस्टर करें",
        billing="बिलिंग",
        support="सहायता",
        profile="प्रोफ़ाइल",
        system="सिस्टम",
        help="मदद",
        search="खोजें",
        refresh="रीफ़्रेश",
        save_changes="परिवर्तन सहेजें",
        cancel="रद्द करें",
        confirm="पुष्टि करें",
        delete="हटाएं",
        edit="संपादित करें",
        upload="अपलोड",
        download="डाउनलोड",
        features="सुविधाएँ",
        integrations="इंटीग्रेशन",
        subscription="सदस्यता",
        payment="भुगतान",
        media_center="मीडिया केंद्र",
        live_chat="लाइव चैट",
        product_memory="उत्पाद मेमोरी",
        onboard_client="ऑनबोर्ड",
        new_user="नया उपयोगकर्ता?",
        register_here="यहां पंजीकरण करें",
        platform_conversations="प्लेटफ़ॉर्म वार्तालाप",
    ),
    "ar": locale_pack(
        dashboard="لوحة التحكم",
        analytics="التحليلات",
        connections="الاتصالات",
        settings="الإعدادات",
        docs="المستندات",
        welcome="مرحبًا",
        welcome_message="مرحبًا بعودتك، {name}!",
        language="اللغة",
        logout="تسجيل الخروج",
        login_button="تسجيل الدخول",
        register_button="تسجيل",
        billing="الفوترة",
        support="الدعم",
        profile="الملف الشخصي",
        system="النظام",
        help="المساعدة",
        search="بحث",
        refresh="تحديث",
        save_changes="حفظ التغييرات",
        cancel="إلغاء",
        confirm="تأكيد",
        delete="حذف",
        edit="تعديل",
        upload="رفع",
        download="تنزيل",
        features="الميزات",
        integrations="التكاملات",
        subscription="الاشتراك",
        payment="الدفع",
        media_center="مركز الوسائط",
        live_chat="الدردشة المباشرة",
        product_memory="ذاكرة المنتج",
        onboard_client="تهيئة",
        new_user="مستخدم جديد؟",
        register_here="سجل هنا",
        platform_conversations="محادثات المنصة",
    ),
    "zh": locale_pack(
        dashboard="仪表盘",
        analytics="分析",
        connections="连接",
        settings="设置",
        docs="文档",
        welcome="欢迎",
        welcome_message="欢迎回来，{name}！",
        language="语言",
        logout="退出登录",
        login_button="登录",
        register_button="注册",
        billing="账单",
        support="支持",
        profile="资料",
        system="系统",
        help="帮助",
        search="搜索",
        refresh="刷新",
        save_changes="保存更改",
        cancel="取消",
        confirm="确认",
        delete="删除",
        edit="编辑",
        upload="上传",
        download="下载",
        features="功能",
        integrations="集成",
        subscription="订阅",
        payment="付款",
        media_center="媒体中心",
        live_chat="直播聊天",
        product_memory="产品记忆",
        onboard_client="客户接入",
        new_user="新用户？",
        register_here="在此注册",
        platform_conversations="平台对话",
    ),
    "ja": locale_pack(
        dashboard="ダッシュボード",
        analytics="分析",
        connections="接続",
        settings="設定",
        docs="ドキュメント",
        welcome="ようこそ",
        welcome_message="おかえりなさい、{name} さん！",
        language="言語",
        logout="ログアウト",
        login_button="ログイン",
        register_button="登録",
        billing="請求",
        support="サポート",
        profile="プロフィール",
        system="システム",
        help="ヘルプ",
        search="検索",
        refresh="更新",
        save_changes="変更を保存",
        cancel="キャンセル",
        confirm="確認",
        delete="削除",
        edit="編集",
        upload="アップロード",
        download="ダウンロード",
        features="機能",
        integrations="連携",
        subscription="サブスク",
        payment="支払い",
        media_center="メディアセンター",
        live_chat="ライブチャット",
        product_memory="商品メモリ",
        onboard_client="オンボード",
        new_user="新規ユーザー？",
        register_here="ここで登録",
        platform_conversations="プラットフォーム会話",
    ),
    "tr": locale_pack(
        dashboard="Gösterge Paneli",
        analytics="Analitik",
        connections="Bağlantılar",
        settings="Ayarlar",
        docs="Dokümanlar",
        welcome="Hoş geldiniz",
        welcome_message="Tekrar hoş geldiniz, {name}!",
        language="Dil",
        logout="Çıkış yap",
        login_button="Giriş yap",
        register_button="Kayıt ol",
        billing="Faturalama",
        support="Destek",
        profile="Profil",
        system="Sistem",
        help="Yardım",
        search="Ara",
        refresh="Yenile",
        save_changes="Değişiklikleri kaydet",
        cancel="İptal",
        confirm="Onayla",
        delete="Sil",
        edit="Düzenle",
        upload="Yükle",
        download="İndir",
        features="Özellikler",
        integrations="Entegrasyonlar",
        subscription="Abonelik",
        payment="Ödeme",
        media_center="Medya Merkezi",
        live_chat="Canlı Sohbet",
        product_memory="Ürün Hafızası",
        onboard_client="Müşteri kaydı",
        new_user="Yeni kullanıcı?",
        register_here="Buradan kaydol",
        platform_conversations="Platform konuşmaları",
    ),
    "ru": locale_pack(
        dashboard="Панель",
        analytics="Аналитика",
        connections="Подключения",
        settings="Настройки",
        docs="Документы",
        welcome="Добро пожаловать",
        welcome_message="С возвращением, {name}!",
        language="Язык",
        logout="Выйти",
        login_button="Войти",
        register_button="Зарегистрироваться",
        billing="Оплата",
        support="Поддержка",
        profile="Профиль",
        system="Система",
        help="Помощь",
        search="Поиск",
        refresh="Обновить",
        save_changes="Сохранить изменения",
        cancel="Отмена",
        confirm="Подтвердить",
        delete="Удалить",
        edit="Изменить",
        upload="Загрузить",
        download="Скачать",
        features="Функции",
        integrations="Интеграции",
        subscription="Подписка",
        payment="Платеж",
        media_center="Медиацентр",
        live_chat="Живой чат",
        product_memory="Память продукта",
        onboard_client="Подключение клиента",
        new_user="Новый пользователь?",
        register_here="Зарегистрируйтесь здесь",
        platform_conversations="Диалоги платформы",
    ),
    "sw": locale_pack(
        dashboard="Dashibodi",
        analytics="Takwimu",
        connections="Miunganisho",
        settings="Mipangilio",
        docs="Nyaraka",
        welcome="Karibu",
        welcome_message="Karibu tena, {name}!",
        language="Lugha",
        logout="Toka",
        login_button="Ingia",
        register_button="Jisajili",
        billing="Utozaji",
        support="Usaidizi",
        profile="Wasifu",
        system="Mfumo",
        help="Msaada",
        search="Tafuta",
        refresh="Onyesha upya",
        save_changes="Hifadhi mabadiliko",
        cancel="Ghairi",
        confirm="Thibitisha",
        delete="Futa",
        edit="Hariri",
        upload="Pakia",
        download="Pakua",
        features="Vipengele",
        integrations="Ujumuishaji",
        subscription="Usajili",
        payment="Malipo",
        media_center="Kituo cha Midia",
        live_chat="Gumzo la Moja kwa Moja",
        product_memory="Kumbukumbu ya Bidhaa",
        onboard_client="Onboard",
        new_user="Mtumiaji mpya?",
        register_here="Jisajili hapa",
        platform_conversations="Mazungumzo ya jukwaa",
    ),
    "id": locale_pack(
        dashboard="Dasbor",
        analytics="Analitik",
        connections="Koneksi",
        settings="Pengaturan",
        docs="Dokumen",
        welcome="Selamat datang",
        welcome_message="Selamat datang kembali, {name}!",
        language="Bahasa",
        logout="Keluar",
        login_button="Masuk",
        register_button="Daftar",
        billing="Penagihan",
        support="Dukungan",
        profile="Profil",
        system="Sistem",
        help="Bantuan",
        search="Cari",
        refresh="Segarkan",
        save_changes="Simpan perubahan",
        cancel="Batal",
        confirm="Konfirmasi",
        delete="Hapus",
        edit="Edit",
        upload="Unggah",
        download="Unduh",
        features="Fitur",
        integrations="Integrasi",
        subscription="Langganan",
        payment="Pembayaran",
        media_center="Pusat Media",
        live_chat="Obrolan Langsung",
        product_memory="Memori Produk",
        onboard_client="Onboarding",
        new_user="Pengguna baru?",
        register_here="Daftar di sini",
        platform_conversations="Percakapan platform",
    ),
})

def t(key, **kwargs):
    language = st.session_state.get("language", "en")
    text = translations.get(language, translations["en"]).get(key, translations["en"].get(key, key))
    if kwargs:
        try:
            text = text.format(**kwargs)
        except:
            pass
    return text

# =============================================================================
# REAL PLATFORM LOGOS (SVG format with official colors)
# =============================================================================
def get_platform_logo(platform, size=32):
    logos = {
        "TikTok": f'''
        <svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M19.59 6.69a4.83 4.83 0 0 1-3.77-4.25V2h-3.45v13.67a2.89 2.89 0 0 1-5.2 1.74 2.89 2.89 0 0 1 2.31-4.64 2.93 2.93 0 0 1 .88.13V9.4a6.84 6.84 0 0 0-1-.05A6.33 6.33 0 0 0 5 20.24a6.34 6.34 0 0 0 10.86-4.43v-7a8.16 8.16 0 0 0 4.77 1.52v-3.4a4.85 4.85 0 0 1-1.04.11v-.11z" fill="#000000"/>
        </svg>
        ''',
        "YouTube": f'''
        <svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M23.5 6.2a3.1 3.1 0 0 0-2.2-2.2C19.5 3.5 12 3.5 12 3.5s-7.5 0-9.3.5A3.1 3.1 0 0 0 .5 6.2 32.7 32.7 0 0 0 0 12a32.7 32.7 0 0 0 .5 5.8 3.1 3.1 0 0 0 2.2 2.2c1.8.5 9.3.5 9.3.5s7.5 0 9.3-.5a3.1 3.1 0 0 0 2.2-2.2c.3-1.9.5-3.9.5-5.8a32.7 32.7 0 0 0-.5-5.8zM9.5 15.5V8.5l6.2 3.5-6.2 3.5z" fill="#FF0000"/>
        </svg>
        ''',
        "WhatsApp": f'''
        <svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M19.1 4.9A10.2 10.2 0 0 0 2 15.7L1 20l4.3-1.1a10.2 10.2 0 0 0 4.9 1.2h0a10.2 10.2 0 0 0 8.9-15.2zM12 19.2h0a8.5 8.5 0 0 1-4.3-1.2l-.3-.2-2.6.7.7-2.5-.2-.3a8.5 8.5 0 0 1 6.7-13 8.5 8.5 0 0 1 8.5 8.5 8.5 8.5 0 0 1-8.5 8.5z" fill="#25D366"/>
            <path d="M16.5 13.3c-.3-.1-1.7-.8-1.9-.9-.3-.1-.5-.1-.7.1-.2.2-.7.9-.9 1.1-.1.2-.3.2-.6.1-1-.3-1.9-.9-2.6-1.6-.5-.5-.9-1.1-1.2-1.8-.1-.3 0-.5.1-.6.1-.1.2-.3.3-.4.1-.1.2-.2.2-.4 0-.1.1-.3 0-.4-.1-.1-.7-1.7-.9-2.3-.2-.5-.5-.5-.7-.5h-.6c-.2 0-.5.1-.8.3-.3.3-.9.9-.9 2.1 0 1.2.9 2.4 1 2.6.1.2 1.7 2.7 4.2 3.7 2.5 1 2.5.7 3 .6.4-.1 1.3-.5 1.5-1 .2-.5.2-.9.1-1-.1-.1-.2-.2-.4-.3z" fill="#25D366"/>
        </svg>
        ''',
        "Telegram": f'''
        <svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M22.3 2.2L1.8 10.5c-1.1.4-1 1.9.1 2.2l4.9 1.5 2.9 8.8c.3.9 1.3 1.3 2.1.8l4.2-3.1c.6-.4 1.3-.5 2-.2l4.5 2.2c.9.4 1.9-.3 1.7-1.3L23.8 3.8c-.2-1-1.2-1.5-2.1-1.1h.6zM9.5 14.5l-.5 4.5 2-3 5-4-6.5-2.5-1 2 1 3z" fill="#0088cc"/>
        </svg>
        ''',
        "Facebook": f'''
        <svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M22.7 0H1.3C.6 0 0 .6 0 1.3v21.4c0 .7.6 1.3 1.3 1.3h11.5v-9.3H9.5v-3.6h3.3V8.4c0-3.3 2-5 4.9-5 1.4 0 2.6.1 2.9.1v3.4h-2c-1.6 0-1.9.8-1.9 1.9v2.5h3.8l-.5 3.6h-3.3V24h6.5c.7 0 1.3-.6 1.3-1.3V1.3c0-.7-.6-1.3-1.3-1.3z" fill="#1877F2"/>
        </svg>
        ''',
        "Instagram": f'''
        <svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M12 2.2c3.2 0 3.6 0 4.9.1 1.2.1 2 .2 2.6.4.6.3 1.1.6 1.6 1.1.5.5.8 1 1.1 1.6.2.6.4 1.4.4 2.6.1 1.3.1 1.7.1 4.9s0 3.6-.1 4.9c-.1 1.2-.2 2-.4 2.6-.3.6-.6 1.1-1.1 1.6-.5.5-1 .8-1.6 1.1-.6.2-1.4.4-2.6.4-1.3.1-1.7.1-4.9.1s-3.6 0-4.9-.1c-1.2-.1-2-.2-2.6-.4-.6-.3-1.1-.6-1.6-1.1-.5-.5-.8-1-1.1-1.6-.2-.6-.4-1.4-.4-2.6-.1-1.3-.1-1.7-.1-4.9s0-3.6.1-4.9c.1-1.2.2-2 .4-2.6.3-.6.6-1.1 1.1-1.6.5-.5 1-.8 1.6-1.1.6-.2 1.4-.4 2.6-.4 1.3 0 1.7-.1 4.9-.1zM12 0C8.7 0 8.3 0 7 .1 5.7.2 4.8.4 4 .7c-.9.3-1.6.7-2.3 1.4C1 2.8.6 3.5.3 4.3.1 5.1 0 6 0 7.2c0 1.3-.1 1.7-.1 5s0 3.7.1 5c.1 1.2.3 2.1.6 2.9.3.8.7 1.6 1.4 2.3.7.7 1.5 1.1 2.3 1.4.8.3 1.7.5 2.9.5 1.3 0 1.7.1 5 .1s3.7 0 5-.1c1.2-.1 2.1-.3 2.9-.6.8-.3 1.6-.7 2.3-1.4.7-.7 1.1-1.5 1.4-2.3.3-.8.5-1.7.5-2.9 0-1.3.1-1.7.1-5s0-3.7-.1-5c-.1-1.2-.3-2.1-.6-2.9-.3-.8-.7-1.6-1.4-2.3C21.2 1 20.4.6 19.6.3c-.8-.3-1.7-.5-2.9-.5C15.4-.1 15-.1 11.7-.1 8.4-.1 8-.1 12 0z" fill="#E4405F"/>
            <path d="M12 5.8c-3.4 0-6.2 2.8-6.2 6.2s2.8 6.2 6.2 6.2 6.2-2.8 6.2-6.2-2.8-6.2-6.2-6.2zm0 10.2c-2.2 0-4-1.8-4-4s1.8-4 4-4 4 1.8 4 4-1.8 4-4 4z" fill="#E4405F"/>
            <circle cx="18.5" cy="5.5" r="1.5" fill="#E4405F"/>
        </svg>
        '''
    }
    return logos.get(platform, f'<div style="width:{size}px;height:{size}px;background:linear-gradient(135deg,#62b6ff,#ff9f5a);border-radius:8px;display:flex;align-items:center;justify-content:center;color:white;font-size:12px;">{platform[0]}</div>')

def get_platform_logo_html(platform, size=32):
    svg = get_platform_logo(platform, size)
    return f'<div style="display: inline-block; vertical-align: middle;">{svg}</div>'


def get_payment_provider_logo(provider, size=32):
    logos = {
        "PayPal": f"""
        <svg width="{size * 2}" height="{size}" viewBox="0 0 96 28" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="PayPal">
            <path d="M20.5 6c-1.6-1.4-3.8-2-6.8-2H5.9c-.5 0-.9.4-1 .8L1.8 24.2c-.1.5.3.8.8.8h4.7l1-6.5h4.4c4.4 0 7.9-2.9 8.5-7.2.3-2.2-.2-3.9-1.7-5.3z" fill="#003087"/>
            <path d="M39.5 6c-1.5-1.3-3.7-2-6.7-2H23.9c-.5 0-1 .4-1 .9L19.8 24.3c-.1.5.3.8.8.8h5.1l.9-5.8h3.9c4.4 0 7.9-2.9 8.5-7.2.3-2.3-.2-4.1-1.5-6.1z" fill="#009CDE"/>
            <path d="M55.3 7.7h-4.9c-.4 0-.8.3-.9.7l-3.1 16c-.1.5.3.9.8.9h4.9c.4 0 .8-.3.9-.7l3.1-16c.1-.5-.3-.9-.8-.9z" fill="#003087"/>
            <path d="M68.2 7.7h-4.9c-.4 0-.8.3-.9.7l-3.1 16c-.1.5.3.9.8.9H65c.4 0 .8-.3.9-.7l3.1-16c.1-.5-.3-.9-.8-.9z" fill="#009CDE"/>
        </svg>
        """,
        "Paystack": f"""
        <svg width="{size * 2}" height="{size}" viewBox="0 0 96 28" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Paystack">
            <rect width="96" height="28" rx="14" fill="#0BA4A6"/>
            <path d="M20 6h8c4.2 0 6.8 2.2 6.8 5.8s-2.8 5.9-7 5.9h-3.8v4.8H20V6zm4 8h3.5c2 0 3.1-.8 3.1-2.2 0-1.6-1.1-2.3-3.1-2.3H24v4.5z" fill="#ffffff"/>
            <path d="M42 12.1h4.2l2.7 7.2 2.8-7.2h4.1L49 24.8h-3.9l-3.1-12.7z" fill="#ffffff"/>
            <path d="M60.4 12.1H64l2.2 6.4 2.2-6.4h3.6l-3.9 12.7h-3.8l-3.9-12.7z" fill="#ffffff"/>
            <path d="M78.2 12.1h3.7v12.7h-3.7V12.1z" fill="#ffffff"/>
        </svg>
        """,
        "Dodo": f"""
        <svg width="{size * 2}" height="{size}" viewBox="0 0 96 28" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Dodo Payments">
            <rect width="96" height="28" rx="14" fill="#F97316"/>
            <circle cx="16" cy="14" r="7" fill="#ffffff"/>
            <path d="M13.5 11.2h3.1c2.7 0 4.6 1.7 4.6 4.2s-1.9 4.4-4.6 4.4h-3.1V11.2zm2.5 6.1h.6c1.2 0 1.9-.7 1.9-1.9 0-1.1-.7-1.8-1.9-1.8H16v3.7z" fill="#F97316"/>
            <path d="M30 10h4.1l2.4 4 2.4-4H43l-4.7 6.8 5 7.2h-4.4l-2.6-4.3-2.6 4.3h-4.1l4.8-7.1L30 10z" fill="#ffffff"/>
            <path d="M48 10h4v14h-4V10z" fill="#ffffff"/>
            <path d="M57.2 10H61v10.6h6V24h-9.8V10z" fill="#ffffff"/>
            <path d="M71 10h4l3.2 6.9V10H82v14h-4l-3.2-6.8V24H71V10z" fill="#ffffff"/>
        </svg>
        """,
    }
    return logos.get(provider, f'<div style="width:{size}px;height:{size}px;background:linear-gradient(135deg,#62b6ff,#ff9f5a);border-radius:8px;display:flex;align-items:center;justify-content:center;color:white;font-size:12px;">{provider[0]}</div>')


def get_payment_provider_logo_html(provider, size=32):
    svg = get_payment_provider_logo(provider, size)
    return f'<div style="display:inline-block; vertical-align:middle;">{svg}</div>'


def get_app_logo_html(size=56):
    try:
        encoded = base64.b64encode(APP_ICON_PATH.read_bytes()).decode("utf-8")
        return f'<img src="data:image/svg+xml;base64,{encoded}" alt="Social Ai Agent" style="width:{size}px;height:{size}px;display:block;" />'
    except Exception:
        return f'<div style="width:{size}px;height:{size}px;border-radius:{size // 4}px;background:linear-gradient(135deg,#0f172a,#1d4ed8);display:flex;align-items:center;justify-content:center;color:#fff;font-weight:800;">SA</div>'


def render_app_topbar():
    st.markdown(
        f"""
        <div class='app-topbar' style='position:sticky; top:0; z-index:999; display:flex; align-items:center; justify-content:space-between; gap:14px; padding:10px 14px; margin:0 0 14px 0; border:1px solid rgba(255,255,255,0.08); border-radius:16px; background:linear-gradient(135deg, rgba(18,28,48,0.94), rgba(14,20,35,0.98)); backdrop-filter: blur(14px); -webkit-backdrop-filter: blur(14px); box-shadow:0 10px 22px rgba(0,0,0,0.14);'>
            <div style='display:flex; align-items:center; gap:10px; min-width:0;'>
                <div style='flex:0 0 auto;'>{get_app_logo_html(34)}</div>
                <div style='min-width:0;'>
                    <div class='app-topbar-subtitle' style='font-size:0.64rem; text-transform:uppercase; letter-spacing:0.16em; color:#8fb7e7; margin-bottom:2px;'>Social Commerce OS</div>
                    <div style='font-size:0.98rem; font-weight:800; color:#f8fafc; line-height:1.05;'>Social Ai Agent</div>
                </div>
            </div>
            <div class='app-topbar-meta' style='flex:0 0 auto; color:#9fb6d6; font-size:0.78rem;'>Unified inbox • AI replies • Monthly billing</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# =============================================================================
# THEME STYLES
# =============================================================================
def apply_styling():
    theme = get_theme_tokens()
    bg_color = theme["bg"]
    card_color = theme["card"]
    card_alt = theme["card_alt"]
    text_color = theme["text"]
    secondary_color = theme["muted"]
    border_color = theme["border"]
    hover_color = theme["primary"]
    input_bg = theme["input"]
    chat_bg = theme["chat"]
    sidebar_bg = theme["sidebar"]
    gradient_start = theme["primary"]
    gradient_mid = theme["secondary"]
    gradient_end = theme["accent"]
    own_message_bg = theme["own_message"]
    other_message_bg = theme["other_message"]
    video_bg = theme["video"]
    
    st.markdown(f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
        
        * {{
            font-family: 'Plus Jakarta Sans', sans-serif;
        }}
        
        .stApp {{
            background-color: {bg_color};
            color: {text_color};
        }}

        .stApp, .stMarkdown, .stText, label, p, span, div {{
            color: {text_color};
        }}

        img, video, canvas, svg, iframe {{
            max-width: 100%;
        }}

        img, video {{
            height: auto;
        }}

        table {{
            width: 100%;
        }}

        strong, b, th {{
            color: {text_color} !important;
            font-weight: 700 !important;
        }}
        
        h1 {{
            font-size: 1.8rem !important;
            font-weight: 700 !important;
            margin-bottom: 0.5rem !important;
        }}
        
        h2 {{
            font-size: 1.5rem !important;
            font-weight: 600 !important;
            margin-bottom: 0.5rem !important;
        }}
        
        h3 {{
            font-size: 1.2rem !important;
            font-weight: 600 !important;
        }}
        
        h4 {{
            font-size: 1rem !important;
            font-weight: 600 !important;
        }}
        
        p, li, .stMarkdown, .stText, .stAlert {{
            font-size: 0.9rem !important;
        }}
        
        .small-text {{
            font-size: 0.8rem !important;
        }}
        
        /* Cards */
        .platform-card, .feature-card, .stat-card, .doc-section, .video-card, .media-card {{
            background: {card_color};
            border: 1px solid {border_color};
            border-radius: 12px;
            padding: 16px;
            margin: 8px 0;
            transition: all 0.2s ease;
        }}
        
        .platform-card:hover, .feature-card:hover, .video-card:hover, .media-card:hover {{
            transform: translateY(-2px);
            border-color: {hover_color};
        }}
        
        /* Video player placeholder */
        .video-placeholder {{
            background: {video_bg};
            border-radius: 8px;
            height: 180px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 3rem;
            color: {secondary_color};
            margin-bottom: 10px;
        }}
        
        /* Media image placeholder */
        .media-image {{
            width: 100%;
            height: 150px;
            object-fit: cover;
            border-radius: 8px;
            background: linear-gradient(135deg, {gradient_start}, {gradient_mid});
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 2rem;
        }}
        
        /* Comment section */
        .comment-section {{
            margin-top: 10px;
            padding: 10px;
            background: {input_bg};
            border-radius: 8px;
            max-height: 200px;
            overflow-y: auto;
        }}
        
        .comment-item {{
            padding: 8px;
            border-bottom: 1px solid {border_color};
            font-size: 0.85rem;
        }}
        
        .comment-item:last-child {{
            border-bottom: none;
        }}
        
        .comment-ai-reply {{
            background: {gradient_start}20;
            padding: 6px;
            border-radius: 6px;
            margin-top: 4px;
            margin-left: 16px;
            font-size: 0.8rem;
            border-left: 2px solid {gradient_start};
        }}
        
        /* Platform connection cards */
        .platform-connection-card {{
            background: {card_color};
            border: 1px solid {border_color};
            border-radius: 12px;
            padding: 12px;
            margin: 8px 0;
            display: flex;
            align-items: center;
            gap: 12px;
            transition: all 0.2s ease;
        }}
        
        .platform-connection-card:hover {{
            border-color: {hover_color};
        }}
        
        .platform-info {{
            flex: 1;
        }}
        
        .platform-name {{
            font-size: 1rem;
            font-weight: 600;
            color: {text_color};
            margin: 0;
        }}
        
        .platform-desc {{
            color: {secondary_color};
            font-size: 0.8rem;
            margin: 4px 0;
        }}
        
        /* Status indicators */
        .status-Connected, .status-Pending, .status-Available,
        .status-hot, .status-warm, .status-cold, .status-new, .status-replied, .status-resolved, .status-pending {{
            font-size: 0.8rem;
            font-weight: 500;
            display: flex;
            align-items: center;
            gap: 4px;
        }}
        
        .status-Connected {{
            color: #10b981;
        }}
        
        .status-Connected::before {{
            content: "●";
            font-size: 1rem;
            animation: pulse 2s infinite;
        }}
        
        .status-Pending {{
            color: #f59e0b;
        }}
        
        .status-Pending::before {{
            content: "◌";
            font-size: 1rem;
            animation: spin 2s linear infinite;
        }}
        
        .status-Available::before {{
            content: "○";
            font-size: 1rem;
        }}

        .status-Available {{
            color: #173c73;
        }}

        .status-hot {{
            color: #ef4444;
        }}

        .status-warm {{
            color: #f59e0b;
        }}

        .status-cold {{
            color: #64748b;
        }}

        .status-new {{
            color: #22c55e;
        }}

        .status-replied {{
            color: {gradient_start};
        }}

        .status-resolved {{
            color: #10b981;
        }}

        .status-pending {{
            color: #f59e0b;
        }}
        
        /* Chat container */
        .chat-container {{
            background: {card_color};
            border: 1px solid {border_color};
            border-radius: 12px;
            padding: 16px;
            height: 400px;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 8px;
        }}
        
        .message-row {{
            display: flex;
            width: 100%;
            margin: 4px 0;
        }}
        
        .message-row.own {{
            justify-content: flex-end;
        }}
        
        .message-row.other {{
            justify-content: flex-start;
        }}
        
        .message-bubble {{
            max-width: 70%;
            padding: 10px 14px;
            border-radius: 18px;
            position: relative;
            word-wrap: break-word;
        }}
        
        .message-bubble.own {{
            background: {own_message_bg};
            color: white;
            border-bottom-right-radius: 4px;
        }}
        
        .message-bubble.other {{
            background: {other_message_bg};
            color: {text_color};
            border-bottom-left-radius: 4px;
        }}
        
        .message-time {{
            font-size: 0.6rem;
            margin-top: 4px;
            opacity: 0.7;
            text-align: right;
        }}
        
        .message-status {{
            font-size: 0.6rem;
            margin-left: 4px;
        }}
        
        /* Chat list items */
        .chat-list-item {{
            background: {card_color};
            border: 1px solid {border_color};
            border-radius: 10px;
            padding: 12px;
            margin: 6px 0;
            cursor: pointer;
            font-size: 0.9rem;
            transition: all 0.2s ease;
            position: relative;
        }}
        
        .chat-list-item:hover, .chat-list-item.selected {{
            border-color: {hover_color};
            background: {input_bg};
        }}
        
        .chat-list-item.selected {{
            border-left: 4px solid {gradient_start};
        }}
        
        .unread-badge {{
            background: {gradient_start};
            color: white;
            border-radius: 12px;
            padding: 2px 8px;
            font-size: 0.7rem;
            font-weight: 600;
            margin-left: 8px;
        }}
        
        /* Platform badge in chat list */
        .platform-badge {{
            font-size: 0.7rem;
            padding: 2px 6px;
            border-radius: 4px;
            background: {gradient_start};
            color: white;
            margin-left: 8px;
        }}
        
        /* Typing indicator */
        .typing-indicator {{
            display: flex;
            gap: 4px;
            padding: 8px 12px;
            background: {other_message_bg};
            border-radius: 18px;
            width: fit-content;
        }}
        
        .typing-dot {{
            width: 8px;
            height: 8px;
            background: {secondary_color};
            border-radius: 50%;
            animation: typing 1.4s infinite ease-in-out;
        }}
        
        .typing-dot:nth-child(1) {{ animation-delay: 0s; }}
        .typing-dot:nth-child(2) {{ animation-delay: 0.2s; }}
        .typing-dot:nth-child(3) {{ animation-delay: 0.4s; }}
        
        @keyframes typing {{
            0%, 60%, 100% {{ transform: translateY(0); opacity: 0.6; }}
            30% {{ transform: translateY(-8px); opacity: 1; }}
        }}
        
        /* Product cards */
        .product-card {{
            background: {card_color};
            border: 1px solid {border_color};
            border-radius: 12px;
            padding: 12px;
            margin: 8px 0;
        }}
        
        .product-image-placeholder {{
            background: linear-gradient(135deg, {gradient_start}, {gradient_mid}, {gradient_end});
            height: 120px;
            border-radius: 8px;
            margin-bottom: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 2rem;
            color: white;
        }}
        
        /* Badges */
        .badge {{
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.7rem;
            font-weight: 500;
            display: inline-block;
        }}
        
        .badge-hot {{
            background: linear-gradient(135deg, #ec4899, #f43f5e);
            color: white;
        }}
        
        .badge-warm {{
            background: linear-gradient(135deg, #f59e0b, #f97316);
            color: white;
        }}
        
        .badge-cold {{
            background: linear-gradient(135deg, #64748b, #475569);
            color: white;
        }}
        
        .badge-new, .ai-badge {{
            background: linear-gradient(135deg, {gradient_start}, {gradient_mid});
            color: white;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.7rem;
            display: inline-block;
        }}
        
        /* Memory indicator */
        .memory-indicator {{
            background: {card_color};
            border: 1px solid {border_color};
            border-radius: 10px;
            padding: 10px;
            margin: 6px 0;
            font-size: 0.9rem;
        }}
        
        /* Metric cards */
        div[data-testid="stMetric"] {{
            background: {card_color};
            border: 1px solid {border_color};
            border-radius: 12px;
            padding: 12px;
        }}
        
        div[data-testid="stMetric"] label {{
            font-size: 0.8rem !important;
            color: {secondary_color} !important;
        }}
        
        div[data-testid="stMetric"] div {{
            font-size: 1.5rem !important;
            font-weight: 600 !important;
        }}
        
        /* Sidebar */
        [data-testid="stSidebar"] {{
            background: #d9eefc !important;
            border-right: 1px solid #b7d5ea;
            padding: 0.8rem 0.75rem;
        }}

        [data-testid="stSidebar"] > div {{
            background: #d9eefc !important;
        }}

        [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {{
            background: #d9eefc !important;
        }}

        [data-testid="stSidebar"] .stMarkdown,
        [data-testid="stSidebar"] .stButton,
        [data-testid="stSidebar"] .stRadio,
        [data-testid="stSidebar"] .stSelectbox {{
            background: transparent !important;
        }}

        [data-testid="stSidebar"] .nav,
        [data-testid="stSidebar"] .nav-pills,
        [data-testid="stSidebar"] .nav-item,
        [data-testid="stSidebar"] .nav-link {{
            background: transparent !important;
        }}

        [data-testid="stSidebar"] .nav-link {{
            color: #173c73 !important;
            border: 1px solid transparent !important;
            box-shadow: none !important;
            font-weight: 600 !important;
        }}

        [data-testid="stSidebar"] .nav-link:hover {{
            background: rgba(111, 182, 240, 0.16) !important;
            color: #0f4c8b !important;
        }}

        [data-testid="stSidebar"] .nav-link-selected {{
            background: linear-gradient(90deg, {theme['primary']}, {theme['secondary']}, {theme['accent']}) !important;
            color: white !important;
            box-shadow: 0 10px 22px rgba(111, 182, 240, 0.22) !important;
        }}

        [data-testid="stSidebar"] [data-testid="stAlert"] {{
            background: rgba(255, 255, 255, 0.65) !important;
            border: 1px solid {border_color} !important;
            color: {text_color} !important;
        }}

        [data-testid="stSidebar"] [data-testid="stAlert"] * {{
            color: {text_color} !important;
        }}

        /* Top header / toolbar */
        [data-testid="stHeader"] {{
            background: linear-gradient(90deg, {card_alt}, {bg_color}) !important;
            border-bottom: 1px solid {border_color};
        }}

        [data-testid="stToolbar"] {{
            right: 1rem;
        }}

        [data-testid="stDecoration"] {{
            background: linear-gradient(90deg, {gradient_start}, {gradient_mid}) !important;
        }}
        
        /* Login container */
        .login-container {{
            background: {card_color};
            border: 1px solid {border_color};
            border-radius: 22px;
            padding: 24px;
            box-shadow: 0 18px 36px rgba(16, 31, 64, 0.08);
        }}
        
        /* Gradient text */
        .gradient-text {{
            background: linear-gradient(90deg, {gradient_start}, {gradient_mid});
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-weight: 700;
        }}
        
        /* Tabs */
        .stTabs [data-baseweb="tab-list"] {{
            gap: 4px;
            background: {card_color};
            padding: 4px;
            border-radius: 10px;
            font-size: 0.9rem;
        }}

        .stTabs [data-baseweb="tab"] {{
            color: {text_color};
            min-width: max-content;
        }}

        /* Input fields */
        .stTextInput input, .stSelectbox select, .stTextArea textarea, .stNumberInput input {{
            font-size: 0.9rem !important;
            padding: 8px !important;
            color: {text_color} !important;
            background: {input_bg} !important;
        }}

        .stSelectbox div[data-baseweb="select"] > div,
        .stMultiSelect div[data-baseweb="select"] > div,
        .stDateInput input {{
            color: {text_color} !important;
            background: {input_bg} !important;
        }}

        .stSelectbox [data-baseweb="select"] *,
        .stSelectbox [data-baseweb="select"] [role="option"],
        .stSelectbox [data-baseweb="select"] [data-baseweb="menu"],
        .stSelectbox [data-baseweb="select"] [data-baseweb="menu"] * {{
            color: {text_color} !important;
        }}

        .stSelectbox [data-baseweb="select"] [data-baseweb="menu"] {{
            background: {card_color} !important;
            border: 1px solid {border_color} !important;
        }}

        .stSelectbox [data-baseweb="select"] [role="option"]:hover {{
            background: {card_alt} !important;
        }}

        .stSelectbox [data-baseweb="select"] [aria-selected="true"] {{
            background: linear-gradient(90deg, {gradient_start}, {gradient_mid}) !important;
            color: white !important;
        }}

        .stAlert, .stInfo, .stSuccess, .stWarning, .stError {{
            color: {text_color} !important;
        }}
        
        /* Buttons */
        .stButton button {{
            font-size: 0.9rem !important;
            font-weight: 700 !important;
            letter-spacing: 0.01em !important;
            padding: 10px 16px !important;
            border-radius: 14px !important;
            border: 1px solid {border_color} !important;
            background: {card_alt} !important;
            color: {text_color} !important;
            box-shadow: 0 8px 18px rgba(31, 111, 229, 0.10);
            transition: all 0.2s ease !important;
            opacity: 1 !important;
            -webkit-text-fill-color: currentColor !important;
        }}

        .stButton button span,
        .stButton button p,
        .stButton button div {{
            color: inherit !important;
            opacity: 1 !important;
            -webkit-text-fill-color: currentColor !important;
            font-weight: 700 !important;
        }}

        .stButton button:hover {{
            border-color: {gradient_start} !important;
            background: {card_alt} !important;
            color: {gradient_start} !important;
            transform: translateY(-1px);
            box-shadow: 0 12px 24px rgba(31, 111, 229, 0.18);
        }}

        .stButton button[kind="primary"] {{
            background: {gradient_start} !important;
            color: white !important;
            border-color: {gradient_start} !important;
        }}

        .stButton button[kind="primary"] span,
        .stButton button[kind="primary"] p,
        .stButton button[kind="primary"] div {{
            color: white !important;
            -webkit-text-fill-color: white !important;
        }}

        .stButton button[kind="primary"]:hover {{
            background: {gradient_mid} !important;
            color: white !important;
        }}

        .stButton button:disabled,
        .stButton button[disabled] {{
            opacity: 1 !important;
            color: {text_color} !important;
            background: {card_alt} !important;
        }}
        
        /* Dataframe */
        .stDataFrame {{
            font-size: 0.9rem !important;
        }}
        
        /* Documentation navigation */
        .doc-nav-item {{
            background: {card_color};
            border: 1px solid {border_color};
            border-radius: 8px;
            padding: 8px 16px;
            cursor: pointer;
            font-size: 0.9rem;
            transition: all 0.2s ease;
            text-align: center;
        }}
        
        .doc-nav-item:hover, .doc-nav-item.active {{
            border-color: {hover_color};
            background: {gradient_start};
            color: white;
        }}

        .landing-hero {{
            background:
                radial-gradient(circle at 20% 28%, {gradient_end}30 0%, {gradient_end}30 5%, transparent 5%),
                radial-gradient(circle at 72% 28%, {gradient_mid}26 0%, {gradient_mid}26 6%, transparent 6%),
                linear-gradient(135deg, {bg_color}, {card_alt});
            border: 1px solid {border_color};
            border-radius: 28px;
            padding: 34px;
            margin-bottom: 20px;
            box-shadow: 0 24px 60px rgba(3, 10, 18, 0.18);
        }}

        .landing-poster {{
            display: grid;
            grid-template-columns: 1.05fr 0.95fr;
            gap: 28px;
            align-items: center;
        }}

        .landing-visual {{
            position: relative;
            min-height: 340px;
            border-radius: 28px;
            background: linear-gradient(135deg, rgba(255,255,255,0.88), {card_color});
            border: 1px solid {border_color};
            overflow: hidden;
            box-shadow: 0 18px 40px rgba(17, 38, 74, 0.10);
        }}

        .landing-visual::before {{
            content: "";
            position: absolute;
            inset: auto -60px -80px auto;
            width: 220px;
            height: 220px;
            background: {gradient_start};
            clip-path: polygon(100% 0, 0 100%, 100% 100%);
            opacity: 0.95;
        }}

        .landing-visual::after {{
            content: "";
            position: absolute;
            top: 34px;
            left: 34px;
            width: 70px;
            height: 70px;
            border-radius: 50%;
            background: {gradient_end};
            opacity: 0.88;
        }}

        .landing-browser {{
            position: absolute;
            left: 34px;
            top: 58px;
            width: 72%;
            background: {card_color};
            border: 1px solid {border_color};
            border-radius: 18px;
            overflow: hidden;
            box-shadow: 0 18px 36px rgba(20, 42, 84, 0.12);
        }}

        .landing-browser-bar {{
            height: 34px;
            background: linear-gradient(90deg, {gradient_end}, {gradient_end}bb);
            display: flex;
            align-items: center;
            padding: 0 14px;
            gap: 8px;
        }}

        .landing-browser-dot {{
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: rgba(255,255,255,0.9);
        }}

        .landing-browser-body {{
            padding: 20px;
            display: grid;
            grid-template-columns: 1.15fr 0.85fr;
            gap: 18px;
            align-items: center;
        }}

        .landing-browser-copy h4 {{
            margin: 0 0 8px 0;
            color: {text_color};
            font-size: 1.2rem !important;
        }}

        .landing-browser-copy p {{
            margin: 0 0 10px 0;
            color: {secondary_color};
            font-size: 0.8rem !important;
        }}

        .landing-browser-cta {{
            display: inline-flex;
            padding: 8px 16px;
            border-radius: 999px;
            background: {gradient_end};
            color: white;
            font-weight: 700;
            font-size: 0.78rem;
        }}

        .landing-figure {{
            position: relative;
            min-height: 180px;
            border-radius: 18px;
            background: linear-gradient(180deg, rgba(255,255,255,0.15), rgba(255,255,255,0.05));
        }}

        .landing-figure-head {{
            position: absolute;
            top: 16px;
            left: 46px;
            width: 62px;
            height: 62px;
            border-radius: 50%;
            background: #ffb4be;
        }}

        .landing-figure-body {{
            position: absolute;
            left: 18px;
            top: 70px;
            width: 122px;
            height: 92px;
            border-radius: 26px 26px 18px 18px;
            background: linear-gradient(135deg, {gradient_mid}, {gradient_start});
        }}

        .landing-figure-card {{
            position: absolute;
            right: 6px;
            top: 42px;
            width: 96px;
            height: 112px;
            border-radius: 18px;
            background: {video_bg};
            border: 1px solid {border_color};
        }}

        .landing-figure-card::before {{
            content: "";
            position: absolute;
            top: 14px;
            left: 14px;
            width: 54px;
            height: 10px;
            border-radius: 999px;
            background: {gradient_start};
        }}

        .landing-figure-card::after {{
            content: "";
            position: absolute;
            top: 38px;
            left: 14px;
            width: 64px;
            height: 48px;
            border-radius: 14px;
            background: rgba(255,255,255,0.62);
        }}

        .landing-stat {{
            padding: 8px 8px 8px 0;
            text-align: left;
            height: 100%;
            border-bottom: 1px solid {border_color};
        }}

        .landing-feature {{
            padding: 6px 8px 6px 0;
            height: 100%;
        }}

        .landing-chip {{
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 7px 12px;
            border-radius: 999px;
            border: 1px solid {border_color};
            background: rgba(255, 255, 255, 0.78);
            color: {gradient_start};
            margin: 0 8px 8px 0;
            font-size: 0.8rem;
            font-weight: 700;
        }}

        .landing-board {{
            display: grid;
            grid-template-columns: 1.2fr 0.8fr;
            gap: 18px;
            margin-top: 22px;
        }}

        .landing-split-row {{
            display: flex;
            justify-content: space-between;
            gap: 24px;
            align-items: flex-start;
            flex-wrap: wrap;
            margin-top: 24px;
        }}

        .landing-panel {{
            padding: 8px 0;
        }}

        .landing-mini {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 10px;
            margin-top: 12px;
        }}

        .landing-mini-card {{
            padding: 8px 0;
            min-height: auto;
            border-bottom: 1px solid {border_color};
        }}

        .landing-compact-meta {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 8px;
            margin-top: 12px;
        }}

        .landing-compact-pill {{
            background: rgba(255,255,255,0.55);
            border: 1px solid {border_color};
            border-radius: 999px;
            padding: 8px 12px;
            font-size: 0.76rem;
            font-weight: 700;
            color: {text_color};
        }}

        .landing-grid-two {{
            display: grid;
            grid-template-columns: 1.2fr 0.8fr;
            gap: 18px;
            margin-top: 20px;
            padding-top: 12px;
            border-top: 1px solid {border_color};
        }}

        .landing-grid-three {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 16px;
            margin-top: 16px;
        }}

        .responsive-side-card {{
            background: {theme["card"]};
            border: 1px solid {border_color};
            border-radius: 18px;
            padding: 16px 18px;
            width: 100%;
            max-width: 320px;
        }}

        .responsive-snapshot-card {{
            background: {theme["card_alt"]};
            border: 1px solid {border_color};
            border-radius: 18px;
            padding: 16px 18px;
            width: 100%;
            max-width: 250px;
        }}

        .responsive-chat-card {{
            background: {theme["card"]};
            border: 1px solid {border_color};
            border-radius: 20px;
            padding: 16px;
            width: 100%;
            max-width: 230px;
        }}

        .billing-plan-card {{
            background: {theme["card"]};
            border: 2px solid {border_color};
            border-radius: 18px;
            padding: 20px;
            min-height: 320px;
            box-shadow: 0 16px 32px rgba(15,23,38,0.08);
            height: 100%;
        }}

        .billing-rail-card {{
            background: {theme["card"]};
            border: 1px solid {border_color};
            border-radius: 16px;
            padding: 16px;
            margin-bottom: 16px;
        }}

        .billing-pill {{
            background: {theme["card_alt"]};
            border: 1px solid {border_color};
            border-radius: 12px;
            padding: 10px 12px;
            text-align: center;
            color: {theme["text"]};
            width: 100%;
        }}

        .connection-card-shell {{
            background: {theme["card"]};
            border: 1px solid {border_color};
            border-radius: 18px;
            padding: 16px 18px;
            margin-bottom: 16px;
        }}

        .connection-status-chip {{
            display: inline-flex;
            align-items: center;
            padding: 6px 12px;
            border-radius: 999px;
            font-size: 0.72rem;
            font-weight: 800;
            letter-spacing: 0.08em;
            text-transform: uppercase;
        }}

        .connection-status-chip.connected {{
            background: #dcfce7;
            color: #166534;
            border: 1px solid #86efac;
        }}

        .connection-status-chip.available {{
            background: #e0f2fe;
            color: #075985;
            border: 1px solid #7dd3fc;
        }}

        .connection-status-chip.pending {{
            background: #fef3c7;
            color: #92400e;
            border: 1px solid #fbbf24;
        }}
        
        /* Code blocks */
        pre {{
            background: {input_bg};
            border: 1px solid {border_color};
            border-radius: 8px;
            padding: 12px;
            font-size: 0.85rem;
            overflow-x: auto;
        }}
        
        code {{
            background: {input_bg};
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 0.85rem;
            color: {gradient_start};
        }}
        
        /* Dividers */
        hr {{
            border: none;
            height: 1px;
            background: linear-gradient(90deg, transparent, {gradient_start}, {gradient_mid}, {gradient_end}, transparent);
            margin: 20px 0;
        }}
        
        /* Animations */
        @keyframes pulse {{
            0%, 100% {{ opacity: 1; }}
            50% {{ opacity: 0.5; }}
        }}
        
        @keyframes spin {{
            from {{ transform: rotate(0deg); }}
            to {{ transform: rotate(360deg); }}
        }}

        @media (max-width: 1024px) {{
            .landing-poster,
            .landing-board,
            .landing-grid-two,
            .landing-grid-three {{
                grid-template-columns: 1fr;
            }}

            .landing-visual,
            .landing-browser {{
                width: 100%;
                min-width: 0;
            }}

            .landing-browser {{
                position: relative;
                left: auto;
                top: auto;
            }}

            .landing-hero {{
                padding: 24px;
            }}

            .landing-split-row {{
                flex-direction: column;
            }}

            .landing-split-row > div {{
                min-width: 0 !important;
                max-width: 100% !important;
                width: 100% !important;
            }}
        }}

        @media (max-width: 768px) {{
            .stApp {{
                padding-left: 0.25rem;
                padding-right: 0.25rem;
            }}

            section.main > div.block-container {{
                padding-top: 0.75rem;
                padding-bottom: 1rem;
                padding-left: 0.75rem;
                padding-right: 0.75rem;
            }}

            .stApp h1 {{
                font-size: 1.65rem !important;
                line-height: 1.08 !important;
            }}

            .stApp h2 {{
                font-size: 1.25rem !important;
            }}

            .stApp h3 {{
                font-size: 1.05rem !important;
            }}

            .landing-hero {{
                border-radius: 20px;
                padding: 18px;
            }}

            .login-container {{
                padding: 18px;
                border-radius: 18px;
            }}

            .login-container h3 {{
                font-size: 1.1rem !important;
            }}

            .platform-card,
            .feature-card,
            .stat-card,
            .doc-section,
            .video-card,
            .media-card,
            .billing-plan-card,
            .billing-rail-card,
            .connection-card-shell {{
                border-radius: 16px;
                padding: 14px;
            }}

            div[data-testid="stMetric"] {{
                padding: 10px;
            }}

            [data-testid="stSidebar"] {{
                padding: 0.5rem;
            }}

            .landing-browser-body {{
                grid-template-columns: 1fr;
            }}

            .landing-browser-copy h4 {{
                font-size: 1rem !important;
            }}

            .landing-browser-copy p {{
                font-size: 0.78rem !important;
            }}

            .landing-mini,
            .landing-compact-meta {{
                grid-template-columns: 1fr;
            }}

            .stTabs [data-baseweb="tab-list"] {{
                overflow-x: auto;
                white-space: nowrap;
            }}

            div[data-testid="stHorizontalBlock"] {{
                flex-wrap: wrap;
                gap: 0.5rem;
            }}

            div[data-testid="stDataFrame"] {{
                overflow-x: auto;
            }}

            div[data-testid="column"] {{
                flex: 1 1 100% !important;
                min-width: 100% !important;
            }}

            .responsive-side-card,
            .responsive-snapshot-card,
            .responsive-chat-card {{
                max-width: 100% !important;
            }}

            .billing-plan-card {{
                min-height: auto;
            }}

            .billing-plan-card h3 {{
                font-size: 1.05rem !important;
            }}

            .billing-rail-card {{
                padding: 12px;
            }}

            .billing-rail-card h4 {{
                font-size: 0.95rem !important;
            }}

            .billing-pill {{
                padding: 9px 10px;
                font-size: 0.74rem;
            }}

            .billing-provider-head {{
                gap: 10px !important;
                align-items: flex-start !important;
            }}

            .billing-provider-name {{
                font-size: 0.98rem !important;
            }}

            .billing-provider-copy {{
                font-size: 0.8rem !important;
            }}

            .connection-card-shell > div[style*="grid-template-columns"] {{
                grid-template-columns: 1fr !important;
            }}

            .sidebar-desktop-only {{
                display: none !important;
            }}

            .app-topbar {{
                padding: 8px 10px !important;
                margin: 0 0 10px 0 !important;
                border-radius: 14px !important;
                gap: 10px !important;
            }}

            .app-topbar-subtitle {{
                font-size: 0.56rem !important;
                letter-spacing: 0.14em !important;
                margin-bottom: 0 !important;
            }}

            .app-topbar-meta {{
                display: none !important;
            }}
        }}
        </style>
        """, unsafe_allow_html=True)

# =============================================================================
# AI FUNCTIONS
# =============================================================================
def ai_analyze_product(product_name, product_description):
    description = (product_description or "").lower()
    if any(word in description for word in ["premium", "luxury", "quality", "durable"]):
        return f"Position {product_name} as a premium offer and reinforce build quality in replies."
    if any(word in description for word in ["fast", "speed", "instant", "quick"]):
        return f"Lead with speed and convenience when presenting {product_name} to prospects."
    if any(word in description for word in ["save", "budget", "affordable", "price"]):
        return f"Highlight value, pricing confidence, and ROI when recommending {product_name}."
    if any(word in description for word in ["easy", "simple", "setup", "beginner"]):
        return f"Emphasize low-friction onboarding and ease of use for {product_name}."
    suggestions = [
        f"Highlight the clearest business outcome customers get from {product_name}.",
        f"Use social proof and customer examples when pitching {product_name}.",
        f"Anchor conversations around the top two features of {product_name}.",
    ]
    return random.choice(suggestions)


def get_matching_product(customer_message, selected_product="None"):
    if selected_product and selected_product != "None":
        return selected_product

    message = (customer_message or "").lower()
    for product in st.session_state.products:
        name = product.get("name", "")
        if name and name.lower() in message:
            return name

    if st.session_state.products:
        return st.session_state.products[0].get("name", "None")
    return "None"


def get_relevant_media_context(platform, selected_product="None"):
    if not st.session_state.media_items:
        return ""

    candidates = [
        media for media in st.session_state.media_items
        if media.get("platform") in {platform, "Other"}
        or selected_product != "None" and selected_product.lower() in media.get("title", "").lower()
    ]
    if not candidates:
        candidates = st.session_state.media_items

    media_item = random.choice(candidates)
    return f" I can also share this {media_item.get('type', 'media')} with you: {media_item.get('title', 'Media')} ({media_item.get('url', '')})"

def ai_generate_reply(customer_message, selected_product, platform="WhatsApp"):
    """Generate AI reply based on customer message and selected product"""
    selected_product = get_matching_product(customer_message, selected_product)
    message = (customer_message or "").lower()

    if not selected_product or selected_product == "None":
        if "price" in message or "cost" in message or "how much" in message:
            return "Thanks for checking with us. I can share pricing options right away if you tell me which product or package you want."
        if "demo" in message or "video" in message:
            return "Absolutely. I can share a quick demo and a short walkthrough so you can review it before deciding."
        return "Thank you for your message. Tell me what you need help with and I can guide you to the right product or package."

    media_context = get_relevant_media_context(platform, selected_product) if random.choice([True, False]) else ""

    if "price" in message or "cost" in message or "how much" in message:
        return f"Thanks for asking about {selected_product}. I can share current pricing, availability, and the best package option for you.{media_context}"
    if "stock" in message or "available" in message or "availability" in message:
        return f"{selected_product} is available and I can confirm the current stock status for you now.{media_context}"
    if "demo" in message or "video" in message or "show" in message:
        return f"Absolutely. I can send a quick demo of {selected_product} and walk you through the main features.{media_context}"
    if "ship" in message or "delivery" in message:
        return f"We can help with delivery details for {selected_product}, including shipping timelines and supported regions.{media_context}"
    return random.choice(
        [
            f"Thanks for your interest in {selected_product}. It is one of our strongest options and I can share the key features right away.{media_context}",
            f"Great choice. {selected_product} is a strong fit for customers looking for reliability and fast support.{media_context}",
            f"Based on your message, {selected_product} sounds like the right match. I can send pricing, specs, or a demo next.{media_context}",
        ]
    )

def ai_reply_to_comment(comment_text, platform, video_id=None, media_id=None):
    """Generate AI reply to a comment on social media"""
    text = (comment_text or "").lower()
    if "price" in text or "how much" in text:
        return f"Thanks for asking. Send us a message and we can share the latest pricing and package options for {platform}."
    if "available" in text or "stock" in text:
        return "Yes, we can help confirm current availability. Send us a quick message and we will guide you."
    if "where" in text or "buy" in text:
        return "We can help you place an order directly. Message us and we will send the best buying option for you."
    if "love" in text or "great" in text or "awesome" in text:
        return "Thank you, we appreciate the support. Let us know if you want product details or a direct recommendation."
    return random.choice(
        [
            "Thanks for your comment. We are happy to help with details, pricing, or product recommendations.",
            "Great question. Message us directly and we can guide you to the best option.",
            "We appreciate the comment. Tell us what you need and we can help right away.",
        ]
    )

def ai_score_client(client_data):
    score = 55
    if client_data.get("email"):
        score += 8
    if client_data.get("phone"):
        score += 8
    interest = (client_data.get("interest") or "").lower()
    if interest and interest != "general inquiry":
        score += 12
    notes = (client_data.get("notes") or "").lower()
    if any(term in notes for term in ["buy", "ready", "urgent", "quote", "price", "today"]):
        score += 15
    if any(term in notes for term in ["demo", "video", "sample", "details"]):
        score += 8
    return max(60, min(score, 98))


def ai_client_summary(client_data):
    score = ai_score_client(client_data)
    interest = client_data.get("interest") or "General Inquiry"
    if score >= 85:
        stage = "Hot"
    elif score >= 70:
        stage = "Warm"
    else:
        stage = "Cold"
    return f"{stage} lead. Prioritize {interest.lower()} follow-up and respond with a clear next step."


def reply_to_unanswered_comments(comments, platform):
    updated = False
    for comment in comments:
        if not comment.get("replied"):
            comment["ai_reply"] = ai_reply_to_comment(comment.get("text", ""), platform)
            comment["replied"] = True
            updated = True
    return updated

def mark_messages_as_read(chat_id, platform):
    """Mark all messages in a chat as read"""
    if platform in st.session_state.platform_conversations:
        for conv in st.session_state.platform_conversations[platform]:
            if conv.get('id') == chat_id:
                for msg in conv.get('messages', []):
                    msg['read'] = True
                conv['unread'] = 0
                break

def register_user(email, password):
    payload = {
        "email": (email or "").strip().lower(),
        "password": password,
        "name": ((email or "").split("@")[0] if email else "").strip(),
    }
    result = api_post("/api/auth/register", payload)
    if result and result.get("status") == "success":
        user = result.get("user", {})
        st.session_state.auth_token = result.get("token", "")
        st.session_state.subscription_status = (user.get("subscription_status") or "inactive").strip().lower()
        return True
    return False


def handle_password_reset(email):
    email = (email or "").strip().lower()
    if not email:
        return False, "Enter your email address to continue."
    result = api_post("/api/auth/forgot-password", {"email": email})
    if result and result.get("status") == "success":
        return True, result.get("message", f"Password reset email sent to {email}")
    return False, "We could not send a reset email. Check the address and server email settings."


def apply_login_state(email, name="", role="User", token="", subscription_status="inactive"):
    normalized_email = (email or "").strip().lower()
    st.session_state.logged_in = True
    st.session_state.show_landing = False
    st.session_state.auth_token = token or ""
    st.session_state.user_email = normalized_email
    st.session_state.user_name = (name or normalized_email.split("@")[0]).strip()
    st.session_state.user_role = (role or "User").strip() or "User"
    st.session_state.subscription_status = (subscription_status or "inactive").strip().lower() or "inactive"


def refresh_workspace_after_login():
    loaders = [
        load_platform_credentials_from_backend,
    ]
    for loader in loaders:
        try:
            loader()
        except Exception as exc:
            # Login should stay usable even if one data source is temporarily broken.
            st.session_state.notifications.append(
                {
                    "type": "warning",
                    "message": f"Signed in, but {loader.__name__} could not finish loading.",
                    "time": datetime.now().strftime("%H:%M"),
                }
            )
            print(f"{loader.__name__} failed after login: {exc}")

# =============================================================================
# DATA MANAGEMENT
# =============================================================================
class DataManager:
    @staticmethod
    def get_sample_data():
        data = {
            "timestamp": [(datetime.now() - pd.Timedelta(hours=i)).strftime("%H:%M") for i in range(15)],
            "platform": ["TikTok", "YouTube", "WhatsApp", "Telegram", "Facebook", 
                        "Instagram", "TikTok", "YouTube", "WhatsApp", "Telegram",
                        "Facebook", "Instagram", "TikTok", "YouTube", "WhatsApp"],
            "customer": [f"+1{str(i).zfill(9)}" for i in range(100, 115)],
            "message": [
                "Interested in pricing",
                "Need integration help",
                "Quick question",
                "Add to group",
                "Following your page",
                "Sent DM",
                "Collaboration request",
                "Live question",
                "Voice message",
                "Poll response",
                "Page liked",
                "Story mention",
                "Challenge entry",
                "Subscribed",
                "Status replied"
            ],
            "score": ["Hot", "Warm", "Hot", "Cold", "Warm", "Hot", 
                     "Warm", "Cold", "Hot", "Warm", "Cold", "Hot",
                     "Warm", "Hot", "Warm"]
        }
        return pd.DataFrame(data)
    
    @staticmethod
    def add_notification(message, type="info"):
        st.session_state.notifications.append({
            "message": message,
            "type": type,
            "time": datetime.now().strftime("%H:%M")
        })
        if len(st.session_state.notifications) > 5:
            st.session_state.notifications = st.session_state.notifications[-5:]

    @staticmethod
    def initialize_sample_media():
        """Initialize sample media for demo"""
        if not st.session_state.media_items:
            st.session_state.media_items = [
                {"id": 1, "type": "video", "platform": "TikTok", "url": "https://example.com/video1.mp4", "thumbnail": "🎥", "title": "Product Demo 1", "comments": [
                    {"user": "@user1", "text": "Great product!", "replied": True, "ai_reply": "Thanks for your comment! Check out our website for more."},
                    {"user": "@user2", "text": "How much does it cost?", "replied": True, "ai_reply": "It's $99 with free shipping!"},
                    {"user": "@user3", "text": "Love this!", "replied": False}
                ]},
                {"id": 2, "type": "video", "platform": "TikTok", "url": "https://example.com/video2.mp4", "thumbnail": "🎥", "title": "Product Demo 2", "comments": [
                    {"user": "@user4", "text": "When will this be available?", "replied": True, "ai_reply": "It's available now!"},
                    {"user": "@user5", "text": "Awesome!", "replied": False}
                ]},
                {"id": 3, "type": "photo", "platform": "Instagram", "url": "https://example.com/photo1.jpg", "thumbnail": "📸", "title": "Product Photo 1", "comments": [
                    {"user": "@user6", "text": "Beautiful shot!", "replied": True, "ai_reply": "Thanks! The product looks even better in person."},
                    {"user": "@user7", "text": "Where can I buy?", "replied": True, "ai_reply": "You can purchase on our website."}
                ]},
                {"id": 4, "type": "photo", "platform": "Facebook", "url": "https://example.com/photo2.jpg", "thumbnail": "📸", "title": "Product Photo 2", "comments": [
                    {"user": "John Doe", "text": "Interested!", "replied": True, "ai_reply": "Great! Let me know if you have questions."}
                ]}
            ]
        
        if not st.session_state.youtube_videos:
            st.session_state.youtube_videos = [
                {"id": "vid1", "title": "Product Overview", "thumbnail": "https://img.youtube.com/vi/1/0.jpg", "comments": [
                    {"user": "TechReviewer", "text": "Great review!", "replied": True, "ai_reply": "Thanks for watching! Let us know if you have questions."},
                    {"user": "ProductHunter", "text": "How's the battery life?", "replied": True, "ai_reply": "Battery life is up to 30 hours!"}
                ]},
                {"id": "vid2", "title": "How to Use", "thumbnail": "https://img.youtube.com/vi/2/0.jpg", "comments": [
                    {"user": "NewUser", "text": "Very helpful!", "replied": False}
                ]}
            ]

# =============================================================================
# AUTHENTICATION
# =============================================================================
def check_password(email, password):
    normalized_email = (email or "").strip().lower()
    result = api_post("/api/auth/login", {"email": normalized_email, "password": password})
    if result and result.get("status") == "success":
        user = result.get("user", {})
        apply_login_state(
            user.get("email", normalized_email),
            user.get("name", normalized_email.split("@")[0]),
            user.get("role", "User"),
            result.get("token", ""),
            user.get("subscription_status", "inactive"),
        )
        return True
    return False

# =============================================================================
# LANDING PAGE
# =============================================================================
def landing_page():
    theme = get_theme_tokens()
    status_label, health_data = get_backend_status()
    status_color = "#22c55e" if status_label == "Online" else theme["secondary"]

    st.markdown(
        f"""
        <div class='landing-hero'>
            <div class='landing-poster'>
                <div class='landing-visual'>
                    <div class='landing-browser'>
                        <div class='landing-browser-bar'>
                            <span class='landing-browser-dot'></span>
                            <span class='landing-browser-dot'></span>
                            <span class='landing-browser-dot'></span>
                        </div>
                        <div class='landing-browser-body'>
                            <div class='landing-browser-copy'>
                                <h4>All your buyer conversations in one place</h4>
                                <p>Control replies, leads, products, and media from one clean workspace.</p>
                                <span class='landing-browser-cta'>Open workspace</span>
                            </div>
                            <div class='landing-figure'>
                                <div class='landing-figure-head'></div>
                                <div class='landing-figure-body'></div>
                                <div class='landing-figure-card'></div>
                            </div>
                        </div>
                    </div>
                </div>
                <div>
                    <div style='margin-bottom:16px;'>{get_app_logo_html(72)}</div>
                    <p style='text-transform:uppercase; letter-spacing:0.18em; font-size:0.72rem; color:{status_color}; margin:0 0 14px 0;'>
                        Social Ai Agent | Social Commerce Operating System
                    </p>
                    <h1 style='font-size:clamp(2rem, 5vw, 3.35rem); line-height:1.05; margin:0 0 14px 0; max-width:780px;'>
                        Social Ai Agent turns comments, DMs, media, and billing into one live revenue workflow.
                    </h1>
                    <p style='font-size:clamp(0.92rem, 2vw, 1rem); color:{theme["muted"]}; max-width:640px; margin:0 0 20px 0;'>
                        Capture leads, reply with AI, upload product media, and keep monthly subscriptions running from one dashboard built for social selling teams.
                    </p>
                    <div style='margin-bottom:16px;'>
                        <span class='landing-chip'>AI replies</span>
                        <span class='landing-chip'>Media uploads</span>
                        <span class='landing-chip'>Monthly billing</span>
                        <span class='landing-chip'>Multi-platform inbox</span>
                        <span class='landing-chip'>Lead tracking</span>
                    </div>
                </div>
            </div>
            <div class='landing-split-row'>
                <div style='flex:1 1 420px;'>
                    <div style='display:flex; gap:12px; flex-wrap:wrap;'>
                        <span class='landing-chip'>Reply faster</span>
                        <span class='landing-chip'>Track every platform</span>
                        <span class='landing-chip'>Keep context loaded</span>
                    </div>
                </div>
                <div class='responsive-side-card'>
                    <div class='landing-panel'>
                        <p style='margin:0 0 10px 0; color:{theme["muted"]}; text-transform:uppercase; letter-spacing:0.12em; font-size:0.72rem;'>Live operator board</p>
                        <div style='display:flex; justify-content:space-between; align-items:end; gap:12px;'>
                            <p style='margin:0; font-size:1.8rem; font-weight:800;'>89 active chats</p>
                            <span class='landing-compact-pill'>Live now</span>
                        </div>
                        <p style='margin:6px 0 0 0; color:{theme["muted"]}; font-size:0.9rem;'>Jump from comments to DMs and keep buyers moving.</p>
                        <div class='landing-mini'>
                            <div class='landing-mini-card'>
                                <p style='margin:0; color:{theme["muted"]}; font-size:0.75rem;'>Open leads</p>
                                <p style='margin:6px 0 0 0; font-size:1.2rem; font-weight:700;'>156</p>
                            </div>
                            <div class='landing-mini-card'>
                                <p style='margin:0; color:{theme["muted"]}; font-size:0.75rem;'>Reply speed</p>
                                <p style='margin:6px 0 0 0; font-size:1.2rem; font-weight:700;'>24/7</p>
                            </div>
                            <div class='landing-mini-card'>
                                <p style='margin:0; color:{theme["muted"]}; font-size:0.75rem;'>Connected channels</p>
                                <p style='margin:6px 0 0 0; font-size:1.2rem; font-weight:700;'>6</p>
                            </div>
                            <div class='landing-mini-card'>
                                <p style='margin:0; color:{theme["muted"]}; font-size:0.75rem;'>Database</p>
                                <p style='margin:6px 0 0 0; font-size:1.2rem; font-weight:700;'>{"Ready" if health_data and health_data.get("database_exists") else "Pending"}</p>
                            </div>
                        </div>
                        <div class='landing-compact-meta'>
                            <span class='landing-compact-pill'>WhatsApp</span>
                            <span class='landing-compact-pill'>TikTok</span>
                            <span class='landing-compact-pill'>YouTube</span>
                            <span class='landing-compact-pill'>Instagram</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_cta1, col_cta2, col_cta3 = st.columns([1.4, 1.1, 1.5])
    with col_cta1:
        if st.button("Open Dashboard", use_container_width=True, type="primary"):
            st.session_state.show_landing = False
            st.session_state.show_register = False
            st.rerun()
    with col_cta2:
        if st.button("Create Account", use_container_width=True):
            st.session_state.show_landing = False
            st.session_state.show_register = True
            st.rerun()
    with col_cta3:
        if st.button("Sign In", use_container_width=True):
            st.session_state.show_landing = False
            st.session_state.show_register = False
            st.rerun()

    st.markdown("---")

    st.markdown(
        f"""
        <div class='landing-grid-three'>
            <div class='landing-stat'>
                <p style='margin:0; color:{theme["muted"]};'>Unified Inbox</p>
                <p style='margin:6px 0; font-size:1.9rem; font-weight:700;'>89</p>
                <p style='margin:0; color:{theme["muted"]};'>active conversations</p>
            </div>
            <div class='landing-stat'>
                <p style='margin:0; color:{theme["muted"]};'>Lead Pipeline</p>
                <p style='margin:6px 0; font-size:1.9rem; font-weight:700;'>156</p>
                <p style='margin:0; color:{theme["muted"]};'>tracked leads</p>
            </div>
            <div class='landing-stat'>
                <p style='margin:0; color:{theme["muted"]};'>AI Coverage</p>
                <p style='margin:6px 0; font-size:1.9rem; font-weight:700;'>24/7</p>
                <p style='margin:0; color:{theme["muted"]};'>always-on response layer</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div class='landing-grid-two'>
            <div class='landing-panel'>
                <p style='margin:0 0 12px 0; color:{theme["muted"]}; text-transform:uppercase; letter-spacing:0.12em; font-size:0.72rem;'>Why teams choose Social Ai Agent</p>
                <div class='landing-grid-three' style='margin-top:0;'>
                    <div class='landing-feature'>
                        <h3 style='margin-top:0;'>Reply with context</h3>
                        <p style='color:{theme["muted"]}; margin-bottom:0;'>Bring product knowledge, customer intent, and media references into every response.</p>
                    </div>
                    <div class='landing-feature'>
                        <h3 style='margin-top:0;'>See the channel mix</h3>
                        <p style='color:{theme["muted"]}; margin-bottom:0;'>Track TikTok, Instagram, Facebook, YouTube, WhatsApp, and Telegram from one view.</p>
                    </div>
                    <div class='landing-feature'>
                        <h3 style='margin-top:0;'>Move to action</h3>
                        <p style='color:{theme["muted"]}; margin-bottom:0;'>Turn comments into leads and leads into conversations without losing momentum.</p>
                    </div>
                </div>
            </div>
            <div class='landing-panel'>
                <p style='margin:0 0 12px 0; color:{theme["muted"]}; text-transform:uppercase; letter-spacing:0.12em; font-size:0.72rem;'>Built for</p>
                <p style='margin:0 0 8px 0; font-size:1.25rem; font-weight:700;'>Operators, sales teams, social storefronts</p>
                <p style='margin:0; color:{theme["muted"]};'>If your buyers discover you in comments, stories, DMs, or live channels, this workspace is designed to hold the thread from attention to sale.</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div class='landing-grid-two'>
            <div class='landing-panel'>
                <p style='margin:0 0 12px 0; color:{theme["muted"]}; text-transform:uppercase; letter-spacing:0.12em; font-size:0.72rem;'>How it works</p>
                <div class='landing-grid-three' style='margin-top:0;'>
                    <div class='landing-feature'>
                        <p style='font-size:0.8rem; letter-spacing:0.12em; color:{theme["muted"]}; margin:0;'>01</p>
                        <h4 style='margin:10px 0 8px 0;'>Connect the channels</h4>
                        <p style='color:{theme["muted"]}; margin:0;'>Bring your active social surfaces into one visible layer.</p>
                    </div>
                    <div class='landing-feature'>
                        <p style='font-size:0.8rem; letter-spacing:0.12em; color:{theme["muted"]}; margin:0;'>02</p>
                        <h4 style='margin:10px 0 8px 0;'>Load products and people</h4>
                        <p style='color:{theme["muted"]}; margin:0;'>Build a memory your team can actually use during live conversations.</p>
                    </div>
                    <div class='landing-feature'>
                        <p style='font-size:0.8rem; letter-spacing:0.12em; color:{theme["muted"]}; margin:0;'>03</p>
                        <h4 style='margin:10px 0 8px 0;'>Operate from one desk</h4>
                        <p style='color:{theme["muted"]}; margin:0;'>Reply, qualify, route, and monitor without losing the thread.</p>
                    </div>
                </div>
            </div>
            <div class='landing-panel'>
                <p style='margin:0 0 12px 0; color:{theme["muted"]}; text-transform:uppercase; letter-spacing:0.12em; font-size:0.72rem;'>Workspace story</p>
                <div style='display:grid; gap:10px;'>
                    <div class='landing-mini-card'>
                        <p style='margin:0; font-weight:700;'>Before</p>
                        <p style='margin:8px 0 0 0; color:{theme["muted"]};'>Scattered inboxes, slow replies, missing context.</p>
                    </div>
                    <div class='landing-mini-card'>
                        <p style='margin:0; font-weight:700;'>During</p>
                        <p style='margin:8px 0 0 0; color:{theme["muted"]};'>AI supports operators with product and customer context.</p>
                    </div>
                    <div class='landing-mini-card'>
                        <p style='margin:0; font-weight:700;'>After</p>
                        <p style='margin:8px 0 0 0; color:{theme["muted"]};'>Cleaner pipeline, faster follow-up, better conversion rhythm.</p>
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# =============================================================================
# LOGIN SCREEN with Register Option
# =============================================================================
def login_screen():
    theme = get_theme_tokens()
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown(f"<div style='display:flex; justify-content:center; margin-bottom:16px;'>{get_app_logo_html(72)}</div>", unsafe_allow_html=True)
        st.markdown("<h1 style='text-align: center;' class='gradient-text'>Social Ai Agent</h1>", unsafe_allow_html=True)
        st.markdown(f"<p style='text-align: center; color: {theme['muted']};'>{t('version')} | Intelligent Social Media</p>", unsafe_allow_html=True)
        
        if st.session_state.show_forgot_password:
            with st.container():
                st.markdown("<div class='login-container'>", unsafe_allow_html=True)
                with st.form("forgot_password_form"):
                    st.markdown("<h3 style='text-align: center;'>🔐 Forgot Password</h3>", unsafe_allow_html=True)
                    st.markdown(
                        f"<p style='text-align: center; color: {theme['muted']};'>Enter your email and we will help you recover access.</p>",
                        unsafe_allow_html=True,
                    )
                    reset_email = st.text_input(
                        f"📧 {t('email')}",
                        placeholder="your@email.com",
                        value=st.session_state.reset_email,
                    )
                    
                    if st.form_submit_button("Send Reset Link", use_container_width=True, type="primary"):
                        ok, message = handle_password_reset(reset_email)
                        st.session_state.reset_email = reset_email
                        if ok:
                            st.success(message)
                        else:
                            st.error(message)

                if st.button("← Back to Login", key="back_from_forgot", use_container_width=True):
                    st.session_state.show_forgot_password = False
                    st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)

        elif not st.session_state.show_register:
            with st.container():
                st.markdown("<div class='login-container'>", unsafe_allow_html=True)
                with st.form("login_form"):
                    st.markdown("<h3 style='text-align: center;'>🔐 Login</h3>", unsafe_allow_html=True)
                    email = st.text_input(f"📧 {t('email')}", placeholder="your@email.com")
                    password = st.text_input(f"🔑 {t('password')}", type="password", placeholder="••••••••")
                    
                    if st.form_submit_button(t('login_button'), use_container_width=True, type="primary"):
                        if email and password:
                            if check_password(email, password):
                                st.session_state.logged_in = True
                                st.session_state.show_landing = False
                                DataManager.add_notification(t('welcome_message', name=st.session_state.user_name), "success")
                                st.rerun()
                            else:
                                st.error(t('login_error'))
                        else:
                            st.warning("Enter email and password")
                
                st.markdown("<div style='text-align: center; margin-top: 15px;'>", unsafe_allow_html=True)
                if st.button("✨ Explore Workspace", key="back_to_landing", use_container_width=True):
                    st.session_state.show_register = False
                    st.session_state.show_forgot_password = False
                    st.session_state.show_landing = True
                    st.rerun()
                if st.button("Forgot Password?", key="forgot_password_cta", use_container_width=True):
                    st.session_state.show_forgot_password = True
                    st.session_state.show_register = False
                    st.rerun()
                st.markdown(f"<p>{t('new_user')}</p>", unsafe_allow_html=True)
                if st.button("Create New Account", use_container_width=True):
                    st.session_state.show_register = True
                    st.session_state.show_forgot_password = False
                    st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)
        
        else:
            with st.container():
                st.markdown("<div class='login-container'>", unsafe_allow_html=True)
                with st.form("register_form"):
                    st.markdown("<h3 style='text-align: center;'>📝 Register</h3>", unsafe_allow_html=True)
                    new_email = st.text_input(f"📧 {t('email')}", placeholder="your@email.com")
                    new_password = st.text_input(f"🔑 {t('password')}", type="password", placeholder="Choose a password")
                    confirm_password = st.text_input("🔒 Confirm Password", type="password", placeholder="Confirm your password")
                    
                    if st.form_submit_button(t('register_button'), use_container_width=True, type="primary"):
                        if new_email and new_password and confirm_password:
                            if new_password != confirm_password:
                                st.error("Passwords do not match!")
                            elif register_user(new_email, new_password):
                                st.success(t('register_success'))
                                st.session_state.show_register = False
                                st.rerun()
                            else:
                                st.error(t('register_error'))
                        else:
                            st.warning("Please fill all fields")
                
                st.markdown("<div style='text-align: center; margin-top: 15px;'>", unsafe_allow_html=True)
                if st.button("← Back to Login", use_container_width=True):
                    st.session_state.show_register = False
                    st.session_state.show_forgot_password = False
                    st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)
        
# =============================================================================
# SIDEBAR
# =============================================================================
def render_sidebar():
    with st.sidebar:
        theme = get_theme_tokens()
        sidebar_bg = "#d9eefc"
        sidebar_card = "#eef8ff"
        sidebar_border = "#b7d5ea"
        sidebar_text = "#173c73"
        sidebar_muted = "#315f90"
        sidebar_primary = "#6fb6f0"
        sidebar_secondary = "#b9def8"
        sidebar_accent = "#f97316"
        st.markdown(
            f"""
            <div style='display:flex; align-items:center; gap:12px; padding:10px 4px 16px 4px;'>
                <div style='flex:0 0 auto;'>{get_app_logo_html(56)}</div>
                <div style='min-width:0;'>
                    <div style='font-size:0.75rem; text-transform:uppercase; letter-spacing:0.16em; color:{sidebar_muted}; margin-bottom:4px;'>Social Commerce OS</div>
                    <div style='font-size:1.1rem; font-weight:800; color:{sidebar_text}; line-height:1.1;'>Social Ai Agent</div>
                    <div style='font-size:0.82rem; color:{sidebar_muted}; margin-top:4px;'>Connect, sell, reply, and bill from one workspace.</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        
        bg_color = sidebar_card
        border_color = sidebar_border
        text_secondary = sidebar_muted
        text_primary = sidebar_text
        
        st.markdown(f"""
        <div style='background: {bg_color}; padding: 12px; border-radius: 12px; margin-bottom: 15px; border: 1px solid {border_color};'>
            <div style='display: flex; align-items: center; gap: 10px;'>
                <div style='width: 36px; height: 36px; border-radius: 18px; background: linear-gradient(135deg, {sidebar_primary}, {sidebar_accent}); 
                display: flex; align-items: center; justify-content: center; color: white; font-weight: 600;'>
                {st.session_state.user_name[0] if st.session_state.user_name else 'U'}
                </div>
                <div>
                    <p style='color: {text_secondary}; margin: 0; font-size: 0.7rem;'>{t('operator')}</p>
                    <p style='color: {text_primary}; margin: 0; font-weight: 600;'>{st.session_state.user_name}</p>
                    <p style='color: {theme["primary"]}; margin: 0; font-size: 0.7rem;'>{st.session_state.user_role}</p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        subscription_status = (st.session_state.get("subscription_status") or "inactive").strip().lower()
        badge_text = "Active" if subscription_status == "active" else "Locked"
        badge_bg = "#16a34a" if subscription_status == "active" else "#f97316"
        st.markdown(
            f"""
            <div style='margin: 0 0 12px 0; padding: 10px 12px; border-radius: 12px; background: {badge_bg}; color: white; font-size: 0.8rem; font-weight: 800; letter-spacing: 0.04em; text-transform: uppercase;'>
                Subscription: {badge_text}
            </div>
            """,
            unsafe_allow_html=True,
        )
        deployment_snapshot = api_get("/api/deployment/check") or {}
        ai_mode = "AI status active" if deployment_snapshot.get("ai_mode") == "active" else "AI status fallback"
        ai_bg = "#16a34a" if deployment_snapshot.get("ai_mode") == "active" else "#f97316"
        st.markdown(
            f"""
            <div style='margin: 0 0 12px 0; padding: 10px 12px; border-radius: 12px; background: {ai_bg}; color: white; font-size: 0.8rem; font-weight: 800; letter-spacing: 0.04em; text-transform: uppercase;'>
                AI: {ai_mode}
            </div>
            """,
            unsafe_allow_html=True,
        )

        col1, col2 = st.columns(2)
        with col1:
            st.metric(t('total_leads'), st.session_state.leads_count)
        with col2:
            total_unread = 0
            for platform, convs in st.session_state.platform_conversations.items():
                total_unread += sum(c.get('unread', 0) for c in convs)
            st.metric(t('conversations'), f"{st.session_state.conversations_count} ({total_unread} new)")
        st.markdown("---")

        subscription_status = (st.session_state.get("subscription_status") or "inactive").strip().lower()
        is_paid = subscription_status == "active"
        if is_paid:
            menu_options = [
                t('dashboard'),
                t('onboard_client'),
                t('media_center'),
                t('product_memory'),
                t('live_chat'),
                t('analytics'),
                t('connections'),
                t('settings'),
                t('billing'),
                t('docs')
            ]
            menu_icons = ['house', 'person-plus', 'camera-reels', 'memory', 'whatsapp', 'graph-up', 'plug', 'gear', 'credit-card', 'book']
            if st.session_state.user_role == "Admin":
                menu_options.insert(8, "Admin")
                menu_icons.insert(8, "shield-lock")
        else:
            menu_options = [t('billing'), t('docs')]
            menu_icons = ['credit-card', 'book']
        page_map = {
            t('dashboard'): "Dashboard",
            t('onboard_client'): "Onboard Client",
            t('media_center'): "Media Center",
            t('product_memory'): "Product Memory",
            t('live_chat'): "Live Chat",
            t('analytics'): "Analytics",
            t('connections'): "Connections",
            t('settings'): "Settings",
            "Admin": "Admin",
            t('billing'): "Billing",
            t('docs'): "Docs"
        }
        reverse_page_map = {value: key for key, value in page_map.items()}
        current_label = reverse_page_map.get(st.session_state.current_page, t('dashboard'))
        default_index = menu_options.index(current_label) if current_label in menu_options else 0

        selected = option_menu(
            menu_title=None,
            options=menu_options,
            icons=menu_icons,
            menu_icon="cast",
            default_index=default_index,
            styles={
                "container": {"padding": "8px 0 2px 0", "background-color": sidebar_card, "border-radius": "18px"},
                "icon": {"color": sidebar_primary, "font-size": "14px"},
                "nav-link": {
                    "font-size": "13px",
                    "text-align": "left",
                    "margin": "4px 4px",
                    "padding": "0.85rem 0.95rem",
                    "color": text_secondary,
                    "border-radius": "16px",
                },
                "nav-link-selected": {
                    "background": f"linear-gradient(90deg, {sidebar_primary}, {sidebar_secondary}, {sidebar_accent})",
                    "color": "white",
                    "font-weight": "800",
                    "border-radius": "16px",
                },
            }
        )
        if selected in page_map:
            st.session_state.current_page = page_map[selected]
        st.markdown("---")
        
        st.markdown("<div class='sidebar-desktop-only'>", unsafe_allow_html=True)
        st.markdown(f"<p style='color: {text_secondary}; font-size: 0.8rem; margin-bottom: 8px;'>🔗 {t('platform_status')}</p>", unsafe_allow_html=True)
        for platform, status in list(st.session_state.platform_status.items()):
            if status == "Connected":
                status_color = "#0f766e"
            elif status == "Pending":
                status_color = "#b45309"
            else:
                status_color = "#173c73"
            st.markdown(f"""
            <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px; font-size: 0.8rem;'>
                <span style='color: {text_primary};'>{platform}</span>
                <span class='status-{status}' style='color: {status_color}; font-weight: 700;'>● {t(status.lower())}</span>
            </div>
            """, unsafe_allow_html=True)
        st.markdown("---")
        st.markdown("</div>", unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("🌓", help="Toggle Theme"):
                theme_cycle = ["dark", "blue", "light"]
                current_theme = st.session_state.theme if st.session_state.theme in theme_cycle else "dark"
                next_theme = theme_cycle[(theme_cycle.index(current_theme) + 1) % len(theme_cycle)]
                st.session_state.theme = next_theme
                st.rerun()
        with col2:
            if st.button("🌐", help="Change Language"):
                current_language = st.session_state.get("language", "en")
                current_idx = LANGUAGE_CODES.index(current_language) if current_language in LANGUAGE_CODES else 0
                next_idx = (current_idx + 1) % len(LANGUAGE_CODES)
                st.session_state.language = LANGUAGE_CODES[next_idx]
                st.rerun()
        with col3:
            lang_meta = LANGUAGE_META.get(st.session_state.get("language", "en"), LANGUAGE_META["en"])
            st.markdown(f"<div style='text-align: center; font-size: 1rem; color: {text_primary}; font-weight: 700;'>{lang_meta['flag']}</div>", unsafe_allow_html=True)
        
        if st.session_state.notifications:
            st.markdown("<div class='sidebar-desktop-only'>", unsafe_allow_html=True)
            st.markdown("---")
            for notif in st.session_state.notifications[-2:]:
                st.info(f"**{notif['message']}**  \n<small>{notif['time']}</small>")
            st.markdown("</div>", unsafe_allow_html=True)
        if st.button(f"🚪 {t('logout')}", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.auth_token = ""
            st.session_state.show_landing = True
            st.session_state.show_register = False
            st.rerun()


def render_subscription_banner(subscription_status: str) -> None:
    if (subscription_status or "").strip().lower() == "active":
        return

    theme = get_theme_tokens()
    st.markdown(
        f"""
        <div style='margin: 0 0 18px 0; padding: 16px 18px; border-radius: 18px; border: 1px solid {theme["border"]}; background: linear-gradient(135deg, rgba(249, 115, 22, 0.18), rgba(121, 185, 242, 0.12));'>
            <div style='display:flex; align-items:center; justify-content:space-between; gap:16px; flex-wrap:wrap;'>
                <div>
                    <div style='font-size:0.82rem; text-transform:uppercase; letter-spacing:0.14em; color:{theme["muted"]}; font-weight:800;'>Subscription required</div>
                    <div style='font-size:1rem; color:{theme["text"]}; font-weight:700; margin-top:4px;'>Your monthly plan is inactive, so the workspace is locked.</div>
                    <div style='font-size:0.9rem; color:{theme["muted"]}; margin-top:6px;'>Open Billing to activate a subscription and unlock connections, media, chat, analytics, and onboarding.</div>
                </div>
                <div style='font-size:0.85rem; font-weight:700; color:white; background:{theme["accent"]}; padding:10px 14px; border-radius:999px;'>
                    Billing only
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# =============================================================================
# DASHBOARD PAGE
# =============================================================================
def dashboard_page():
    df = DataManager.get_sample_data()
    theme = get_theme_tokens()
    bg_color = theme["card"]
    border_color = theme["border"]
    
    st.markdown(f"""
    <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;'>
        <h1 class='gradient-text'>📊 {t('dashboard')}</h1>
        <div style='background: {bg_color}; padding: 6px 12px; border-radius: 20px; border: 1px solid {border_color};'>
            <span style='font-size: 0.8rem;'>{datetime.now().strftime("%b %d, %Y")}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(t('total_leads'), st.session_state.leads_count, "+12")
    with col2:
        hot = len(df[df['score'] == 'Hot'])
        st.metric(t('hot_leads'), hot, f"{hot/len(df)*100:.0f}%")
    with col3:
        connected_platforms = sum(1 for s in st.session_state.platform_status.values() if s == "Connected")
        st.metric(t('active_platforms'), f"{connected_platforms}/6")
    with col4:
        conversion = (hot/len(df)*100)
        st.metric(t('conversion_rate'), f"{conversion:.0f}%", "+3%")
    
    st.markdown("---")
    st.subheader("🚀 Quick Access")
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        if st.button("👤 Onboard", use_container_width=True):
            st.session_state.current_page = "Onboard Client"
            st.rerun()
    with col2:
        if st.button("📺 Media", use_container_width=True):
            st.session_state.current_page = "Media Center"
            st.rerun()
    with col3:
        if st.button("🧠 Memory", use_container_width=True):
            st.session_state.current_page = "Product Memory"
            st.rerun()
    with col4:
        if st.button("💬 Live Chat", use_container_width=True):
            st.session_state.current_page = "Live Chat"
            st.rerun()
    with col5:
        if st.button("💰 Billing", use_container_width=True):
            st.session_state.current_page = "Billing"
            st.rerun()
    st.markdown("---")
    
    col_chat, col_media = st.columns([2, 1])
    secondary_color = theme["muted"]
    
    with col_chat:
        st.subheader("💬 Recent Conversations Across Platforms")
        
        all_conversations = []
        for platform, convs in st.session_state.platform_conversations.items():
            for conv in convs[:2]:  # Take first 2 from each platform
                all_conversations.append(normalize_conversation(conv, platform))
        
        all_conversations = sorted(all_conversations, key=lambda x: parse_display_time(x.get("time")), reverse=True)[:5]
        
        for conv in all_conversations:
            st.markdown(f"""
            <div class='chat-list-item' style='cursor: default;'>
                <div style='display: flex; align-items: center; gap: 8px;'>
                    <div style='width: 32px; height: 32px; border-radius: 16px; background: linear-gradient(135deg, {theme["primary"]}, {theme["accent"]}); 
                         display: flex; align-items: center; justify-content: center; color: white;'>
                        {conv.get('avatar', '👤')}
                    </div>
                    <div style='flex: 1;'>
                        <div style='display: flex; justify-content: space-between;'>
                            <span style='font-weight: 600;'>{conv.get('name', 'User')}</span>
                            <span style='color: {secondary_color}; font-size: 0.7rem;'>{conv.get('time', '')}</span>
                        </div>
                        <p style='margin: 2px 0; font-size: 0.8rem;'>{conv.get('message', '')[:40]}...</p>
                        <div style='display: flex; justify-content: space-between; align-items: center;'>
                            <span class='status-{conv.get('status', 'pending')}' style='font-size: 0.7rem;'>● {conv.get('status', 'pending')}</span>
                            <span class='platform-badge'>{conv['platform']}</span>
                            {f"<span class='unread-badge'>{conv.get('unread', 0)} {t('unread')}</span>" if conv.get('unread', 0) > 0 else ""}
                        </div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    with col_media:
        st.subheader("📱 Recent Media")
        
        if st.session_state.media_items:
            for media in st.session_state.media_items[:2]:
                st.markdown(f"""
                <div class='media-card'>
                    <div class='media-image' style='background: linear-gradient(135deg, {theme["primary"]}, {theme["secondary"]});'>
                        {media['thumbnail']}
                    </div>
                    <p><strong>{media['title']}</strong></p>
                    <p style='font-size: 0.8rem; color: {secondary_color};'>{media['platform']} • {len(media['comments'])} comments</p>
                    <span class='ai-badge'>AI replied to {sum(1 for c in media['comments'] if c.get('replied'))} comments</span>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No media yet. Connect platforms to see content.")

# =============================================================================
# ONBOARD CLIENT PAGE
# =============================================================================
def onboard_client_page():
    st.markdown(f"<h1 class='gradient-text'>👤 {t('onboard_client')}</h1>", unsafe_allow_html=True)
    st.markdown("---")

    with st.form("onboard_client_form"):
        col1, col2 = st.columns(2)
        with col1:
            client_name = st.text_input("Client Name", placeholder="Jane Doe")
            client_email = st.text_input("Client Email", placeholder="jane@example.com")
        with col2:
            client_phone = st.text_input("Phone Number", placeholder="+1 555 010 1000")
            interest = st.selectbox(
                "Interested Product",
                ["General Inquiry"] + [p.get("name", "Unnamed Product") for p in st.session_state.products],
            )

        notes = st.text_area("Notes", placeholder="How did this lead arrive and what do they need?")
        submitted = st.form_submit_button("Add Client", use_container_width=True, type="primary")

    if submitted:
        if not client_name.strip():
            st.warning("Client name is required.")
        else:
            client_payload = {
                "name": client_name,
                "email": client_email,
                "phone": client_phone,
                "interest": interest,
                "notes": notes,
            }
            client_record = {
                "user_email": st.session_state.user_email,
                "name": client_name.strip(),
                "email": client_email.strip(),
                "phone": client_phone.strip(),
                "company": "",
                "platforms": "All",
                "interest": interest,
                "notes": f"{notes.strip()} | AI: {ai_client_summary(client_payload)}".strip(" |"),
                "score": ai_score_client(client_payload),
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
            }
            backend_result = api_post("/api/clients", client_record)
            if backend_result and backend_result.get("status") == "success":
                load_clients_from_backend()
            else:
                st.session_state.clients.append(client_record)
            DataManager.add_notification(f"Client onboarded: {client_record['name']}", "success")
            st.success(f"{client_record['name']} added successfully. AI assessment: {ai_client_summary(client_payload)}")

    if not st.session_state.clients:
        st.info("No clients added yet.")
        return

    client_rows = []
    for client in st.session_state.clients:
        client_rows.append(
            {
                "Name": client.get("name", "Unknown"),
                "Email": client.get("email", ""),
                "Phone": client.get("phone", ""),
                "Interest": client.get("interest", client.get("product", client.get("platforms", "General Inquiry"))),
                "Score": client.get("score", "N/A"),
                "Created": client.get("created_at", client.get("timestamp", "")),
            }
        )

    render_table_card(
        "Recent Clients",
        "Your latest onboarded leads and contact details.",
        pd.DataFrame(client_rows),
        "No clients added yet.",
        height=300,
    )

# =============================================================================
# MEDIA CENTER PAGE (TikTok/Instagram/Facebook videos/photos with comments)
# =============================================================================
def media_center_page():
    theme = get_theme_tokens()
    st.markdown(f"<h1 class='gradient-text'>📺 {t('media_center')}</h1>", unsafe_allow_html=True)
    st.markdown("---")
    
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["TikTok", "Instagram", "Facebook", "YouTube", "Upload", "AI Responses"])
    
    with tab1:  # TikTok
        st.subheader("🎵 TikTok Videos & Comments")
        
        tiktok_media = [m for m in st.session_state.media_items if m['platform'] == "TikTok"]
        
        if tiktok_media:
            cols = st.columns(2)
            for idx, media in enumerate(tiktok_media):
                with cols[idx % 2]:
                    st.markdown(f"""
                    <div class='video-card'>
                        <div class='video-placeholder'>
                            🎥
                        </div>
                        <h4>{media['title']}</h4>
                        <p style='color: {theme["muted"]}; font-size: 0.8rem;'>TikTok • {len(media['comments'])} comments</p>
                        <div class='comment-section'>
                            <p style='font-weight: 600; margin-bottom: 8px;'>Comments:</p>
                    """, unsafe_allow_html=True)
                    
                    for comment in media['comments'][:3]:
                        st.markdown(f"""
                        <div class='comment-item'>
                            <strong>{comment['user']}:</strong> {comment['text']}
                            {f"<div class='comment-ai-reply'>🤖 AI: {comment['ai_reply']}</div>" if comment.get('replied') else ""}
                        </div>
                        """, unsafe_allow_html=True)
                    
                    if len(media['comments']) > 3:
                        st.markdown(f"<p style='font-size: 0.8rem; color: {theme['muted']};'>+{len(media['comments'])-3} more comments</p>", unsafe_allow_html=True)
                    
                    st.markdown("</div>", unsafe_allow_html=True)
                    
                    if st.button(f"Reply to Comments", key=f"reply_tiktok_{media['id']}", use_container_width=True):
                        if reply_to_unanswered_comments(media["comments"], "TikTok"):
                            log_admin_event("ai_reply", "media_comment", media["title"], "TikTok", "AI replied to TikTok comments")
                            DataManager.add_notification(f"AI replied to TikTok comments on {media['title']}", "success")
                            st.success("AI replied to all unanswered TikTok comments.")
                        else:
                            st.info("All visible TikTok comments already have AI replies.")
                        st.rerun()
        else:
            st.info("No TikTok videos found. Connect your TikTok account to see content.")
    
    with tab2:  # Instagram
        st.subheader("📸 Instagram Photos & Comments")
        
        instagram_media = [m for m in st.session_state.media_items if m['platform'] == "Instagram"]
        
        if instagram_media:
            cols = st.columns(3)
            for idx, media in enumerate(instagram_media):
                with cols[idx % 3]:
                    st.markdown(f"""
                    <div class='media-card'>
                        <div class='media-image'>
                            📸
                        </div>
                        <p><strong>{media['title']}</strong></p>
                        <p style='font-size: 0.8rem; color: {theme["muted"]};'>{len(media['comments'])} comments</p>
                        <div style='font-size: 0.8rem; max-height: 100px; overflow-y: auto;'>
                    """, unsafe_allow_html=True)
                    
                    for comment in media['comments'][:2]:
                        st.markdown(f"<div><strong>{comment['user']}:</strong> {comment['text']}</div>", unsafe_allow_html=True)
                        if comment.get('replied'):
                            st.markdown(f"<div style='color: {theme['primary']}; margin-left: 10px;'>🤖 {comment['ai_reply']}</div>", unsafe_allow_html=True)
                    
                    st.markdown("</div>", unsafe_allow_html=True)
                    
                    if st.button(f"Reply", key=f"reply_ig_{media['id']}", use_container_width=True):
                        if reply_to_unanswered_comments(media["comments"], "Instagram"):
                            log_admin_event("ai_reply", "media_comment", media["title"], "Instagram", "AI replied to Instagram comments")
                            DataManager.add_notification(f"AI replied to Instagram comments on {media['title']}", "success")
                            st.success("AI replied to unanswered Instagram comments.")
                        else:
                            st.info("All Instagram comments already have AI replies.")
                        st.rerun()
        else:
            st.info("No Instagram posts found. Connect your Instagram account to see content.")
    
    with tab3:  # Facebook
        st.subheader("📘 Facebook Photos & Comments")
        
        facebook_media = [m for m in st.session_state.media_items if m['platform'] == "Facebook"]
        
        if facebook_media:
            for media in facebook_media:
                with st.expander(f"📘 {media['title']}"):
                    st.markdown(f"""
                    <div style='display: flex; gap: 20px;'>
                        <div style='width: 200px; height: 200px; background: linear-gradient(135deg, {theme["primary"]}, {theme["secondary"]}); border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 3rem;'>
                            📸
                        </div>
                        <div style='flex: 1;'>
                            <h4>Comments ({len(media['comments'])})</h4>
                    """, unsafe_allow_html=True)
                    
                    for comment in media['comments']:
                        st.markdown(f"""
                        <div style='padding: 8px; border-bottom: 1px solid {theme["border"]};'>
                            <strong>{comment['user']}:</strong> {comment['text']}
                            {f"<div style='background: {theme['chat']}; padding: 6px; border-radius: 6px; margin-top: 4px; margin-left: 16px; color: {theme['text']};'><span style='color: {theme['primary']};'>AI:</span> {comment['ai_reply']}</div>" if comment.get('replied') else ""}
                        </div>
                        """, unsafe_allow_html=True)
                    if st.button(f"Reply with AI", key=f"reply_fb_{media['id']}", use_container_width=True):
                        if reply_to_unanswered_comments(media["comments"], "Facebook"):
                            log_admin_event("ai_reply", "media_comment", media["title"], "Facebook", "AI replied to Facebook comments")
                            DataManager.add_notification(f"AI replied to Facebook comments on {media['title']}", "success")
                            st.success("AI replied to unanswered Facebook comments.")
                        else:
                            st.info("All Facebook comments already have AI replies.")
                        st.rerun()
                    
                    st.markdown("</div></div>", unsafe_allow_html=True)
        else:
            st.info("No Facebook posts found. Connect your Facebook account to see content.")
    
    with tab4:  # YouTube
        st.subheader("▶️ YouTube Videos with Comments")
        
        if st.session_state.youtube_videos:
            for video in st.session_state.youtube_videos:
                with st.container():
                    col_thumb, col_info = st.columns([1, 2])
                    with col_thumb:
                        st.markdown(f"""
                        <div style='background: {theme["chat"]}; border: 1px solid {theme["border"]}; border-radius: 8px; padding: 20px; text-align: center;'>
                            <span style='font-size: 3rem;'>▶️</span>
                        </div>
                        """, unsafe_allow_html=True)
                    with col_info:
                        st.markdown(f"**{video['title']}**")
                        st.markdown(f"📊 {len(video['comments'])} comments")
                        
                        with st.expander("View Comments"):
                            for comment in video['comments']:
                                st.markdown(f"""
                                <div style='padding: 8px; border-bottom: 1px solid {theme["border"]};'>
                                    <strong>{comment['user']}:</strong> {comment['text']}
                                    {f"<div style='background: {theme['chat']}; padding: 6px; border-radius: 6px; margin-top: 4px; color: {theme['text']};'><span style='color: {theme['primary']};'>AI:</span> {comment['ai_reply']}</div>" if comment.get('replied') else ""}
                                </div>
                                """, unsafe_allow_html=True)
                            
                            if st.button(f"🤖 AI Reply to All Unanswered", key=f"youtube_reply_{video['id']}"):
                                if reply_to_unanswered_comments(video["comments"], "YouTube"):
                                    log_admin_event("ai_reply", "video_comment", video["title"], "YouTube", "AI replied to YouTube comments")
                                    DataManager.add_notification(f"AI replied to YouTube comments on {video['title']}", "success")
                                    st.success("AI replied to all unanswered YouTube comments.")
                                else:
                                    st.info("All YouTube comments already have AI replies.")
                                st.rerun()
        else:
            st.info("No YouTube videos found. Connect your YouTube account to see content.")
    
    with tab5:  # Upload
        catalog_tab, media_tab = st.tabs(["Catalog Product", "Media Asset"])

        with catalog_tab:
            st.subheader("Add Product to Memory")
            prod_col1, prod_col2 = st.columns(2)
            with prod_col1:
                product_name = st.text_input("Product Name")
                product_price = st.text_input("Price", placeholder="99")
                product_category = st.selectbox("Category", ["General", "Electronics", "Fashion", "Beauty", "Home", "Services"])
            with prod_col2:
                product_tags = st.text_input("Tags", placeholder="premium, featured, bestseller")
                product_file = st.file_uploader(
                    "Browse product media",
                    type=['mp4', 'mov', 'jpg', 'jpeg', 'png', 'gif'],
                    help="This opens the native file picker so you can upload product photos or videos directly.",
                )
                product_media = st.text_input("Media URL", placeholder="Optional fallback URL if you are linking an external asset")
                product_description = st.text_area("Description", height=120)
                if product_file:
                    if product_file.type.startswith("video"):
                        st.video(product_file)
                    else:
                        st.image(product_file, caption=product_file.name, use_container_width=True)

            if st.button("Save Product", key="save_product", type="primary", use_container_width=True):
                if product_name.strip():
                    product_payload = {
                        "user_email": st.session_state.user_email,
                        "name": product_name.strip(),
                        "price": product_price.strip() or "0",
                        "description": product_description.strip(),
                        "category": product_category,
                        "tags": product_tags.strip(),
                        "media_url": product_media.strip(),
                    }
                    if product_file:
                        product_payload.update(
                            {
                                "file_name": Path(product_file.name).name,
                                "file_content_b64": base64.b64encode(product_file.getvalue()).decode("utf-8"),
                                "content_type": product_file.type,
                            }
                        )
                    payload = enrich_product(product_payload)
                    result = api_post("/api/products", payload)
                    if result and result.get("status") == "success":
                        load_products_from_backend()
                    else:
                        st.session_state.products.append(payload)
                        st.session_state.product_memory[payload["name"]] = payload
                    DataManager.add_notification(f"Product added: {payload['name']}", "success")
                    st.success(f"{payload['name']} is now available in Product Memory.")
                else:
                    st.warning("Please enter a product name.")

        with media_tab:
            st.subheader("Upload Media")
            st.caption("Click Browse files to open your computer's file picker, then upload the selected image or video with a title.")
            col1, col2 = st.columns(2)
            with col1:
                platform = st.selectbox("Platform", ["TikTok", "Instagram", "Facebook", "YouTube", "Other"])
                media_type = st.selectbox("Media Type", ["Video", "Photo"])
                title = st.text_input("Title")
            with col2:
                uploaded_file = st.file_uploader(
                    "Browse files from your computer",
                    type=['mp4', 'mov', 'jpg', 'jpeg', 'png', 'gif'],
                    help="This opens the native file picker shown in your screenshot.",
                )
                description = st.text_area("Description", height=100)
                if uploaded_file:
                    if uploaded_file.type.startswith("video"):
                        st.video(uploaded_file)
                    else:
                        st.image(uploaded_file, caption=uploaded_file.name, use_container_width=True)

            if st.button("Upload Media", key="upload_media", type="primary", use_container_width=True):
                if uploaded_file and title.strip():
                    media_item = {
                        "id": len(st.session_state.media_items) + 1,
                        "user_email": st.session_state.user_email,
                        "type": media_type.lower(),
                        "platform": platform,
                        "url": "",
                        "file_name": Path(uploaded_file.name).name,
                        "file_content_b64": base64.b64encode(uploaded_file.getvalue()).decode("utf-8"),
                        "content_type": uploaded_file.type,
                        "thumbnail": "VID" if media_type == "Video" else "IMG",
                        "title": title.strip(),
                        "description": description.strip(),
                        "comments": [],
                    }
                    backend_result = api_post("/api/media", media_item)
                    if backend_result and backend_result.get("status") == "success":
                        load_media_from_backend()
                    else:
                        saved_path = save_uploaded_file(uploaded_file)
                        public_url = f"{API_BASE_URL}/uploads/{Path(saved_path).name}"
                        media_item["url"] = public_url
                        media_item["file_path"] = saved_path
                        media_item.pop("file_name", None)
                        media_item.pop("file_content_b64", None)
                        media_item.pop("content_type", None)
                        st.session_state.media_items.insert(0, media_item)
                    DataManager.add_notification(f"Media uploaded: {title.strip()}", "success")
                    st.success(f"Media '{title.strip()}' uploaded successfully.")
                else:
                    st.warning("Please provide a title and upload a file.")
    
    with tab6:  # AI Responses
        st.subheader("🤖 AI Responses Across Platforms")
        
        all_responses = []
        for media in st.session_state.media_items:
            for comment in media['comments']:
                if comment.get('replied'):
                    all_responses.append({
                        'platform': media['platform'],
                        'user': comment['user'],
                        'comment': comment['text'],
                        'reply': comment['ai_reply'],
                        'media': media['title']
                    })
        
        for video in st.session_state.youtube_videos:
            for comment in video['comments']:
                if comment.get('replied'):
                    all_responses.append({
                        'platform': 'YouTube',
                        'user': comment['user'],
                        'comment': comment['text'],
                        'reply': comment['ai_reply'],
                        'media': video['title']
                    })
        
        if all_responses:
            for response in all_responses:
                st.markdown(f"""
                <div class='platform-card'>
                    <div style='display: flex; justify-content: space-between;'>
                        <span><strong>{response['platform']}</strong> • {response['media']}</span>
                        <span class='ai-badge'>AI Replied</span>
                    </div>
                    <p><strong>👤 {response['user']}:</strong> {response['comment']}</p>
                    <div style='background: {theme["chat"]}; color: {theme["text"]}; padding: 10px; border-radius: 8px; margin-top: 8px; border: 1px solid {theme["border"]};'>
                        <span style='color: {theme["primary"]};'>🤖 AI:</span> {response['reply']}
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No AI responses yet. AI will reply to comments when you connect platforms.")

# =============================================================================
# PRODUCT MEMORY PAGE
# =============================================================================
def product_memory_page():
    theme = get_theme_tokens()
    st.markdown(f"<h1 class='gradient-text'>🧠 {t('product_memory')}</h1>", unsafe_allow_html=True)
    st.markdown("---")
    col1, col2 = st.columns([1, 1])
    with col1:
        st.subheader("📊 Memory Stats")
        total = len(st.session_state.products)
        memory_mb = total * 2.5
        st.markdown(f"""
        <div class='platform-card'>
            <p><strong>Products in Memory:</strong> {total}</p>
            <p><strong>Memory Usage:</strong> {memory_mb:.1f} MB / 100 MB</p>
            <div style='background: {theme["border"]}; height: 6px; border-radius: 3px; margin-bottom: 15px;'>
                <div style='background: linear-gradient(90deg, {theme["primary"]}, {theme["accent"]}); width: {min(memory_mb, 100)}%; height: 6px; border-radius: 3px;'></div>
            </div>
            <p><strong>AI Learning Progress:</strong> {min(total * 5, 100)}%</p>
            <p><strong>Media Items:</strong> {len(st.session_state.media_items)}</p>
            <p><strong>YouTube Videos:</strong> {len(st.session_state.youtube_videos)}</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🧹 Optimize Memory", use_container_width=True):
            st.success("Memory optimized successfully!")
            DataManager.add_notification("Memory optimization complete", "success")
    
    with col2:
        st.subheader("🤖 AI Memory Bank")
        if st.session_state.products:
            selected = st.selectbox("Select product", [p['name'] for p in st.session_state.products])
            product = next((p for p in st.session_state.products if p['name'] == selected), None)
            if product:
                product = enrich_product(product)
                st.markdown(f"""
                <div class='platform-card'>
                    <h4>{product['name']}</h4>
                    <p><strong>Price:</strong> ${product['price']}</p>
                    <p><strong>Category:</strong> {product['category']}</p>
                    <p><strong>SKU:</strong> {product.get('sku', 'N/A')}</p>
                    <div class='ai-badge'>AI: {product.get('ai_notes', 'AI enrichment available after first interaction.')}</div>
                    <p style='margin-top: 10px;'><strong>Media Mentions:</strong> {random.randint(0, 10)} times in social media</p>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No products in memory. Upload products in Media Center.")

# =============================================================================
# LIVE CHAT PAGE (Multi-Platform)
# =============================================================================
def live_chat_page():
    st.markdown(f"<h1 class='gradient-text'>💬 {t('live_chat')}</h1>", unsafe_allow_html=True)
    st.markdown("---")
    theme = get_theme_tokens()
    
    # Platform selector
    platforms = ["All"] + PLATFORM_LIST
    selected_platform = st.selectbox("Filter by Platform", platforms, key="platform_filter")

    if selected_platform != "All":
        st.markdown(
            f"""
            <div style='background: linear-gradient(135deg, {theme["card_alt"]}, {theme["card"]}); border: 1px solid {theme["border"]}; border-radius: 24px; padding: 22px; margin-bottom: 18px; box-shadow: 0 18px 36px rgba(0,0,0,0.06);'>
                <div style='display:flex; justify-content:space-between; gap:20px; align-items:center; flex-wrap:wrap;'>
                    <div style='max-width:700px;'>
                        <p style='margin:0 0 10px 0; color:{theme["primary"]}; text-transform:uppercase; letter-spacing:0.14em; font-size:0.74rem;'>Live Chat Workspace</p>
                        <h2 style='margin:0 0 10px 0;'>Chat live with {selected_platform} customers from one focused panel.</h2>
                        <p style='margin:0; color:{theme["muted"]};'>
                            Select a conversation, review context, use AI suggestions, and send replies without leaving the workspace.
                        </p>
                    </div>
                    <div class='responsive-chat-card'>
                        <p style='margin:0 0 8px 0; color:{theme["muted"]}; font-size:0.78rem;'>Current live channel</p>
                        <p style='margin:0; font-size:1.5rem; font-weight:800;'>{selected_platform}</p>
                        <p style='margin:8px 0 0 0; color:{theme["muted"]};'>Status: {st.session_state.platform_status.get(selected_platform, "Available")}</p>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    
    if st.button("🔄 Sync Conversations", key="chat_sync"):
        load_platform_conversations()
        DataManager.add_notification("Conversation feed refreshed", "success")
        st.rerun()

    # Get all conversations
    all_conversations = []
    for platform, convs in st.session_state.platform_conversations.items():
        if selected_platform == "All" or platform == selected_platform:
            for conv in convs:
                all_conversations.append(normalize_conversation(conv, platform))

    available_keys = {(conv.get("platform"), conv.get("id")) for conv in all_conversations}
    selected_key = (st.session_state.selected_platform, st.session_state.selected_chat)
    if st.session_state.selected_chat and selected_key not in available_keys:
        st.session_state.selected_chat = None
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Conversations", len(all_conversations))
    with col2:
        new = len([c for c in all_conversations if c.get('status') == 'new'])
        st.metric("New", new)
    with col3:
        unread = sum(c.get('unread', 0) for c in all_conversations)
        st.metric("Unread", unread)
    
    st.markdown("---")
    
    chat_col, msg_col = st.columns([1, 1.5])
    
    with chat_col:
        st.subheader("👥 Active Conversations")
        
        search = st.text_input("🔍", placeholder="Search by name...", key="chat_search_input")
        
        filtered = [c for c in all_conversations 
                   if not search or search.lower() in c.get('name', '').lower()]
        
        sorted_chats = sorted(
            filtered,
            key=conversation_sort_key,
        )
        if not sorted_chats:
            st.info("No conversations found for this platform yet. Connect a channel or sync again to populate the live inbox.")
        else:
            chat_page_key = f"live_chat_{selected_platform.lower()}"
            if chat_page_key not in st.session_state:
                st.session_state[chat_page_key] = 1
            chat_page_size = 12
            total_chat_pages = max(1, math.ceil(len(sorted_chats) / chat_page_size))
            current_chat_page = min(max(int(st.session_state[chat_page_key]), 1), total_chat_pages)
            start_idx = (current_chat_page - 1) * chat_page_size
            end_idx = start_idx + chat_page_size
            page_chats = sorted_chats[start_idx:end_idx]

            if total_chat_pages > 1:
                page_left, page_mid, page_right = st.columns([1, 2, 1])
                with page_left:
                    if st.button("◀ Prev", key=f"{chat_page_key}_prev", use_container_width=True, disabled=current_chat_page <= 1):
                        st.session_state[chat_page_key] = current_chat_page - 1
                        st.rerun()
                with page_mid:
                    st.caption(f"Showing {start_idx + 1}-{min(end_idx, len(sorted_chats))} of {len(sorted_chats)} conversations")
                with page_right:
                    if st.button("Next ▶", key=f"{chat_page_key}_next", use_container_width=True, disabled=current_chat_page >= total_chat_pages):
                        st.session_state[chat_page_key] = current_chat_page + 1
                        st.rerun()

            for conv in page_chats:
                selected_class = " selected" if st.session_state.selected_chat == conv.get('id') and st.session_state.selected_platform == conv['platform'] else ""
                
                with st.container():
                    st.markdown(f"<div class='chat-list-item{selected_class}'>", unsafe_allow_html=True)
                    col_avatar, col_info = st.columns([1, 4])
                    with col_avatar:
                        st.markdown(f"<div style='font-size: 2rem;'>{conv.get('avatar', '👤')}</div>", unsafe_allow_html=True)
                    with col_info:
                        col_name_platform = st.columns([2, 1])
                        with col_name_platform[0]:
                            st.markdown(f"**{conv.get('name', 'User')}**")
                        with col_name_platform[1]:
                            platform_logo = get_platform_logo_html(conv['platform'], 16)
                            st.markdown(f"{platform_logo} {conv['platform']}", unsafe_allow_html=True)
                        
                        st.markdown(f"<span style='color: {theme['muted']}; font-size: 0.8rem;'>{conv.get('customer', '')}</span>", unsafe_allow_html=True)
                        st.markdown(f"{conv.get('message', '')[:60]}")
                        
                        col_status_unread = st.columns([1, 1])
                        with col_status_unread[0]:
                            st.markdown(f"<span class='status-{conv.get('status', 'pending')}' style='font-size: 0.7rem;'>{conv.get('status', 'pending').title()}</span>", unsafe_allow_html=True)
                        with col_status_unread[1]:
                            if conv.get('unread', 0) > 0:
                                st.markdown(f"<span class='unread-badge'>{conv['unread']} new</span>", unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True)
                    
                    if st.button(f"Select {conv.get('name', 'User')}", key=f"select_{conv['platform']}_{conv.get('id')}", use_container_width=True):
                        st.session_state.selected_chat = conv.get('id')
                        st.session_state.selected_platform = conv['platform']
                        mark_messages_as_read(conv.get('id'), conv['platform'])
                        st.rerun()
                    st.markdown("---")
    
    with msg_col:
        if st.session_state.selected_chat and st.session_state.selected_platform:
            # Find the selected conversation
            selected_conv = None
            for conv in st.session_state.platform_conversations[st.session_state.selected_platform]:
                if conv.get('id') == st.session_state.selected_chat:
                    selected_conv = normalize_conversation(conv, st.session_state.selected_platform)
                    break
            
            if selected_conv:
                # Get theme colors
                card_color = theme["card"]
                border_color = theme["border"]
                latest_customer_message = next(
                    (get_message_body(m) for m in reversed(selected_conv.get('messages', [])) if m.get('sender') == 'customer'),
                    "",
                )
                conversation_count = len(selected_conv.get("messages", []))
                
                st.markdown(f"""
                <div style='background: {card_color}; border: 1px solid {border_color}; border-radius: 12px; padding: 16px; margin-bottom: 16px;'>
                    <div style='display: flex; align-items: center; gap: 12px;'>
                        <div style='font-size: 2rem;'>{selected_conv.get('avatar', '👤')}</div>
                        <div style='flex: 1;'>
                            <div style='display: flex; align-items: center; gap: 8px;'>
                                <h4 style='margin: 0;'>{selected_conv.get('name', 'User')}</h4>
                                {get_platform_logo_html(selected_conv['platform'], 20)}
                                <span style='font-size: 0.8rem; color: {theme["muted"]};'>{selected_conv['platform']}</span>
                            </div>
                            <p style='margin: 4px 0 0 0; font-size: 0.8rem; color: {theme["muted"]};'>{selected_conv.get('customer', '')}</p>
                        </div>
                        <span class='status-{selected_conv.get('status', 'pending')}'>● {selected_conv.get('status', 'pending')}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                st.markdown(
                    f"""
                    <div style='background: linear-gradient(135deg, {theme["card"]}, {theme["card_alt"]}); border: 1px solid {theme["border"]}; border-radius: 20px; padding: 16px; margin-bottom: 14px;'>
                        <div style='display:flex; justify-content:space-between; gap:16px; align-items:center; flex-wrap:wrap;'>
                            <div>
                                <p style='margin:0 0 6px 0; color:{theme["primary"]}; text-transform:uppercase; letter-spacing:0.12em; font-size:0.72rem;'>Live Section</p>
                                <h4 style='margin:0;'>Active conversation with {selected_conv.get('name', 'Customer')}</h4>
                                <p style='margin:6px 0 0 0; color:{theme["muted"]};'>Channel: {selected_conv['platform']} · Unread cleared · Ready to respond</p>
                            </div>
                            <div style='display:flex; gap:10px; flex-wrap:wrap;'>
                                <span class='landing-chip'>Live reply</span>
                                <span class='landing-chip'>AI assisted</span>
                                <span class='landing-chip'>Context loaded</span>
                            </div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                
                info_col1, info_col2, info_col3 = st.columns(3)
                with info_col1:
                    st.metric("Messages", conversation_count)
                with info_col2:
                    st.metric("Unread", selected_conv.get("unread", 0))
                with info_col3:
                    st.metric("Status", selected_conv.get("status", "pending").title())

                action_col1, action_col2, action_col3, action_col4 = st.columns(4)
                with action_col1:
                    if st.button("🤖 Draft Reply", key="draft_live_reply", use_container_width=True):
                        st.session_state.reply_input = ai_generate_reply(
                            latest_customer_message,
                            st.session_state.chat_product,
                            selected_conv["platform"],
                        )
                        log_admin_event("drafted", "chat_reply", selected_conv.get("name", "Conversation"), selected_conv["platform"], "AI drafted a live chat reply")
                        DataManager.add_notification("AI drafted a reply for this conversation", "success")
                        st.rerun()
                with action_col2:
                    if st.button("📎 Attach Media", key="attach_media_live", use_container_width=True):
                        candidate_media = [
                            media for media in st.session_state.media_items
                            if media.get("platform") in {selected_conv["platform"], "Other"}
                        ] or st.session_state.media_items
                        if candidate_media:
                            media = random.choice(candidate_media)
                            attachment_line = f"\n\nAttached media: {media.get('title', 'Media')} - {media.get('url', '')}"
                            if attachment_line.strip() not in st.session_state.reply_input:
                                st.session_state.reply_input = (st.session_state.reply_input or "").strip() + attachment_line
                            DataManager.add_notification(f"Attached {media.get('title', 'media')} to the reply draft", "success")
                        else:
                            st.warning("No media is available yet. Upload media from the Media Center first.")
                        st.rerun()
                with action_col3:
                    if st.button("🟢 Mark Resolved", key="mark_resolved_live", use_container_width=True):
                        selected_conv["status"] = "resolved"
                        selected_conv["unread"] = 0
                        sync_conversation_to_session(selected_conv)
                        sync_platform_conversations_to_backend(selected_conv["platform"])
                        log_admin_event("updated", "conversation", selected_conv.get("name", "Conversation"), selected_conv["platform"], "Conversation marked as resolved")
                        DataManager.add_notification(f"Marked {selected_conv.get('name', 'conversation')} as resolved", "success")
                        st.rerun()
                with action_col4:
                    if st.button("📩 Simulate Incoming", key="simulate_incoming_live", use_container_width=True):
                        sample_messages = [
                            "Can you share current pricing today?",
                            "Do you have this available right now?",
                            "Please send a quick demo before I decide.",
                            "What package do you recommend for a first order?",
                        ]
                        updated_conv = append_message_to_conversation(selected_conv, "customer", random.choice(sample_messages))
                        sync_conversation_to_session(updated_conv)
                        sync_platform_conversations_to_backend(selected_conv["platform"])
                        log_admin_event("received", "conversation_message", selected_conv.get("name", "Conversation"), selected_conv["platform"], "Simulated incoming customer message")
                        DataManager.add_notification(f"New incoming message from {selected_conv.get('name', 'customer')}", "info")
                        st.rerun()

                messages_to_render = selected_conv.get('messages', [])
                max_visible_messages = 50
                if len(messages_to_render) > max_visible_messages:
                    st.caption(f"Showing the latest {max_visible_messages} of {len(messages_to_render)} messages to keep the chat fast.")
                    messages_to_render = messages_to_render[-max_visible_messages:]

                st.markdown("<div class='chat-container'>", unsafe_allow_html=True)
                for msg in messages_to_render:
                    normalized_message = normalize_message(msg)
                    message_body = normalized_message["message"]
                    if normalized_message['sender'] == 'customer':
                        st.markdown(f"""
                        <div class='message-row other'>
                            <div class='message-bubble other'>
                                <p style='margin: 0;'>{message_body}</p>
                                <span class='message-time'>{normalized_message['time']}</span>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown(f"""
                        <div class='message-row own'>
                            <div class='message-bubble own'>
                                <p style='margin: 0;'>{message_body}</p>
                                <span class='message-time'>{normalized_message['time']}</span>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)
                
                st.markdown("---")
                
                col_ai, col_product = st.columns([1, 2])
                with col_ai:
                    st.markdown(f"<span class='ai-badge'>🤖 AI Assistant</span>", unsafe_allow_html=True)
                
                with col_product:
                    product_options = ["None"] + [p['name'] for p in st.session_state.products] if st.session_state.products else ["None"]
                    selected_product = st.selectbox("Quick product", options=product_options, key="chat_product", label_visibility="collapsed")
                
                if selected_product != "None":
                    ai_reply = ai_generate_reply(latest_customer_message, selected_product, selected_conv['platform'])
                    st.info(f"💡 AI Suggestion: {ai_reply}")

                reply = st.text_area("Type your message", placeholder=t('type_here'), height=100, key="reply_input")

                composer_col1, composer_col2 = st.columns([3, 1])
                with composer_col1:
                    send_reply = st.button(f"📤 {t('send')}", type="primary", use_container_width=True)
                with composer_col2:
                    clear_reply = st.button("🧹 Clear", key="clear_reply_live", use_container_width=True)

                if clear_reply:
                    st.session_state.reply_input = ""
                    st.rerun()

                if send_reply:
                    if reply.strip():
                        backend_result = send_live_message_to_backend(selected_conv, reply)
                        backend_conversation = None
                        delivery_mode = "simulated"
                        delivery_message = ""
                        if backend_result and backend_result.get("status") == "success":
                            backend_conversation = backend_result.get("conversation")
                            delivery_mode = backend_result.get("delivery_mode", "simulated")
                            delivery_message = backend_result.get("delivery_message", "")

                        updated_conv = normalize_conversation(
                            backend_conversation if backend_conversation else append_message_to_conversation(selected_conv, "agent", reply),
                            selected_conv["platform"],
                        )
                        sync_conversation_to_session(updated_conv)
                        sync_platform_conversations_to_backend(selected_conv["platform"])
                        log_admin_event(
                            "sent" if delivery_mode == "live" else "simulated_send",
                            "conversation_message",
                            selected_conv.get("name", "Conversation"),
                            selected_conv["platform"],
                            delivery_message or "Agent sent a live chat reply",
                        )
                        if delivery_mode == "live":
                            DataManager.add_notification(f"Sent a live reply to {selected_conv.get('name', 'User')} on {selected_conv['platform']}", "success")
                        else:
                            DataManager.add_notification(f"Saved a tracked test reply for {selected_conv.get('name', 'User')} on {selected_conv['platform']}", "info")
                        
                        if selected_product != "None" and selected_product in st.session_state.product_memory:
                            st.session_state.product_memory[selected_product]['inquiries'] = st.session_state.product_memory[selected_product].get('inquiries', 0) + 1
                        st.session_state.reply_input = ""
                        st.rerun()
                    st.warning("Type a reply or use Draft Reply to generate one first.")
            else:
                st.info("The selected conversation is no longer available in this filter. Pick another chat from the inbox.")
        else:
            st.info("👈 Select a conversation from the list to start messaging")

# =============================================================================
# ANALYTICS PAGE
# =============================================================================
def analytics_page():
    df = DataManager.get_sample_data()
    client_df = pd.DataFrame(st.session_state.clients) if st.session_state.clients else pd.DataFrame(columns=["score", "interest", "created_at"])
    all_conversations = []
    for platform, conversations in st.session_state.platform_conversations.items():
        for conv in conversations:
            all_conversations.append({"platform": platform, "status": conv.get("status", "pending"), "unread": conv.get("unread", 0)})

    st.markdown(f"<h1 class='gradient-text'>📈 {t('analytics')}</h1>", unsafe_allow_html=True)
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    with col1:
        start = st.date_input("From", datetime.now().replace(day=1))
    with col2:
        end = st.date_input("To", datetime.now())
    
    st.markdown("---")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Leads", max(len(df), len(client_df)))
    with col2:
        connected_platforms = sum(1 for s in st.session_state.platform_status.values() if s == "Connected")
        st.metric("Active Platforms", f"{connected_platforms}/6")
    with col3:
        hot = len(df[df['score'] == 'Hot'])
        if not client_df.empty and "score" in client_df:
            client_scores = pd.to_numeric(client_df["score"], errors="coerce").fillna(0)
            hot += int((client_scores >= 85).sum())
        st.metric("Hot Leads", hot)
    with col4:
        total_leads = max(len(df), 1)
        if not client_df.empty:
            total_leads = max(total_leads, len(client_df))
        conv = (hot / max(total_leads, 1) * 100)
        st.metric("Conversion Rate", f"{conv:.0f}%")
    
    st.markdown("---")
    
    col_chart1, col_chart2 = st.columns(2)
    with col_chart1:
        st.subheader("📊 Platform Distribution")
        chart_source = pd.Series([c["platform"] for c in all_conversations]) if all_conversations else df['platform']
        st.bar_chart(chart_source.value_counts())
    with col_chart2:
        st.subheader("📈 Lead Scores")
        score_counts = df['score'].value_counts()
        for score, count in score_counts.items():
            st.markdown(f"**{score}**: {count} ({(count/len(df)*100):.0f}%)")


def admin_dashboard_page():
    theme = get_theme_tokens()
    overview = api_get("/api/admin/overview") or {}
    users_payload = api_get("/api/admin/users?limit=25") or {"users": []}
    platforms_payload = api_get("/api/admin/platforms") or {"platforms": []}
    activity_payload = api_get("/api/admin/activity?limit=25") or {"activity": []}
    admin_conversations_payload = api_get("/api/admin/conversations?limit=50") or {"conversations": []}
    admin_clients_payload = api_get("/api/admin/clients?limit=50") or {"clients": []}
    admin_products_payload = api_get("/api/admin/products?limit=50") or {"products": []}
    admin_media_payload = api_get("/api/admin/media?limit=50") or {"media": []}
    admin_connections_payload = api_get("/api/admin/connections?limit=100") or {"connections": []}
    admin_events_payload = api_get("/api/admin/events?limit=50") or {"events": []}

    users_rows = users_payload.get("users", [])
    platform_rows = platforms_payload.get("platforms", [])
    activity_rows = activity_payload.get("activity", [])
    admin_conversation_rows = admin_conversations_payload.get("conversations", [])
    admin_client_rows = admin_clients_payload.get("clients", [])
    admin_product_rows = admin_products_payload.get("products", [])
    admin_media_rows = admin_media_payload.get("media", [])
    admin_connection_rows = admin_connections_payload.get("connections", [])
    admin_event_rows = admin_events_payload.get("events", [])
    all_conversations = []
    for platform, conversations in st.session_state.platform_conversations.items():
        for conversation in conversations:
            all_conversations.append(normalize_conversation(conversation, platform))
    client_df = pd.DataFrame(st.session_state.clients) if st.session_state.clients else pd.DataFrame()

    message_capacity = max(int(overview.get("message_capacity", 0) or 0), 1)
    message_usage = int(overview.get("messages_used", 0) or 0)
    usage_pct = min(int(round((message_usage / message_capacity) * 100)), 100)
    connected_platforms = sum(1 for status in st.session_state.platform_status.values() if status == "Connected")
    conversation_count = len(all_conversations)
    live_status = "Live backend" if overview else "Offline snapshot"

    st.markdown("<h1 class='gradient-text'>🛡️ Admin Dashboard</h1>", unsafe_allow_html=True)
    st.markdown(
        f"""
        <div style='background:{theme["card"]}; border:1px solid {theme["border"]}; border-radius:24px; padding:24px; margin:10px 0 18px 0;'>
            <div style='display:flex; justify-content:space-between; align-items:flex-start; gap:16px; flex-wrap:wrap;'>
                <div style='max-width:760px;'>
                    <div style='font-size:0.78rem; letter-spacing:0.18em; text-transform:uppercase; color:{theme["muted"]}; margin-bottom:10px;'>
                        Control Center
                    </div>
                    <div style='font-size:2rem; font-weight:700; color:{theme["text"]}; line-height:1.15; margin-bottom:10px;'>
                        Manage users, message volume, platform traffic, and client demand from one place.
                    </div>
                    <div style='font-size:1rem; color:{theme["muted"]}; line-height:1.6;'>
                        Watch operational health, spot capacity pressure early, and see which channels are creating the most sales conversations.
                    </div>
                </div>
                <div class='responsive-snapshot-card'>
                    <div style='font-size:0.76rem; text-transform:uppercase; letter-spacing:0.12em; color:{theme["muted"]}; margin-bottom:10px;'>
                        System Snapshot
                    </div>
                    <div style='display:grid; gap:10px;'>
                        <div style='display:flex; justify-content:space-between; gap:12px;'>
                            <span style='color:{theme["muted"]};'>Admin</span>
                            <strong style='color:{theme["text"]};'>{st.session_state.user_email or "Not available"}</strong>
                        </div>
                        <div style='display:flex; justify-content:space-between; gap:12px;'>
                            <span style='color:{theme["muted"]};'>Role</span>
                            <strong style='color:{theme["text"]};'>{st.session_state.user_role or "Admin"}</strong>
                        </div>
                        <div style='display:flex; justify-content:space-between; gap:12px;'>
                            <span style='color:{theme["muted"]};'>Data source</span>
                            <strong style='color:{theme["text"]};'>{live_status}</strong>
                        </div>
                        <div style='display:flex; justify-content:space-between; gap:12px;'>
                            <span style='color:{theme["muted"]};'>API</span>
                            <strong style='color:{theme["text"]};'>{API_BASE_URL}</strong>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not overview:
        st.warning("Admin backend data is not available yet. Start the FastAPI backend to load real admin metrics.")

    metric_row_1 = st.columns(4)
    metric_config_1 = [
        ("Users", overview.get("users", 0)),
        ("Active Subs", overview.get("active_subscriptions", 0)),
        ("Leads", overview.get("leads", 0)),
        ("Products", overview.get("products", 0)),
    ]
    for column, (label, value) in zip(metric_row_1, metric_config_1):
        with column:
            st.metric(label, value)

    metric_row_2 = st.columns(4)
    metric_config_2 = [
        ("Clients", overview.get("clients", 0)),
        ("Conversations", overview.get("conversations", 0)),
        ("Media", overview.get("media_assets", 0)),
        ("Events", overview.get("events", 0)),
    ]
    for column, (label, value) in zip(metric_row_2, metric_config_2):
        with column:
            st.metric(label, value)

    metric_row_3 = st.columns(4)
    metric_config_3 = [
        ("AI Replies", overview.get("ai_replies", 0)),
        ("Unread Msgs", overview.get("unread_messages", 0)),
        ("Messages Used", message_usage),
        ("Connected Channels", connected_platforms),
    ]
    for column, (label, value) in zip(metric_row_3, metric_config_3):
        with column:
            st.metric(label, value)

    ops_col, usage_col, live_col = st.columns([1.1, 1, 0.9])
    with ops_col:
        st.markdown(
            f"""
            <div class='platform-card'>
                <div style='font-size:0.78rem; text-transform:uppercase; letter-spacing:0.12em; color:{theme["muted"]}; margin-bottom:8px;'>
                    Operations
                </div>
                <div style='display:grid; gap:8px;'>
                    <div style='display:flex; justify-content:space-between;'><span style='color:{theme["muted"]};'>Conversation load</span><strong>{conversation_count}</strong></div>
                    <div style='display:flex; justify-content:space-between;'><span style='color:{theme["muted"]};'>Selected platforms</span><strong>{len(st.session_state.billing_info.get("platforms", []))}</strong></div>
                    <div style='display:flex; justify-content:space-between;'><span style='color:{theme["muted"]};'>Subscription status</span><strong>{st.session_state.billing_info.get("status", "Inactive")}</strong></div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with usage_col:
        st.markdown(
            f"""
            <div class='platform-card'>
                <div style='font-size:0.78rem; text-transform:uppercase; letter-spacing:0.12em; color:{theme["muted"]}; margin-bottom:8px;'>
                    Message Capacity
                </div>
                <div style='font-size:1.75rem; font-weight:700; color:{theme["text"]}; margin-bottom:8px;'>
                    {usage_pct}%
                </div>
                <div style='background:{theme["input"]}; border-radius:999px; height:10px; overflow:hidden; margin-bottom:10px;'>
                    <div style='width:{usage_pct}%; background:linear-gradient(90deg, {theme["primary"]}, {theme["accent"]}); height:100%;'></div>
                </div>
                <div style='color:{theme["muted"]}; font-size:0.9rem;'>
                    {message_usage} of {message_capacity} monthly messages used
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with live_col:
        st.markdown(
            f"""
            <div class='platform-card'>
                <div style='font-size:0.78rem; text-transform:uppercase; letter-spacing:0.12em; color:{theme["muted"]}; margin-bottom:8px;'>
                    Live Focus
                </div>
                <div style='display:grid; gap:8px;'>
                    <div style='display:flex; justify-content:space-between;'><span style='color:{theme["muted"]};'>Unread messages</span><strong>{sum(conv.get("unread", 0) for conv in all_conversations)}</strong></div>
                    <div style='display:flex; justify-content:space-between;'><span style='color:{theme["muted"]};'>Hot clients</span><strong>{sum(1 for client in st.session_state.clients if safe_int(client.get("score", 0)) >= 85)}</strong></div>
                    <div style='display:flex; justify-content:space-between;'><span style='color:{theme["muted"]};'>Open products</span><strong>{len(st.session_state.products)}</strong></div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    top_col1, top_col2 = st.columns([1.1, 0.9])
    with top_col1:
        st.markdown(
            f"""
            <div style='background:{theme["card"]}; border:1px solid {theme["border"]}; border-radius:22px; padding:18px; margin-bottom:14px;'>
                <div style='font-size:1rem; font-weight:700; color:{theme["text"]}; margin-bottom:4px;'>Platform Activity</div>
                <div style='font-size:0.88rem; color:{theme["muted"]}; line-height:1.5; margin-bottom:12px;'>Volume by channel, useful for spotting the platforms driving the most movement.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if platform_rows:
            platform_df = pd.DataFrame(platform_rows)
            st.bar_chart(platform_df.set_index("platform"))
        else:
            st.info("No platform interaction data yet.")

    with top_col2:
        st.markdown(
            f"""
            <div style='background:{theme["card"]}; border:1px solid {theme["border"]}; border-radius:22px; padding:18px; margin-bottom:14px;'>
                <div style='font-size:1rem; font-weight:700; color:{theme["text"]}; margin-bottom:4px;'>Admin Signals</div>
                <div style='font-size:0.88rem; color:{theme["muted"]}; line-height:1.5; margin-bottom:12px;'>A quick scan of the most active channels and their current interaction counts.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if platform_rows:
            for item in platform_rows[:6]:
                platform_name = item.get("platform", "Platform")
                interaction_count = item.get("interactions", item.get("count", 0))
                st.markdown(
                    f"""
                    <div style='display:flex; justify-content:space-between; align-items:center; gap:12px; padding:12px 14px; border:1px solid {theme["border"]}; border-radius:14px; background:{theme["card"]}; margin-bottom:10px;'>
                        <div>
                            <div style='font-weight:600; color:{theme["text"]};'>{platform_name}</div>
                            <div style='font-size:0.82rem; color:{theme["muted"]};'>Tracked interactions</div>
                        </div>
                        <div style='font-size:1.1rem; font-weight:700; color:{theme["primary"]};'>{interaction_count}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        else:
            st.info("Connect platforms and generate interactions to see live channel signals.")

    users_col, activity_col = st.columns([1.15, 0.85])
    with users_col:
        if users_rows:
            user_df = pd.DataFrame(users_rows)
            if "message_limit" in user_df.columns and "message_count" in user_df.columns:
                user_df["usage_pct"] = (
                    (user_df["message_count"].fillna(0) / user_df["message_limit"].replace(0, 1).fillna(1)) * 100
                ).round(0).astype(int)
            preferred_columns = [
                column for column in [
                    "name",
                    "email",
                    "role",
                    "plan",
                    "message_count",
                    "message_limit",
                    "usage_pct",
                    "created_at",
                ]
                if column in user_df.columns
            ]
            render_table_card(
                "User Directory",
                "Active accounts, plans, and monthly usage at a glance.",
                user_df[preferred_columns] if preferred_columns else user_df,
                "No user records available.",
                height=300,
                page_size=12,
                page_key="admin_users",
            )
        else:
            st.info("No user records available.")

    with activity_col:
        st.subheader("Recent Activity")
        if activity_rows:
            for item in activity_rows[:8]:
                st.markdown(
                    f"""
                    <div style='background:{theme["card"]}; border:1px solid {theme["border"]}; border-radius:16px; padding:14px; margin-bottom:10px;'>
                        <div style='display:flex; justify-content:space-between; gap:10px; margin-bottom:8px;'>
                            <strong style='color:{theme["text"]};'>{item.get("platform", "Platform")}</strong>
                            <span style='color:{theme["muted"]}; font-size:0.78rem;'>{item.get("timestamp", "")}</span>
                        </div>
                        <div style='font-size:0.88rem; color:{theme["muted"]}; margin-bottom:6px;'>
                            {item.get("user_email", "Unknown user")}
                        </div>
                        <div style='font-size:0.9rem; color:{theme["text"]}; margin-bottom:4px;'>
                            Customer: {item.get("customer_number", "Direct message")}
                        </div>
                        <div style='font-size:0.9rem; color:{theme["text"]}; margin-bottom:6px;'>
                            Lead score: {item.get("lead_score", "N/A")}
                        </div>
                        <div style='font-size:0.86rem; color:{theme["muted"]}; line-height:1.45;'>
                            {item.get("last_message", "No preview available.")}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        else:
            st.info("No recent lead activity available.")

    detail1, detail2 = st.columns(2)
    with detail1:
        if all_conversations:
            conv_df = pd.DataFrame(all_conversations)
            health_df = conv_df.groupby(["platform", "status"], as_index=False).size().rename(columns={"size": "count"})
            render_table_card(
                "Conversation Health",
                "Platform and status breakdown for active message threads.",
                health_df,
                "Connect platforms to see conversation analytics.",
                height=280,
                page_size=12,
                page_key="admin_conversation_health",
            )
        else:
            st.info("Connect platforms to see conversation analytics.")

    with detail2:
        if not client_df.empty:
            pipeline_df = client_df.copy()
            if "score" in pipeline_df.columns:
                score_values = pd.to_numeric(pipeline_df["score"], errors="coerce").fillna(0)
                pipeline_df["stage"] = score_values.apply(
                    lambda score: "Hot" if score >= 85 else "Warm" if score >= 70 else "Cold"
                )
            else:
                pipeline_df["stage"] = "Warm"
            visible_columns = [
                column for column in ["name", "email", "phone", "stage", "interest", "created_at"]
                if column in pipeline_df.columns
            ]
            render_table_card(
                "Client Pipeline",
                "Lead stages, contact details, and interest signals.",
                pipeline_df[visible_columns] if visible_columns else pipeline_df,
                "Onboard clients to populate the pipeline.",
                height=280,
                page_size=12,
                page_key="admin_clients_pipeline",
            )
        else:
            st.info("Onboard clients to populate the pipeline.")

    st.markdown("---")
    if admin_connection_rows:
        audit_df = pd.DataFrame(admin_connection_rows)
        audit_summary_col1, audit_summary_col2, audit_summary_col3 = st.columns(3)
        with audit_summary_col1:
            st.metric("Connected Profiles", int(audit_df["connected"].fillna(False).astype(bool).sum()))
        with audit_summary_col2:
            st.metric("Auto-refresh Ready", int(audit_df["auto_refresh_ready"].fillna(False).astype(bool).sum()))
        with audit_summary_col3:
            st.metric("At Risk", int((audit_df["health"] == "Manual reconnect risk").sum()))
        render_table_card(
            "Connection Audit",
            "Platform access, refresh readiness, and account references.",
            audit_df,
            "No platform connection audits are available yet.",
            height=320,
            page_size=12,
            page_key="admin_connection_audit",
            columns=[
                "owner_name",
                "owner_email",
                "role",
                "platform",
                "connected",
                "health",
                "auto_refresh_ready",
                "account_ref",
                "last_refreshed_at",
                "created_at",
            ],
        )
    else:
        st.info("No platform connection audits are available yet.")

    st.markdown("---")
    record_tab1, record_tab2, record_tab3, record_tab4, record_tab5, record_tab6 = st.tabs(
        ["Conversations", "Clients", "Products", "Media", "Connections", "Events"]
    )

    with record_tab1:
        render_table_card(
            "Conversations",
            "Persisted conversations across channels.",
            pd.DataFrame(admin_conversation_rows),
            "No persisted conversations yet. Use Connections or Live Chat to generate tracked conversation records.",
            height=320,
            page_size=12,
            page_key="admin_conversations",
        )

    with record_tab2:
        render_table_card(
            "Clients",
            "Admin-visible client records and onboarding history.",
            pd.DataFrame(admin_client_rows),
            "No admin-visible client records yet.",
            height=320,
            page_size=12,
            page_key="admin_clients",
        )

    with record_tab3:
        render_table_card(
            "Products",
            "Catalog entries and saved product metadata.",
            pd.DataFrame(admin_product_rows),
            "No admin-visible product records yet.",
            height=320,
            page_size=12,
            page_key="admin_products",
        )

    with record_tab4:
        render_table_card(
            "Media",
            "Uploaded files and generated media records.",
            pd.DataFrame(admin_media_rows),
            "No admin-visible media records yet.",
            height=320,
            page_size=12,
            page_key="admin_media",
        )

    with record_tab5:
        render_table_card(
            "Connections",
            "Connection audit history across all platforms.",
            pd.DataFrame(admin_connection_rows),
            "No connection audit records yet.",
            height=320,
            page_size=12,
            page_key="admin_connections",
        )

    with record_tab6:
        render_table_card(
            "Events",
            "Operational events and timeline records.",
            pd.DataFrame(admin_event_rows),
            "No app events logged yet.",
            height=320,
            page_size=12,
            page_key="admin_events",
        )

def seed_connected_platform(platform):
    if platform in {"TikTok", "Instagram", "Facebook", "YouTube"}:
        DataManager.initialize_sample_media()
    if not st.session_state.platform_conversations.get(platform):
        st.session_state.platform_conversations[platform] = [
            {
                "id": f"{platform.lower()}-demo-1",
                "name": "Sample User",
                "customer": "+1234567890",
                "message": f"Hello! I'm interested in your products on {platform}",
                "time": datetime.now().strftime("%I:%M %p"),
                "status": "new",
                "avatar": "👤",
                "unread": 1,
                "messages": [
                    {
                        "sender": "customer",
                        "message": f"Hello! I'm interested in your products on {platform}",
                        "time": datetime.now().strftime("%I:%M %p"),
                        "read": False,
                    }
                ],
            }
        ]
    sync_platform_conversations_to_backend(platform)


# =============================================================================
# CONNECTIONS PAGE (6 Platforms Only)
# =============================================================================
def connections_page():
    theme = get_theme_tokens()
    load_platform_credentials_from_backend()
    backend_public_url = (os.getenv("BACKEND_PUBLIC_URL") or API_BASE_URL).rstrip("/")
    youtube_callback = f"{backend_public_url}/oauth/youtube/callback"
    meta_callback = f"{backend_public_url}/oauth/meta/callback"
    tiktok_callback = f"{backend_public_url}/oauth/tiktok/callback"

    st.markdown(f"<h1 class='gradient-text'>🔌 {t('connections')}</h1>", unsafe_allow_html=True)
    st.markdown(
        f"""
        <div style='background:{theme["card"]}; border:1px solid {theme["border"]}; border-radius:18px; padding:18px; margin-bottom:18px;'>
            <div style='font-size:1rem; color:{theme["text"]}; font-weight:600; margin-bottom:6px;'>Owner Onboarding</div>
            <div style='color:{theme["muted"]}; line-height:1.6;'>
                Save each business owner's approved platform identifiers and tokens here. Social Ai Agent uses these credentials to load conversations, reply with AI, and keep the Admin dashboard in sync.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    wizard_cols = st.columns(3)
    wizard_steps = [
        ("1. Pick a platform", "Choose the channel you want to connect."),
        ("2. Open OAuth or enter tokens", "Use the connect button or save credentials manually."),
        ("3. Reload saved profiles", "Confirm the connection and start syncing conversations."),
    ]
    for col, (step_title, step_desc) in zip(wizard_cols, wizard_steps):
        with col:
            st.markdown(
                f"""
                <div style='background:{theme["card"]}; border:1px solid {theme["border"]}; border-radius:16px; padding:14px; height:100%;'>
                    <div style='font-size:0.78rem; text-transform:uppercase; letter-spacing:0.14em; color:{theme["primary"]}; margin-bottom:8px;'>{step_title}</div>
                    <div style='color:{theme["muted"]}; line-height:1.55;'>{step_desc}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.caption("Quick connect: choose a platform below to jump straight to its setup card.")
    quick_connects = st.columns(6)
    for idx, platform in enumerate(PLATFORM_LIST):
        with quick_connects[idx]:
            if st.button(f"Connect {platform}", key=f"quick_connect_{platform.lower()}", use_container_width=True):
                st.session_state.connection_focus = platform
                st.rerun()

    connected = sum(1 for status in st.session_state.platform_status.values() if status == "Connected")
    available = sum(1 for status in st.session_state.platform_status.values() if status == "Available")
    metric1, metric2, metric3 = st.columns(3)
    with metric1:
        st.metric("Connected", f"{connected}/6")
    with metric2:
        st.metric("Available", available)
    with metric3:
        st.metric("Stored Profiles", sum(1 for platform in PLATFORM_LIST if st.session_state.platform_credentials.get(platform)))

    refresh_col1, refresh_col2 = st.columns([1, 2])
    with refresh_col1:
        if st.button("Reload Saved Connections", use_container_width=True):
            load_platform_credentials_from_backend(force=True)
            st.success("Saved platform profiles reloaded.")
            st.rerun()
    with refresh_col2:
        st.caption("After finishing OAuth in a new tab, come back here and reload saved connections to confirm the owner profile was stored.")

    maintenance_col1, maintenance_col2 = st.columns([1, 2])
    with maintenance_col1:
        if st.button("Refresh All Eligible Tokens", use_container_width=True):
            result = api_post("/api/platform-connections/refresh-all", {})
            if result and result.get("status") == "success":
                load_platform_credentials_from_backend(force=True)
                refreshed = ", ".join(result.get("refreshed", [])) or "none"
                skipped = ", ".join(result.get("skipped", [])) or "none"
                DataManager.add_notification(f"Token maintenance completed. Refreshed: {refreshed}", "success")
                st.success(f"Refreshed: {refreshed}")
                if skipped != "none":
                    st.info(f"Skipped: {skipped}")
                st.rerun()
            st.error("Could not run token maintenance. Check your OAuth settings and refresh tokens.")
    with maintenance_col2:
        st.caption("Use this to refresh every connected platform that already has a stored refresh token, without opening each connection one by one.")

    st.markdown(
        f"""
        <div style='background:{theme["card"]}; border:1px solid {theme["border"]}; border-radius:18px; padding:18px; margin-bottom:18px;'>
            <div style='font-size:1rem; color:{theme["text"]}; font-weight:700; margin-bottom:8px;'>Connection Callback URLs</div>
            <div style='color:{theme["muted"]}; line-height:1.65; margin-bottom:10px;'>
                Register these exact callback URLs in your OAuth consoles. If you are using ngrok, make sure <code>BACKEND_PUBLIC_URL</code> matches the live tunnel URL.
            </div>
            <div style='display:grid; gap:8px;'>
                <div><strong style='color:{theme["text"]};'>YouTube / Google:</strong> <code>{youtube_callback}</code></div>
                <div><strong style='color:{theme["text"]};'>Meta / Facebook / Instagram / WhatsApp:</strong> <code>{meta_callback}</code></div>
                <div><strong style='color:{theme["text"]};'>TikTok:</strong> <code>{tiktok_callback}</code></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    platform_descriptions = {
        "WhatsApp": "Business messaging with Phone Number ID and Cloud API token.",
        "TikTok": "Business account access via Open ID plus TikTok access and refresh tokens.",
        "YouTube": "Channel connection using Google OAuth access token, refresh token, and channel ID.",
        "Telegram": "Bot-based messaging using the BotFather token.",
        "Facebook": "Page messaging and comments using Page ID plus Page access token.",
        "Instagram": "Instagram messaging through the linked Facebook Page credentials.",
    }

    for platform in PLATFORM_LIST:
        credentials = st.session_state.platform_credentials.get(platform, {}).copy()
        status = st.session_state.platform_status.get(platform, "Available")
        health_label = get_connection_health_label(platform, credentials)
        logo = get_platform_logo_html(platform, 28)
        focus_platform = st.session_state.get("connection_focus")
        expanded = status == "Connected" or focus_platform == platform
        with st.expander(f"{platform} • {status}", expanded=expanded):
            status_class = "connected" if status == "Connected" else "pending" if "Missing" in health_label or "Manual reconnect" in health_label else "available"
            status_detail = "Ready" if status == "Connected" else "Needs credentials" if status == "Available" else "Review"
            st.markdown(
                f"""
                <div class='connection-card-shell'>
                    <div style='display:flex; justify-content:space-between; gap:12px; align-items:flex-start; flex-wrap:wrap;'>
                        <div style='display:flex; align-items:flex-start; gap:14px; flex:1 1 auto; min-width:0;'>
                            <div>{logo}</div>
                            <div>
                                <div style='font-size:1rem; font-weight:600; color:{theme["text"]};'>{platform}</div>
                                <div style='color:{theme["muted"]}; font-size:0.92rem; line-height:1.55;'>{platform_descriptions[platform]}</div>
                            </div>
                        </div>
                        <div class='connection-status-chip {status_class}'>{status_detail}</div>
                    </div>
                    <div style='display:grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap:10px; margin-top:14px;'>
                        <div style='background:{theme["card_alt"]}; border:1px solid {theme["border"]}; border-radius:14px; padding:10px 12px;'>
                            <div style='font-size:0.7rem; text-transform:uppercase; letter-spacing:0.12em; color:{theme["muted"]};'>Connection</div>
                            <div style='font-weight:700; color:{theme["text"]}; margin-top:4px;'>{status}</div>
                        </div>
                        <div style='background:{theme["card_alt"]}; border:1px solid {theme["border"]}; border-radius:14px; padding:10px 12px;'>
                            <div style='font-size:0.7rem; text-transform:uppercase; letter-spacing:0.12em; color:{theme["muted"]};'>Health</div>
                            <div style='font-weight:700; color:{theme["text"]}; margin-top:4px;'>{health_label}</div>
                        </div>
                        <div style='background:{theme["card_alt"]}; border:1px solid {theme["border"]}; border-radius:14px; padding:10px 12px;'>
                            <div style='font-size:0.7rem; text-transform:uppercase; letter-spacing:0.12em; color:{theme["muted"]};'>Mode</div>
                            <div style='font-weight:700; color:{theme["text"]}; margin-top:4px;'>{'OAuth' if platform in {'YouTube', 'TikTok', 'Facebook', 'Instagram', 'WhatsApp'} else 'Manual'}</div>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.caption(f"Connection health: {health_label}")

            oauth_url = ""
            oauth_note = ""
            oauth_params = urlencode(
                {
                    "user_email": st.session_state.user_email,
                    "auth_token": st.session_state.auth_token,
                }
            )
            if platform == "YouTube":
                oauth_url = f"{API_BASE_URL}/oauth/youtube/start?{oauth_params}"
                oauth_note = "Recommended: connect with Google OAuth so refresh tokens can be stored automatically."
            elif platform == "TikTok":
                oauth_url = f"{API_BASE_URL}/oauth/tiktok/start?{oauth_params}"
                oauth_note = "Recommended: connect with TikTok OAuth so the open_id, access token, and refresh token are saved automatically."
            elif platform in {"Facebook", "Instagram", "WhatsApp"}:
                oauth_url = f"{API_BASE_URL}/oauth/meta/start?{oauth_params}"
                oauth_note = "Recommended: connect with Meta OAuth to save the Page credentials automatically. WhatsApp still needs a Phone Number ID afterward."

            if oauth_url:
                st.link_button(
                    f"Connect {platform} with {'Google' if platform == 'YouTube' else 'TikTok' if platform == 'TikTok' else 'Meta'} OAuth",
                    oauth_url,
                    use_container_width=True,
                )
                st.caption(oauth_note)

            form_key = f"connect_form_{platform.lower()}"
            with st.form(form_key):
                for field_name, label, placeholder in PLATFORM_CONNECTION_FIELDS[platform]:
                    value = credentials.get(field_name, "")
                    is_secret = "token" in field_name
                    credentials[field_name] = st.text_input(
                        label,
                        value=value,
                        placeholder=placeholder,
                        type="password" if is_secret else "default",
                        key=f"{platform.lower()}_{field_name}",
                    )
                save_connection = st.form_submit_button(
                    f"Save {platform} Connection",
                    type="primary",
                    use_container_width=True,
                )

            action_col1, action_col2 = st.columns([1, 1])
            with action_col1:
                if save_connection:
                    if has_required_platform_credentials(platform, credentials):
                        payload = {"user_email": st.session_state.user_email, **credentials}
                        result = api_post(f"/api/platform-connections/{platform.lower()}", payload)
                        if result and result.get("status") == "success":
                            st.session_state.platform_credentials[platform] = credentials
                            st.session_state.platform_status[platform] = "Connected"
                            st.session_state.platform_credentials_loaded_at = 0.0
                            seed_connected_platform(platform)
                            DataManager.add_notification(f"{platform} credentials saved successfully", "success")
                            st.success(f"{platform} is now connected.")
                            st.rerun()
                        else:
                            st.error(f"Could not save the {platform} credentials. Make sure the backend is running.")
                    else:
                        st.warning(f"Enter the required {platform} credentials before saving.")

            with action_col2:
                if st.button(f"Disconnect {platform}", key=f"disconnect_{platform.lower()}", use_container_width=True):
                    result = api_delete(f"/api/platform-connections/{platform.lower()}")
                    if result and result.get("status") == "success":
                        st.session_state.platform_credentials[platform] = {
                            field: "" for field, _, _ in PLATFORM_CONNECTION_FIELDS[platform]
                        }
                        st.session_state.platform_status[platform] = "Available"
                        st.session_state.platform_credentials_loaded_at = 0.0
                        DataManager.add_notification(f"{platform} disconnected", "info")
                        st.success(f"{platform} has been disconnected.")
                        st.rerun()
                    else:
                        st.error(f"Could not disconnect {platform}.")

            if platform in {"YouTube", "TikTok"} and status == "Connected":
                refresh_label = f"Refresh {platform} Token"
                if st.button(refresh_label, key=f"refresh_{platform.lower()}_token", use_container_width=True):
                    result = api_post(f"/api/platform-connections/{platform.lower()}/refresh", {})
                    if result and result.get("status") == "success":
                        load_platform_credentials_from_backend(force=True)
                        DataManager.add_notification(f"{platform} token refreshed successfully", "success")
                        st.success(f"{platform} access token refreshed.")
                        st.rerun()
                    st.error(f"Could not refresh the {platform} token. Check the stored refresh token and OAuth app settings.")

            required_labels = [
                label for field, label, _ in PLATFORM_CONNECTION_FIELDS[platform] if field != "tiktok_shop_id"
            ]
            st.caption("Required fields: " + ", ".join(required_labels))
            if platform == "YouTube":
                st.caption("Health: refresh token required for long-lived channel access.")
            if platform == "TikTok":
                st.caption("Health: TikTok refresh token lets you renew access without reconnecting the owner.")

    if st.session_state.get("connection_focus"):
        st.session_state.connection_focus = ""

# =============================================================================
# SETTINGS PAGE
# =============================================================================
def settings_page():
    theme = get_theme_tokens()
    if st.session_state.get("profile_country_source") != "manual":
        sync_billing_country_from_backend()
    st.markdown(f"<h1 class='gradient-text'>⚙️ {t('settings')}</h1>", unsafe_allow_html=True)
    st.markdown("---")
    
    tabs = st.tabs([t('profile'), t('notifications'), t('system'), t('billing')])
    
    with tabs[0]:
        st.subheader("👤 Profile Settings")
        
        with st.form("profile_form"):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input(t('name'), value=st.session_state.user_name, key="profile_name_input")
                email = st.text_input(t('email'), value=st.session_state.user_email, disabled=True)
                phone = st.text_input("Phone", value=st.session_state.profile_phone, key="profile_phone_input")
            with col2:
                company = st.text_input(t('company'), value=st.session_state.profile_company, key="profile_company_input")
                role = st.text_input(t('role'), value=st.session_state.user_role, disabled=True)
                timezone_options = ["UTC-8 (PST)", "UTC-5 (EST)", "UTC+0 (GMT)", "UTC+1 (CET)", "UTC+8 (SGT)"]
                timezone_value = st.session_state.profile_timezone if st.session_state.profile_timezone in timezone_options else "UTC-5 (EST)"
                timezone = st.selectbox("Timezone", ["UTC-8 (PST)", "UTC-5 (EST)", "UTC+0 (GMT)", "UTC+1 (CET)", "UTC+8 (SGT)"], 
                                      index=timezone_options.index(timezone_value))
                country_value = st.session_state.profile_country if st.session_state.profile_country in COUNTRY_OPTIONS else "Global / Other"
                country = st.selectbox("Billing Country", COUNTRY_OPTIONS, index=COUNTRY_OPTIONS.index(country_value))
            
            if st.form_submit_button(t('save_changes'), type="primary"):
                st.session_state.profile_name = name
                st.session_state.profile_phone = phone
                st.session_state.profile_company = company
                st.session_state.profile_timezone = timezone
                st.session_state.profile_country = country
                st.session_state.profile_country_source = "manual"
                DataManager.add_notification("Profile updated successfully", "success")
                st.success("✅ Profile updated!")
    
    with tabs[1]:
        st.subheader("🔔 Notification Settings")
        
        with st.form("notification_form"):
            col1, col2 = st.columns(2)
            with col1:
                email_alerts = st.checkbox("Email alerts for new messages", value=st.session_state.email_alerts)
                push_notifications = st.checkbox("Push notifications", value=st.session_state.push_notifications)
                sms_alerts = st.checkbox("SMS alerts", value=st.session_state.sms_alerts)
            with col2:
                daily_summary = st.checkbox("Daily summary report", value=st.session_state.daily_summary)
                weekly_report = st.checkbox("Weekly analytics report", value=st.session_state.weekly_report)
                ai_activity = st.checkbox("AI activity reports", value=True)
            
            if st.form_submit_button(t('save_changes'), type="primary"):
                st.session_state.email_alerts = email_alerts
                st.session_state.push_notifications = push_notifications
                st.session_state.sms_alerts = sms_alerts
                st.session_state.daily_summary = daily_summary
                st.session_state.weekly_report = weekly_report
                DataManager.add_notification("Notification settings saved", "success")
                st.success("✅ Settings saved!")
    
    with tabs[2]:
        st.subheader("⚙️ System Settings")
        
        with st.form("system_form"):
            col1, col2 = st.columns(2)
            with col1:
                theme_options = ["dark", "blue", "light"]
                selected_theme = st.selectbox(
                    t('theme'),
                    theme_options,
                    format_func=lambda x: "Dark" if x == "dark" else "Light Blue" if x == "blue" else "Light",
                    index=theme_options.index(st.session_state.theme) if st.session_state.theme in theme_options else 0
                )
                
                language_codes = LANGUAGE_CODES
                current_language = st.session_state.get("language", "en")
                lang = st.selectbox(
                    t('language'),
                    language_codes,
                    format_func=lambda x: f"{LANGUAGE_META[x]['flag']} {LANGUAGE_META[x]['label']}",
                    index=language_codes.index(current_language) if current_language in language_codes else 0,
                )
            with col2:
                refresh = st.slider("Auto-refresh rate (seconds)", 10, 300, st.session_state.refresh_rate)
                timeout = st.number_input("Session timeout (minutes)", 5, 120, st.session_state.timeout)
                cache = st.select_slider("Cache size (MB)", options=[100, 250, 500, 1000], value=st.session_state.cache_size)
            
            if st.form_submit_button(t('save_changes'), type="primary"):
                if selected_theme != st.session_state.theme:
                    st.session_state.theme = selected_theme
                if lang != st.session_state.language:
                    st.session_state.language = lang
                st.session_state.refresh_rate = refresh
                st.session_state.timeout = timeout
                st.session_state.cache_size = cache
                DataManager.add_notification("System settings saved", "success")
                st.success("✅ Settings saved!")
                st.rerun()

    st.markdown("---")
    st.subheader("🚀 Deployment Readiness")
    deployment_check = api_get("/api/deployment/check") or {}
    readiness_cols = st.columns(3)
    with readiness_cols[0]:
        st.metric("Ready", "Yes" if deployment_check.get("deployment_ready") else "No")
    with readiness_cols[1]:
        st.metric("Billing", "Ready" if deployment_check.get("billing_ready") else "Missing")
    with readiness_cols[2]:
        st.metric("Uploads", "Ready" if deployment_check.get("upload_ready") else "Missing")

    st.metric("AI", "AI status active" if deployment_check.get("ai_mode") == "active" else "AI status fallback")

    warnings = deployment_check.get("deployment_warnings") or []
    if deployment_check.get("ai_mode") == "fallback":
        st.info("AI fallback mode is active. Add your AI key to enable AI-powered responses.")
    if warnings:
        st.warning("Review the items below before deploying:")
        for warning in warnings:
            st.write(f"- {warning}")
    else:
        st.success("Deployment checks look good. You can test and deploy from here.")

    detected_country = sync_billing_country_from_backend()
    country_label = "detected" if st.session_state.get("profile_country_source") == "auto" else "selected"
    st.caption(f"Billing country ({country_label}): {detected_country}")
    st.caption("You can override this in the Profile tab if the detected country is not correct.")

    st.markdown("---")
    st.subheader("✅ Go-Live Checklist")

    checklist_items = [
        ("Strong `AUTH_SECRET`", deployment_check.get("auth_secret_ok"), "Set a non-default signing secret."),
        ("Production `FRONTEND_APP_URL`", deployment_check.get("frontend_url_ok"), "Use your live dashboard URL."),
        ("Production `DATABASE_URL`", deployment_check.get("database_url_ok"), "Point the app at your live database."),
        ("Billing provider ready", deployment_check.get("billing_ready"), "At least one live billing rail must be enabled."),
        ("Paystack live mode", deployment_check.get("paystack_ok"), "Use live Paystack keys for real monthly subscriptions."),
        ("SMTP configured", deployment_check.get("smtp_ok"), "Password reset email needs working mail settings."),
        ("AI enabled", deployment_check.get("ai_ready"), "AI is optional, but recommended for live replies."),
        ("Uploads ready", deployment_check.get("upload_ready"), "Media uploads are already wired through the backend."),
    ]

    for label, is_ready, hint in checklist_items:
        badge_bg = "#dcfce7" if is_ready else "#fef3c7"
        badge_fg = "#166534" if is_ready else "#92400e"
        badge_border = "#86efac" if is_ready else "#fbbf24"
        badge_label = "READY" if is_ready else "CHECK"
        st.markdown(
            dedent(
                f"""
                <div style="display:flex; align-items:flex-start; gap:12px; padding:12px 14px; margin-bottom:10px; border:1px solid {theme['border']}; border-radius:14px; background:{theme['card']};">
                    <div style="flex:1 1 auto;">
                        <div style="font-weight:700; color:{theme['text']}; margin-bottom:4px;">{label}</div>
                        <div style="color:{theme['muted']}; font-size:0.9rem;">{hint}</div>
                    </div>
                    <div style="flex:0 0 auto; align-self:center; padding:6px 12px; border-radius:999px; background:{badge_bg}; color:{badge_fg}; border:1px solid {badge_border}; font-size:0.72rem; font-weight:800; letter-spacing:0.08em;">
                        {badge_label}
                    </div>
                </div>
                """
            ),
                unsafe_allow_html=True,
            )

# =============================================================================
# BILLING PAGE (New)
# =============================================================================
def billing_page():
    theme = get_theme_tokens()
    if st.session_state.get("profile_country_source") != "manual":
        sync_billing_country_from_backend()
    st.markdown(f"<h1 class='gradient-text'>💰 Billing & Subscription</h1>", unsafe_allow_html=True)
    st.markdown("---")
    billing_meta = api_get("/api/billing/plans") or {}
    billing_country = get_billing_country()
    paystack_supported_country = is_paystack_supported_country(billing_country)
    paypal_live = bool(billing_meta.get("paypal_enabled"))
    dodo_live = bool(billing_meta.get("dodo_enabled")) and (billing_meta.get("dodo_env") or "").strip().lower() == "live_mode"
    paystack_live = billing_meta.get("paystack_env") == "live"

    country_label = "detected" if st.session_state.get("profile_country_source") == "auto" else "selected"
    st.caption(f"Billing country ({country_label}): {billing_country}")
    if not paystack_supported_country:
        st.info("Paystack is hidden for the selected billing country. PayPal and Dodo remain available when live.")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Current Plan", st.session_state.billing_info["plan"] if st.session_state.billing_info["plan"] else "None", "Select a plan")
    with col2:
        st.metric("Status", st.session_state.billing_info["status"], "✅" if st.session_state.billing_info["status"] == "Active" else "")
    with col3:
        platforms_count = len(st.session_state.billing_info["platforms"])
        st.metric("Platforms", f"{platforms_count}/6", f"${PLATFORM_PRICES.get(platforms_count, 0)}/mo")
    
    st.markdown("---")
    st.subheader("Provider Readiness")

    provider_cards = [
        (
            "PayPal",
            paypal_live,
            "Add `PAYPAL_CLIENT_SECRET` and keep `PAYPAL_ENV=live` on the backend host.",
        ),
        (
            "Paystack",
            paystack_live and paystack_supported_country,
            "Use a live `sk_live_...` key on the backend host and select a supported billing country.",
        ),
        (
            "Dodo",
            dodo_live,
            "Add `DODO_PAYMENTS_API_KEY`, keep `DODO_ENV=live_mode`, and restart the backend.",
        ),
    ]
    provider_cols = st.columns(3)
    for col, (label, ready, hint) in zip(provider_cols, provider_cards):
        with col:
            badge_bg = "#dcfce7" if ready else "#fef3c7"
            badge_fg = "#166534" if ready else "#92400e"
            badge_border = "#86efac" if ready else "#fbbf24"
            badge_label = "READY" if ready else "CHECK"
            st.markdown(
                dedent(
                    f"""
                    <div style="padding:14px 16px; border:1px solid {theme['border']}; border-radius:16px; background:{theme['card']}; min-height:140px;">
                        <div style="display:flex; align-items:center; justify-content:space-between; gap:12px; margin-bottom:10px;">
                            <div style="font-size:1rem; font-weight:800; color:{theme['text']};">{label}</div>
                            <div style="padding:6px 12px; border-radius:999px; background:{badge_bg}; color:{badge_fg}; border:1px solid {badge_border}; font-size:0.72rem; font-weight:800; letter-spacing:0.08em;">{badge_label}</div>
                        </div>
                        <div style="color:{theme['muted']}; font-size:0.9rem; line-height:1.55;">{hint}</div>
                    </div>
                    """
                ),
                unsafe_allow_html=True,
            )

    st.subheader("📋 Choose Your Platform Package")
    st.markdown("Select the platforms you want to connect. Price is based on the number of platforms.")

    def select_plan(label, platforms, plan_key):
        st.session_state.selected_platforms = platforms
        st.session_state.billing_info["platforms"] = platforms
        st.session_state.billing_info["plan"] = label
        st.session_state.billing_info["plan_key"] = plan_key
        st.session_state.billing_info["status"] = "Pending Payment"
        st.session_state.billing_info["payment_method"] = ""
        st.session_state.billing_info["paypal_order_id"] = ""
        st.session_state.billing_info["paypal_payment_link"] = ""
        st.session_state.billing_info["paystack_session_id"] = ""
        st.session_state.billing_info["paystack_payment_link"] = ""
        st.session_state.billing_info["dodo_payment_id"] = ""
        st.session_state.billing_info["dodo_payment_link"] = ""
        st.session_state.billing_info["next_billing"] = None
        st.success("Plan selected! Please complete payment.")

    plan_specs = [
        ("1 Platform", 30, ["Any single platform", "AI replies", "Media integration"], [PLATFORM_LIST[0]], False, "plan_1"),
        ("2 Platforms", 50, ["Any 2 platforms", "AI replies", "Media integration"], PLATFORM_LIST[:2], False, "plan_2"),
        ("3 Platforms", 80, ["Any 3 platforms", "AI replies", "Media integration"], PLATFORM_LIST[:3], False, "plan_3"),
        ("4 Platforms", 100, ["Any 4 platforms", "AI replies", "Media integration"], PLATFORM_LIST[:4], True, "plan_4"),
        ("5 Platforms", 120, ["Any 5 platforms", "AI replies", "Media integration"], PLATFORM_LIST[:5], False, "plan_5"),
        ("All 6 Platforms", 130, ["All 6 platforms", "AI replies", "Media integration"], PLATFORM_LIST, False, "plan_6"),
    ]

    for chunk_start in range(0, len(plan_specs), 3):
        row = st.columns(3)
        for col, (label, price, features, platforms, popular, plan_key) in zip(row, plan_specs[chunk_start:chunk_start + 3]):
            with col:
                highlight = theme["primary"] if popular else theme["border"]
                badge_line = "<p style='margin:0 0 10px 0; color:{}; font-weight:700; text-transform:uppercase; letter-spacing:0.08em; font-size:0.75rem;'>{}</p>".format(
                    theme["primary"], "Popular" if popular else "Plan"
                )
                feature_lines = "".join(
                    f"<p style='margin:0 0 10px 0; color:{theme['text']};'>✓ {feature}</p>" for feature in features
                )
                card_html = dedent(
                    f"""
                    <div class='billing-plan-card' style='border-color:{highlight};'>
                        {badge_line}
                        <h3 style='margin:0 0 10px 0; color:{theme["text"]};'>{label}</h3>
                        <p style='margin:0; font-size:1.9rem; font-weight:800; color:{theme["primary"]};'>${price}</p>
                        <p style='margin:8px 0 18px 0; color:{theme["muted"]};'>per month</p>
                        <hr style='margin:16px 0;'>
                        {feature_lines}
                    </div>
                    """
                ).strip()
                st.markdown(card_html, unsafe_allow_html=True)
                if st.button("Select", key=plan_key, type="primary" if popular else "secondary", use_container_width=True):
                    select_plan(label, platforms, plan_key)
    
    if st.session_state.selected_platforms:
        st.markdown("---")
        st.subheader("💳 Choose Billing Rail")
        st.markdown(
            f"<div class='billing-rail-card'><h4 style='margin:0; color:{theme['text']};'>Selected Platforms</h4></div>",
            unsafe_allow_html=True,
        )
        selected_cols = st.columns(min(len(st.session_state.selected_platforms), 4))
        for idx, platform in enumerate(st.session_state.selected_platforms):
            with selected_cols[idx % len(selected_cols)]:
                st.markdown(
                    f"<div class='billing-pill'>{platform}</div>",
                    unsafe_allow_html=True,
                )
        
        tab_pay1, tab_pay2, tab_pay3 = st.tabs(["PayPal", "Paystack", "Dodo"])

        with tab_pay1:
            st.markdown(
                f"""
                <div class='billing-provider-head' style='display:flex; align-items:center; gap:12px; margin-bottom:12px;'>
                    {get_payment_provider_logo_html("PayPal", 28)}
                    <div>
                        <div class='billing-provider-name' style='font-size:1.05rem; font-weight:700; color:{theme["text"]};'>PayPal subscription</div>
                        <div class='billing-provider-copy' style='font-size:0.88rem; color:{theme["muted"]};'>Monthly plan checkout for customers who prefer PayPal.</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if billing_meta.get("paypal_enabled"):
                st.success("PayPal live subscription billing is configured.")
            else:
                st.warning("PayPal is not live yet. Make sure the backend host has `PAYPAL_CLIENT_SECRET` and `PAYPAL_ENV=live`, then restart the backend.")

            if st.button("Create PayPal Subscription", key="pay_paypal", type="primary", use_container_width=True):
                plan_key = st.session_state.billing_info.get("plan_key") or ""
                if not plan_key:
                    st.warning("Select a plan first.")
                else:
                    payment_result = api_post_verbose(
                        "/api/payments/paypal/create",
                        {
                            "plan_key": plan_key,
                            "customer_name": st.session_state.user_name or st.session_state.profile_name or st.session_state.user_email,
                        },
                    )
                    if payment_result.get("ok") and payment_result.get("data", {}).get("payment_link"):
                        payment_data = payment_result["data"]
                        st.session_state.billing_info["payment_method"] = "PayPal (live)"
                        st.session_state.billing_info["paypal_order_id"] = payment_data.get("subscription_id", payment_data.get("order_id", ""))
                        st.session_state.billing_info["paypal_payment_link"] = payment_data.get("payment_link", "")
                        st.session_state.billing_info["status"] = "Pending Payment"
                        st.success("Live PayPal subscription created. Open the approval link to complete checkout.")
                        st.markdown(f"[Open PayPal Subscription Checkout]({payment_data['payment_link']})")
                    else:
                        st.error(f"Could not create a live PayPal subscription: {payment_result.get('error', 'Unknown PayPal error')}")

            paypal_order_id = st.session_state.billing_info.get("paypal_order_id", "")
            if paypal_order_id and st.button("Refresh PayPal Status", key="refresh_paypal_status", use_container_width=True):
                status_result = api_get(f"/api/payments/paypal/{paypal_order_id}")
                if status_result:
                    payment_status = (status_result.get("payment_status") or "").upper()
                    if payment_status in {"ACTIVE", "APPROVED"}:
                        st.session_state.billing_info["status"] = "Active"
                        st.session_state.subscription_status = "active"
                        st.session_state.billing_info["next_billing"] = (datetime.now().replace(day=1) + pd.DateOffset(months=1)).strftime("%Y-%m-%d")
                        st.success("✅ PayPal subscription confirmed. Your monthly plan is now active.")
                    else:
                        st.info(f"Current payment status: {payment_status or 'CREATED'}")
                else:
                    st.warning("Unable to verify the PayPal order right now.")

        with tab_pay2:
            st.markdown(
                f"""
                <div class='billing-provider-head' style='display:flex; align-items:center; gap:12px; margin-bottom:12px;'>
                    {get_payment_provider_logo_html("Paystack", 28)}
                    <div>
                        <div class='billing-provider-name' style='font-size:1.05rem; font-weight:700; color:{theme["text"]};'>Paystack subscription</div>
                        <div class='billing-provider-copy' style='font-size:0.88rem; color:{theme["muted"]};'>Monthly plan checkout for African markets and card payments.</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if paystack_live and paystack_supported_country:
                st.success("Paystack live subscription billing is configured.")
            else:
                if not paystack_supported_country:
                    st.info("Paystack subscriptions are not shown for this billing country.")
                else:
                    st.warning("Paystack is not live yet. Replace `PAYSTACK_SECRET_KEY` with a live `sk_live_...` key to enable real subscriptions.")

            if paystack_live and paystack_supported_country and st.button("Create Paystack Subscription", key="pay_paystack", type="primary", use_container_width=True):
                plan_key = st.session_state.billing_info.get("plan_key") or ""
                if not plan_key:
                    st.warning("Select a plan first.")
                else:
                    payment_result = api_post_verbose(
                        "/api/payments/paystack/create",
                        {
                            "plan_key": plan_key,
                            "customer_name": st.session_state.user_name or st.session_state.profile_name or st.session_state.user_email,
                        },
                    )
                    if payment_result.get("ok") and payment_result.get("data", {}).get("payment_link"):
                        payment_data = payment_result["data"]
                        st.session_state.billing_info["payment_method"] = "Paystack (live)"
                        st.session_state.billing_info["paystack_session_id"] = payment_data.get("reference", payment_data.get("session_id", ""))
                        st.session_state.billing_info["paystack_payment_link"] = payment_data.get("payment_link", "")
                        st.session_state.billing_info["status"] = "Pending Payment"
                        st.success("Live Paystack subscription checkout created. Open the checkout link to complete payment.")
                        st.markdown(f"[Open Paystack Subscription Checkout]({payment_data['payment_link']})")
                    else:
                        st.error(f"Could not create a live Paystack subscription checkout session: {payment_result.get('error', 'Unknown Paystack error')}")

            if not paystack_supported_country:
                st.caption("Choose a supported country in Settings to show the Paystack rail.")

            paystack_session_id = st.session_state.billing_info.get("paystack_session_id", "")
            if paystack_session_id and st.button("Refresh Paystack Status", key="refresh_paystack_status", use_container_width=True):
                status_result = api_get(f"/api/payments/paystack/{paystack_session_id}")
                if status_result:
                    payment_status = (status_result.get("payment_status") or "").lower()
                    if payment_status == "success":
                        st.session_state.billing_info["status"] = "Active"
                        st.session_state.subscription_status = "active"
                        st.session_state.billing_info["next_billing"] = (datetime.now().replace(day=1) + pd.DateOffset(months=1)).strftime("%Y-%m-%d")
                        st.success("✅ Paystack subscription confirmed. Your monthly plan is now active.")
                    else:
                        st.info(f"Current payment status: {payment_status or 'pending'}")
                else:
                    st.warning("Unable to verify the Paystack checkout right now.")

        with tab_pay3:
            st.markdown(
                f"""
                <div class='billing-provider-head' style='display:flex; align-items:center; gap:12px; margin-bottom:12px;'>
                    {get_payment_provider_logo_html("Dodo", 28)}
                    <div>
                        <div class='billing-provider-name' style='font-size:1.05rem; font-weight:700; color:{theme["text"]};'>Dodo subscription</div>
                        <div class='billing-provider-copy' style='font-size:0.88rem; color:{theme["muted"]};'>Monthly checkout powered by Dodo Payments.</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if not st.session_state.billing_info.get("plan_key"):
                st.info("Select a plan above first, then open the live Dodo subscription checkout.")
            else:
                plan_key = st.session_state.billing_info.get("plan_key")
                if dodo_status := api_get("/api/billing/plans"):
                    selected_plan = next((plan for plan in dodo_status.get("plans", []) if plan.get("plan_key") == plan_key), None)
                else:
                    selected_plan = None

                if selected_plan:
                    st.write(f"Selected plan: **{selected_plan['label']}**")
                    st.write(f"Live price: **${selected_plan['price_cents'] / 100:.2f}**")
                else:
                    st.write(f"Selected plan key: **{plan_key}**")

                if st.button("Create Dodo Subscription", key="create_dodo_checkout", type="primary", use_container_width=True):
                    payment_result = api_post_verbose(
                        "/api/payments/dodo/create",
                        {
                            "plan_key": plan_key,
                            "customer_name": st.session_state.user_name or st.session_state.profile_name or st.session_state.user_email,
                            "return_url": FRONTEND_APP_URL,
                        },
                    )
                    if payment_result.get("ok") and payment_result.get("data", {}).get("payment_link"):
                        payment_data = payment_result["data"]
                        st.session_state.billing_info["payment_method"] = "Dodo Payments (live)"
                        st.session_state.billing_info["dodo_payment_id"] = payment_data.get("subscription_id", payment_data.get("payment_id", ""))
                        st.session_state.billing_info["dodo_payment_link"] = payment_data.get("payment_link", "")
                        st.session_state.billing_info["status"] = "Pending Payment"
                        st.success("Live subscription checkout created. Open the payment link to complete the purchase.")
                        st.markdown(
                            f"<a href='{payment_data['payment_link']}' target='_blank'>Open Dodo Subscription Checkout</a>",
                            unsafe_allow_html=True,
                        )
                    else:
                        st.error(f"Could not create a Dodo subscription checkout link: {payment_result.get('error', 'Unknown Dodo error')}")

                payment_id = st.session_state.billing_info.get("dodo_payment_id", "")
                if payment_id:
                    st.caption(f"Payment ID: {payment_id}")
                    if st.button("Refresh Payment Status", key="refresh_dodo_status", use_container_width=True):
                        status_result = api_get(f"/api/payments/dodo/{payment_id}")
                        if status_result:
                            payment_status = (status_result.get("payment_status") or "").lower()
                            if payment_status in {"succeeded", "paid", "completed", "active"}:
                                st.session_state.billing_info["status"] = "Active"
                                st.session_state.subscription_status = "active"
                                st.session_state.billing_info["next_billing"] = (datetime.now().replace(day=1) + pd.DateOffset(months=1)).strftime("%Y-%m-%d")
                                st.success("✅ Dodo subscription confirmed. Your monthly plan is now active.")
                            else:
                                st.info(f"Current payment status: {payment_status or 'pending'}")
                        else:
                            st.warning("Unable to verify the payment status right now.")

    st.markdown("---")
    st.subheader("📄 Subscription History")
    
    history = pd.DataFrame({
        "Date": ["Mar 1, 2024", "Feb 1, 2024", "Jan 1, 2024"],
        "Description": ["Professional Plan - Monthly", "Professional Plan - Monthly", "Professional Plan - Monthly"],
        "Amount": ["$99.00", "$99.00", "$99.00"],
        "Status": ["Paid", "Paid", "Paid"],
        "Invoice": ["INV-001", "INV-002", "INV-003"]
    })
    st.dataframe(history, use_container_width=True, hide_index=True)

# =============================================================================
# DOCUMENTATION PAGE
# =============================================================================
def documentation_page():
    st.markdown(f"<h1 class='gradient-text'>📚 {t('docs')}</h1>", unsafe_allow_html=True)
    st.markdown("---")
    
    col_nav1, col_nav2, col_nav3, col_nav4, col_nav5 = st.columns(5)
    with col_nav1:
        if st.button(" Getting Started", use_container_width=True, type="primary" if st.session_state.doc_section == "Getting Started" else "secondary"):
            st.session_state.doc_section = "Getting Started"
    with col_nav2:
        if st.button("🔌 API", use_container_width=True, type="primary" if st.session_state.doc_section == "API" else "secondary"):
            st.session_state.doc_section = "API"
    with col_nav3:
        if st.button("🔔 Webhooks", use_container_width=True, type="primary" if st.session_state.doc_section == "Webhooks" else "secondary"):
            st.session_state.doc_section = "Webhooks"
    with col_nav4:
        if st.button("📦 SDKs", use_container_width=True, type="primary" if st.session_state.doc_section == "SDKs" else "secondary"):
            st.session_state.doc_section = "SDKs"
    with col_nav5:
        if st.button("❓ FAQ", use_container_width=True, type="primary" if st.session_state.doc_section == "FAQ" else "secondary"):
            st.session_state.doc_section = "FAQ"
    st.markdown("---")
    
    if st.session_state.doc_section == "Getting Started":
        st.markdown("""
        ###  Quick Start Guide
        
        **Navigation Overview**  
        The left sidebar is the main workspace navigator. It gives you access to:
        - **Dashboard** for overview metrics, quick actions, recent conversations, and recent media
        - **Onboard Client** for adding and reviewing client records
        - **Media Center** for social media content, uploads, and AI comment responses
        - **Product Memory** for product context, AI notes, and memory statistics
        - **Live Chat** for multi-platform conversations and AI-assisted replies
        - **Analytics** for performance metrics, platform distribution, and pipeline health
        - **Connections** for connecting and disconnecting supported platforms
        - **Settings** for profile, notifications, system configuration, and theme/language
        - **Billing** for plans, payment methods, and billing history
        - **Docs** for in-app help, API notes, webhooks, SDK guidance, and FAQ

        **1. Add Products**  
        Go to **Media Center** and upload your products with images and descriptions. AI will automatically analyze each product.
        
        **2. Connect Platforms**  
        Visit **Connections** to link your social media accounts. We support 6 platforms: WhatsApp, TikTok, YouTube, Telegram, Facebook, and Instagram.
        
        **3. Choose Your Plan**  
        Go to **Billing** and select the number of platforms you want to connect. Use the PayPal, Paystack, or Dodo tabs when live billing is configured.
        
        **4. Onboard Clients**  
        Use **Onboard Client** to add new clients. AI will score their potential and suggest products.
        
        **5. Start Chatting**  
        Use **Live Chat** to engage with customers across all connected platforms. AI will suggest replies based on your products and media.
        
        **6. Monitor Media**  
        View TikTok videos, Instagram photos, Facebook posts, and YouTube videos in the **Media Center**. AI automatically replies to comments.
        
        **7. Manage Memory**  
        The **Product Memory** stores all product information and learns from interactions to provide better suggestions.

        **Top Bar & Sidebar Controls**  
        - Use the theme button in the sidebar to cycle between available themes
        - Use the language button to cycle through the supported languages
        - The top toolbar is Streamlit's app header and remains available while you work
        """)
    
    elif st.session_state.doc_section == "API":
        st.markdown("""
        ### 🔌 API Reference
        
        **Authentication**  
        All API requests require an API key. Include it in the Authorization header:
        """)

        st.code(
            'Authorization: Bearer YOUR_API_KEY\nContent-Type: application/json',
            language="text"
        )

        st.markdown(f"""
        **Base URL**  
        `{BACKEND_DOC_URL}`

        **Common Endpoints**
        - `GET /health` to verify backend and database availability
        - `GET /api/products` to list uploaded products
        - `POST /api/products` to create a new product
        - `GET /api/clients` to list onboarded clients
        - `POST /api/clients` to create a client record
        - `GET /api/media` to load media assets
        - `POST /api/media` to upload media assets
        - `GET /api/youtube/videos` to load YouTube content
        - `GET /api/conversations/{platform}` to fetch conversations by platform

        **How the UI Uses the API**
        - The dashboard loads products, clients, media, YouTube videos, and conversations from these endpoints after login
        - Product uploads from Media Center are written through the API
        - Client onboarding writes new records through the API
        """)

    elif st.session_state.doc_section == "Webhooks":
        st.markdown("""
        ### 🔔 Webhooks

        Use webhooks to receive real-time events from connected platforms and automation flows.

        **Supported Events**
        - New message received
        - New comment on media
        - Lead created
        - Payment status changed

        **Webhook Best Practices**
        - Validate the source signature before processing events
        - Retry failed deliveries with exponential backoff
        - Keep handlers idempotent so duplicate events are safe
        """)

        st.code(
            "POST /webhooks/{platform}\n"
            "Headers:\n"
            "  X-Signature: <signed-payload>\n"
            "Body:\n"
            "  {\"event\": \"message.created\", \"data\": {...}}",
            language="text"
        )

    elif st.session_state.doc_section == "SDKs":
        st.markdown("""
        ### 📦 SDKs

        The platform can be integrated from backend services, automations, and internal tools.

        **Recommended Setup**
        - Python for backend automation and AI workflows
        - JavaScript for dashboards and client-side integrations
        - Webhooks for lightweight event forwarding

        **Typical Workflow**
        1. Authenticate with your API key
        2. Create or sync products
        3. Pull conversations from connected channels
        4. Post AI-assisted replies or trigger follow-up tasks

        **Internal App Modules**
        - `dashboard.py` launches the Streamlit interface
        - `main.py` exposes the FastAPI backend
        - `database.py` manages SQLite persistence
        - Workers and integrations live under the packaged app modules for background and platform tasks
        """)

    else:
        st.markdown("""
        ### ❓ Frequently Asked Questions

        **Which platforms are supported?**  
        WhatsApp, TikTok, YouTube, Telegram, Facebook, and Instagram.

        **Can AI suggest replies automatically?**  
        Yes. The assistant can draft replies for chats, comments, and lead follow-ups.

        **Do I need to upload products first?**  
        It is recommended because the AI uses product context to personalize replies.

        **Can I switch plans later?**  
        Yes. You can update your connected platform package from the Billing page.

        **Where do I find each tool in the app?**  
        Use the sidebar. Every main area of the product has a dedicated navigation entry.

        **Where do uploads and new records go?**  
        Product, client, and media actions are stored through the backend API and reflected back into the dashboard.

        **What is simulated vs. live?**  
        Some platform interactions are demo-friendly in the UI, while the backend structure is prepared for real platform integrations.
        """)


def main():
    ensure_session_state()
    apply_styling()
    render_app_topbar()

    if not st.session_state.logged_in:
        if st.session_state.show_landing:
            landing_page()
            return
        login_screen()
        return

    render_sidebar()

    subscription_status = (st.session_state.get("subscription_status") or "inactive").strip().lower()
    render_subscription_banner(subscription_status)
    if subscription_status != "active" and st.session_state.current_page not in {"Billing", "Docs"}:
        st.session_state.current_page = "Billing"
        st.info("A monthly subscription is required to unlock workspace features. Open Billing to activate your plan.")

    page_handlers = {
        "Dashboard": dashboard_page,
        "Onboard Client": onboard_client_page,
        "Media Center": media_center_page,
        "Product Memory": product_memory_page,
        "Live Chat": live_chat_page,
        "Analytics": analytics_page,
        "Connections": connections_page,
        "Settings": settings_page,
        "Admin": admin_dashboard_page,
        "Billing": billing_page,
        "Docs": documentation_page,
    }

    if subscription_status != "active" and st.session_state.current_page not in {"Billing", "Docs"}:
        billing_page()
    else:
        page_handlers.get(st.session_state.current_page, dashboard_page)()


if __name__ == "__main__":
    main()
