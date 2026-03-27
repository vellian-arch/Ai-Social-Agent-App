import os
import time
import requests
import sqlite3
from ai_engine import generate_ai_response
from database import (
    get_business_config,
    get_user_products,
    save_interaction_to_db,
    increment_usage,
    update_youtube_tokens,
    check_usage_limit,
)
from platform_api import post_youtube_reply

DB_PATH = "ai_business_memory.db"
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")


def refresh_google_token(refresh_token):
    """Uses the refresh token to get a brand new access_token from Google."""
    url = "https://oauth2.googleapis.com/token"
    payload = {
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token",
    }
    response = requests.post(url, data=payload)
    res_data = response.json()
    return res_data.get("access_token")


def fetch_youtube_comments(access_token, channel_id):
    """Fetch latest comment threads for a given channel ID."""
    url = "https://www.googleapis.com/youtube/v3/commentThreads"
    params = {
        "part": "snippet",
        "allThreadsRelatedToChannelId": channel_id,
        "maxResults": 5,
        "order": "time",
        "access_token": access_token,
    }
    response = requests.get(url, params=params)
    if response.status_code == 401:  # Token expired
        return "EXPIRED"
    return response.json().get("items", [])


def run_worker():
    print("🎬 Saintvellian YouTube Worker is Live...")
    while True:
        try:
            with sqlite3.connect(DB_PATH) as conn:
                conn.row_factory = sqlite3.Row
                users = conn.execute(
                    "SELECT * FROM users WHERE ai_active_youtube = 1 AND youtube_token IS NOT NULL"
                ).fetchall()

            for user in users:
                email = user["email"]
                token = user["youtube_token"]
                refresh_token = user["youtube_refresh_token"]
                channel_id = user["youtube_channel_id"]

                if not channel_id:
                    print(f"⚠️ No channel ID for {email}, skipping.")
                    continue

                # 1. Check usage limit before processing
                if not check_usage_limit(email):
                    print(f"🛑 Usage limit reached for {email}")
                    continue

                # 2. Fetch comments
                items = fetch_youtube_comments(token, channel_id)

                # 3. If token expired, refresh it automatically
                if items == "EXPIRED" and refresh_token:
                    print(f"🔄 Refreshing YouTube token for {email}...")
                    new_token = refresh_google_token(refresh_token)
                    if new_token:
                        update_youtube_tokens(email, new_token)
                        token = new_token
                        items = fetch_youtube_comments(token, channel_id)

                # 4. Process each new comment
                if isinstance(items, list):
                    # Fetch user's products for AI context
                    products = get_user_products(email)

                    for item in items:
                        # Check usage limit again inside loop
                        if not check_usage_limit(email):
                            break

                        comment = item["snippet"]["topLevelComment"]["snippet"]
                        comment_id = item["snippet"]["topLevelComment"]["id"]
                        author_name = comment["authorDisplayName"]
                        author_channel = comment["authorChannelId"]["value"]
                        text = comment["textOriginal"]

                        # Skip if it's the channel owner's own comment
                        if author_channel == channel_id:
                            continue

                        # Skip if already has replies
                        if item["snippet"]["totalReplyCount"] > 0:
                            continue

                        print(f"💬 New YouTube comment for {email} from {author_name}: {text}")

                        # Generate AI response (product-aware, will save interaction & trigger alerts)
                        ai_reply = generate_ai_response(
                            business_id=channel_id,
                            customer_id=author_channel,
                            user_text=text,
                            platform="YouTube",
                            products=products,
                        )

                        # Post reply using user's token
                        result = post_youtube_reply(comment_id, ai_reply, token)
                        if "error" not in result:
                            print(f"✅ Replied to comment {comment_id}")
                        else:
                            print(f"❌ Failed to reply: {result}")

            time.sleep(60)
        except Exception as e:
            print(f"⚠️ Worker Error: {e}")
            time.sleep(30)


if __name__ == "__main__":
    run_worker()
