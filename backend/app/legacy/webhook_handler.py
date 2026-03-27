from flask import Flask, request, jsonify
import os
import requests
import sqlite3
from ai_engine import generate_ai_response, extract_order_id
from database import (
    get_business_config,
    get_user_products,
    save_interaction_to_db,
    increment_usage,
    update_tiktok_tokens,
    update_youtube_tokens
)
from platform_api import send_whatsapp_message, send_tiktok_comment_reply, get_tiktok_shop_order

app = Flask(__name__)

# --- CONFIGURATION ---
TIKTOK_CLIENT_KEY = os.getenv("TIKTOK_CLIENT_KEY", "")
TIKTOK_CLIENT_SECRET = os.getenv("TIKTOK_CLIENT_SECRET", "")

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
BACKEND_PUBLIC_URL = os.getenv("BACKEND_PUBLIC_URL", "").strip()
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "")


def resolve_redirect_uri(path):
    if BACKEND_PUBLIC_URL:
        normalized_path = {
            "/callback/google": "/oauth/youtube/callback",
            "/callback/tiktok": "/oauth/tiktok/callback",
        }.get(path, path)
        return f"{BACKEND_PUBLIC_URL.rstrip('/')}{normalized_path}"
    if path in {"/callback/google", "/oauth/youtube/callback"}:
        return os.getenv("GOOGLE_REDIRECT_URI") or "http://localhost:8000/oauth/youtube/callback"
    return os.getenv("TIKTOK_REDIRECT_URI") or "http://localhost:8000/oauth/tiktok/callback"


def _safe_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default

# --- 1. TIKTOK OAUTH CALLBACK ---
@app.route('/callback/tiktok', methods=['GET', 'POST'])
@app.route('/oauth/tiktok/callback', methods=['GET', 'POST'])
def tiktok_callback():
    code = request.args.get('code')
    user_email = request.args.get('state') 
    if not code:
        return "TikTok Handshake Endpoint Active", 200

    token_url = "https://open.tiktokapis.com/v2/oauth/token/"
    payload = {
        "client_key": TIKTOK_CLIENT_KEY,
        "client_secret": TIKTOK_CLIENT_SECRET,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": resolve_redirect_uri("/oauth/tiktok/callback")
    }
    
    try:
        response = requests.post(token_url, data=payload)
        res_data = response.json()
        if "access_token" in res_data:
            update_tiktok_tokens(user_email, res_data["access_token"], res_data.get("refresh_token"))
            return "✅ TikTok Connected! You can now close this tab.", 200
    except Exception as e:
        return f"❌ Connection Error: {str(e)}", 400
    return "❌ Failed to connect", 400

# --- 2. GOOGLE/YOUTUBE OAUTH CALLBACK ---
@app.route('/callback/google', methods=['GET'])
@app.route('/oauth/youtube/callback', methods=['GET'])
def google_callback():
    code = request.args.get('code')
    user_email = request.args.get('state')
    if not code: return "Error: No code received", 400

    token_url = "https://oauth2.googleapis.com/token"
    payload = {
        "code": code,
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "redirect_uri": resolve_redirect_uri("/oauth/youtube/callback"),
        "grant_type": "authorization_code",
    }
    
    try:
        response = requests.post(token_url, data=payload, timeout=30)
        response.raise_for_status()
        res_data = response.json()
    except Exception as e:
        return f"❌ Connection Error: {str(e)}", 400

    if "access_token" in res_data:
        update_youtube_tokens(user_email, res_data["access_token"], res_data.get("refresh_token"))
        return "✅ YouTube Connected!", 200
    return "❌ Failed", 400

# --- 3. UNIVERSAL WEBHOOK ---
@app.route('/webhook', methods=['GET', 'POST'])
def universal_webhook():
    if request.method == 'GET':
        if request.args.get('hub.verify_token') == VERIFY_TOKEN:
            return request.args.get('hub.challenge'), 200
        return 'Invalid token', 403

    data = request.get_json(silent=True) or {}
    if not isinstance(data, dict):
        return jsonify({"status": "ignored"}), 200
    if data.get('type') == 'verify' or data.get('event') == 'tiktok.ping':
        return jsonify({"status": "success", "challenge": data.get('challenge')}), 200

    try:
        biz_id, cust_no, msg_body, platform, video_id = None, None, None, None, None

        # A. WhatsApp Detector
        entries = data.get('entry') or []
        if entries and isinstance(entries, list):
            first_entry = entries[0] or {}
            changes = first_entry.get('changes') or []
            if changes and isinstance(changes, list):
                entry = (changes[0] or {}).get('value') or {}
                messages = entry.get('messages') or []
                if messages and isinstance(messages, list):
                    message = messages[0] or {}
                    metadata = entry.get('metadata') or {}
                    text = message.get('text') or {}
                    biz_id = metadata.get('phone_number_id')
                    cust_no = message.get('from')
                    msg_body = text.get('body')
                    if biz_id and cust_no and msg_body:
                        platform = "whatsapp"
            
        # B. TikTok Detector
        elif data.get('event') == 'video.comment.new':
            payload = data.get('data') or {}
            biz_id = payload.get('user_id')          # TikTok Open ID of the business
            cust_no = payload.get('comment_id')
            video_id = payload.get('video_id')
            msg_body = payload.get('content')
            if biz_id and cust_no and video_id and msg_body:
                platform = "tiktok"

        if not platform:
            return jsonify({"status": "ignored"}), 200

        # Get user configuration (includes tokens and email)
        config = get_business_config(biz_id)
        if not config:
            print(f"No user found for platform ID {biz_id}")
            return jsonify({"status": "user_not_found"}), 200

        # Check if AI is active for this platform
        if not config.get(f'ai_active_{platform}', 1):
            print(f"AI inactive for {platform}")
            return jsonify({"status": "ai_inactive"}), 200

        # Check usage limit
        if _safe_int(config.get('message_count')) >= _safe_int(config.get('message_limit'), default=0):
            print(f"Usage limit reached for {config['email']}")
            return jsonify({"status": "limit_reached"}), 200

        # Fetch user's product catalog (for product-aware AI)
        user_email = config['email']
        products = get_user_products(user_email)

        # 1. Generate AI response (product-aware, saves interaction and triggers alerts)
        ai_reply = generate_ai_response(
            business_id=biz_id,
            customer_id=cust_no,
            user_text=msg_body,
            platform=platform,
            products=products
        )

        # 2. OPTION A: If message contains an order ID, fetch real TikTok Shop status
        order_id = extract_order_id(msg_body)
        if order_id and platform == "tiktok":
            shop_data = get_tiktok_shop_order(
                order_id,
                config.get('tiktok_shop_id'),
                config.get('tiktok_access_token')
            )
            if shop_data and shop_data.get('status') == 'success':
                status_msg = f" I've checked your order {order_id}. The status is: {shop_data.get('order_status', 'unknown')}."
                ai_reply += status_msg

        # 3. Increment usage counter
        increment_usage(user_email)

        # 4. Send reply via platform API
        if platform == "whatsapp":
            # Use the WhatsApp token stored for this user, or fallback to global env
            token = config.get('whatsapp_token') or os.getenv("WHATSAPP_TOKEN")
            send_whatsapp_message(cust_no, ai_reply, biz_id, token)
        elif platform == "tiktok":
            token = config.get('tiktok_access_token')
            if token:
                send_tiktok_comment_reply(video_id, cust_no, ai_reply, token)
            else:
                print("No TikTok token available")

        return jsonify({"status": "success"}), 200

    except Exception as e:
        print(f"🔥 Webhook Error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    app.run(port=8000, debug=True)
