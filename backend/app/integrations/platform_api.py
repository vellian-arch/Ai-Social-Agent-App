import requests
import json
import os
import logging

logger = logging.getLogger(__name__)

def send_whatsapp_message(customer_number, text, phone_id, access_token):
    """Sends a reply back to WhatsApp via Meta's Graph API."""
    url = f"https://graph.facebook.com/v18.0/{phone_id}/messages"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": customer_number,
        "type": "text",
        "text": {"body": text}
    }
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"❌ WhatsApp API Error: {e}")
        return {"error": str(e)}

def send_tiktok_comment_reply(video_id, comment_id, text, access_token):
    """Replies to a comment on a TikTok video."""
    url = "https://open.tiktokapis.com/v2/item/comment/reply/"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json; charset=UTF-8"
    }
    payload = {
        "item_id": video_id,
        "comment_id": comment_id,
        "content": text
    }
    try:
        response = requests.post(url, headers=headers, json=payload)
        return response.json()
    except Exception as e:
        logger.error(f"❌ TikTok Comment Error: {e}")
        return {"error": str(e)}

def send_tiktok_dm(recipient_open_id, text, access_token):
    """Sends a direct message through TikTok's messaging API."""
    url = "https://open.tiktokapis.com/v2/messaging/send/"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    payload = {
        "recipient_openid": recipient_open_id,
        "message": {"text": text}
    }
    try:
        response = requests.post(url, headers=headers, json=payload)
        return response.json()
    except Exception as e:
        logger.error(f"❌ TikTok DM Error: {e}")
        return {"error": str(e)}

def get_tiktok_shop_order(order_id, shop_id, access_token):
    """
    Fetches order details from TikTok Shop.
    Requires TikTok Shop Partner API permissions.
    """
    url = "https://open-api.tiktokglobalshop.com/api/order/get_order_detail"
    params = {
        "app_key": os.getenv("TIKTOK_CLIENT_KEY"),
        "shop_id": shop_id,
        "order_id_list": f"[{order_id}]"
    }
    headers = {
        "x-tts-access-token": access_token,
        "Content-Type": "application/json"
    }
    try:
        response = requests.get(url, params=params, headers=headers)
        data = response.json()
        if data.get("code") == 0:
            order_data = data.get("data", {}).get("order_list", [{}])[0]
            status = order_data.get("order_status_msg", "Unknown")
            return {"status": "success", "order_status": status, "details": order_data}
        else:
            return {"status": "error", "message": data.get("message", "Order not found")}
    except Exception as e:
        logger.error(f"❌ TikTok Shop API Error: {e}")
        return {"status": "error", "message": str(e)}

def post_youtube_reply(comment_id, text, access_token):
    """Posts a reply to a YouTube comment."""
    url = "https://www.googleapis.com/youtube/v3/comments"
    params = {"part": "snippet"}
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    payload = {
        "snippet": {
            "parentId": comment_id,
            "textOriginal": text
        }
    }
    try:
        response = requests.post(url, params=params, headers=headers, json=payload)
        return response.json()
    except Exception as e:
        logger.error(f"❌ YouTube Reply Error: {e}")
        return {"error": str(e)}

def send_telegram_message(chat_id, text, bot_token=None):
    """
    Sends a message to a Telegram chat using a bot token.
    If bot_token not provided, uses TELEGRAM_BOT_TOKEN from environment.
    """
    token = bot_token or os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.error("No Telegram bot token provided")
        return {"error": "No bot token"}
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML"
    }
    try:
        response = requests.post(url, json=payload)
        return response.json()
    except Exception as e:
        logger.error(f"❌ Telegram API Error: {e}")
        return {"error": str(e)}
