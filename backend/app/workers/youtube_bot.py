import os
import sqlite3
import time
import json
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from dotenv import load_dotenv

from database import (
    DB_PATH,
    get_user_products,
    save_interaction_to_db,
    check_usage_limit,
    increment_usage
)
from ai_engine import generate_ai_response

load_dotenv()

# --- CONFIGURATION ---
SCOPES = ['https://www.googleapis.com/auth/youtube.force-ssl']

# --- UTILITY FUNCTIONS ---

def get_youtube_client(token_json):
    """Creates an authorized YouTube API client for a specific user."""
    try:
        creds_data = json.loads(token_json)
        creds = Credentials.from_authorized_user_info(creds_data, SCOPES)
        
        # Auto-refresh the token if it expired (Google tokens last 1 hour)
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            # Note: We don't save back here, but the updated creds work for this session
            
        return build('youtube', 'v3', credentials=creds)
    except Exception as e:
        print(f"❌ Auth Error: {e}")
        return None

# --- CORE LOGIC ---

def process_user_channel(user):
    """The main logic for a single user's YouTube channel."""
    email = user['email']
    token = user['youtube_token']
    channel_id = user['youtube_channel_id']
    
    # 1. Check if user is over their SaaS limit
    if not check_usage_limit(email):
        print(f"🛑 Usage limit reached for {email}. Skipping.")
        return

    youtube = get_youtube_client(token)
    if not youtube:
        return

    # Fetch user's products for AI context
    products = get_user_products(email)

    try:
        # Fetch latest comments
        request = youtube.commentThreads().list(
            part="snippet",
            allThreadsRelatedToChannelId=channel_id,
            maxResults=10,
            order="time"
        )
        response = request.execute()

        for item in response.get('items', []):
            comment = item['snippet']['topLevelComment']
            comment_id = comment['id']
            user_text = comment['snippet']['textOriginal']
            author_name = comment['snippet']['authorDisplayName']
            author_id = comment['snippet']['authorChannelId']['value']

            # --- ANTI-SPAM & LOGIC CHECKS ---
            # Don't reply to self/owner
            if author_id == channel_id:
                continue

            # Don't reply if already answered
            if item['snippet']['totalReplyCount'] > 0:
                continue

            # Final check: Does user still have credits (in case loop is large)?
            if not check_usage_limit(email):
                break

            print(f"💬 New comment on {email}'s channel from {author_name}: {user_text}")

            # Generate AI response (now product-aware, and will save interaction & trigger alerts)
            ai_reply = generate_ai_response(
                business_id=channel_id,          # business_id can be the channel ID
                customer_id=author_id,
                user_text=user_text,
                platform="YouTube",
                products=products
            )

            # Post the Reply to YouTube
            youtube.comments().insert(
                part="snippet",
                body={
                    "snippet": {
                        "parentId": comment_id,
                        "textOriginal": ai_reply
                    }
                }
            ).execute()
            
            # No need to increment_usage or save_interaction here; generate_ai_response already did.
            print(f"✅ Replied for {email}")

    except Exception as e:
        if "commentsDisabled" in str(e):
            print(f"⏭️ Skipping {email}: Comments are disabled on this video.")
        else:
            print(f"⚠️ Error for {email}: {e}")

def run_bot():
    print("🚀 Saintvellian YouTube SaaS Bot is Live...")
    while True:
        try:
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Only pull active subscribers with connected accounts
            cursor.execute("SELECT * FROM users WHERE subscription_status = 'active' AND youtube_token IS NOT NULL")
            active_users = cursor.fetchall()
            conn.close()

            for user in active_users:
                process_user_channel(user)

            print("😴 Scanning finished. Sleeping for 5 minutes...")
            time.sleep(300) 
            
        except Exception as e:
            print(f"❌ Critical Loop Error: {e}")
            time.sleep(60)

if __name__ == "__main__":
    run_bot()