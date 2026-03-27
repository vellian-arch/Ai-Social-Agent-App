import os
import time
import requests
from database import get_business_config, get_user_products
from ai_engine import generate_ai_response
from platform_api import send_tiktok_dm  # hypothetical; you'll need to implement this
from dotenv import load_dotenv

load_dotenv()

# TikTok Config – these are for the bot's own app (not per user)
TIKTOK_ACCESS_TOKEN = os.getenv("TIKTOK_ACCESS_TOKEN")  # fallback, but we'll use per‑user tokens
APP_CLIENT_KEY = os.getenv("TIKTOK_CLIENT_KEY")

def fetch_tiktok_dms(access_token, business_id):
    """
    Fetch new direct messages for a business account.
    Note: TikTok's DM API is limited; this is a placeholder.
    You may need to use webhooks instead.
    """
    url = "https://open.tiktokapis.com/v2/message/list/"
    headers = {"Authorization": f"Bearer {access_token}"}
    params = {"business_id": business_id}  # adjust to actual API spec
    try:
        resp = requests.get(url, headers=headers, params=params)
        return resp.json().get("data", {}).get("messages", [])
    except Exception as e:
        print(f"Error fetching TikTok DMs: {e}")
        return []

def process_tiktok_message(message):
    """
    Process a single TikTok DM:
    - Identify the recipient business (you may have multiple businesses connected)
    - Generate AI reply
    - Send reply
    """
    # In a multi‑tenant setup, you need to know which business this message belongs to.
    # The message should contain a recipient ID (the business's open_id).
    recipient_open_id = message.get("recipient_open_id")  # adjust field name
    sender_open_id = message.get("sender_open_id")
    text = message.get("content", "")

    # Get the user (business) associated with this recipient_open_id
    config = get_business_config(recipient_open_id)  # assumes recipient_open_id is stored in users.tiktok_open_id
    if not config:
        print(f"No user found for TikTok open ID {recipient_open_id}")
        return

    # Check AI active and usage limits
    if not config.get("ai_active_tiktok"):
        print("AI inactive for TikTok")
        return
    if config["message_count"] >= config["message_limit"]:
        print("Usage limit reached")
        return

    # Fetch user's products
    products = get_user_products(config["email"])

    # Generate AI reply
    reply = generate_ai_response(
        business_id=recipient_open_id,
        customer_id=sender_open_id,
        user_text=text,
        platform="tiktok",
        products=products
    )

    # Send reply using the user's TikTok token
    token = config.get("tiktok_access_token") or TIKTOK_ACCESS_TOKEN
    send_tiktok_dm(sender_open_id, reply, token)

    # Note: generate_ai_response already increments usage and saves interaction
    # But you might need to increment_usage again if you handle it separately
    # It's better to keep it inside generate_ai_response as already done.

def check_tiktok_messages():
    """
    Poll for new messages for all connected TikTok businesses.
    This is inefficient; webhooks are preferred.
    """
    # In a real app, you would query the database for all users with TikTok tokens
    # and fetch messages for each.
    # For simplicity, we assume a single business ID stored in env.
    business_id = os.getenv("TIKTOK_BUSINESS_ID")  # you may need to set this
    if not business_id:
        print("No TIKTOK_BUSINESS_ID set")
        return

    # Get the user's config via business_id (which could be the tiktok_open_id)
    config = get_business_config(business_id)
    if not config:
        print(f"No user for business ID {business_id}")
        return

    token = config.get("tiktok_access_token") or TIKTOK_ACCESS_TOKEN
    messages = fetch_tiktok_dms(token, business_id)
    for msg in messages:
        process_tiktok_message(msg)

if __name__ == "__main__":
    while True:
        check_tiktok_messages()
        time.sleep(60)  # check every minute