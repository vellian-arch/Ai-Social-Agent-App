import os

import requests
import yagmail
from dotenv import load_dotenv
from sqlalchemy import select

from database import engine, notifications

load_dotenv()
FRONTEND_APP_URL = os.getenv("FRONTEND_APP_URL", "http://localhost:8501").rstrip("/")


def get_user_notification_settings(user_email):
    """
    Retrieve notification preferences for a given user from the database.
    Returns a dict with keys: email_notify, slack_webhook, discord_webhook, sms_number, notify_critical_only.
    If no settings found, returns default (email only, notify_critical_only=True).
    """
    stmt = select(
        notifications.c.email_notify,
        notifications.c.slack_webhook,
        notifications.c.discord_webhook,
        notifications.c.sms_number,
        notifications.c.notify_critical_only,
    ).where(notifications.c.user_email == user_email)
    with engine.connect() as conn:
        row = conn.execute(stmt).mappings().first()

    if row:
        return dict(row)

    # Default: email notifications enabled, no webhooks, critical only
    return {
        "email_notify": 1,
        "slack_webhook": None,
        "discord_webhook": None,
        "sms_number": None,
        "notify_critical_only": 1,
    }


def send_slack_alert(webhook_url, message):
    """Send a message to a Slack channel via incoming webhook."""
    try:
        payload = {"text": message}
        requests.post(webhook_url, json=payload)
    except Exception as e:
        print(f"Slack notification error: {e}")


def send_discord_alert(webhook_url, message):
    """Send a message to a Discord channel via webhook."""
    try:
        payload = {"content": message}
        requests.post(webhook_url, json=payload)
    except Exception as e:
        print(f"Discord notification error: {e}")


def send_sms_alert(phone_number, message):
    """
    Send an SMS alert using a service like Twilio.
    Placeholder – implement with your preferred SMS provider.
    """
    # Example using Twilio (commented out to avoid requiring twilio package)
    # from twilio.rest import Client
    # account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    # auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    # client = Client(account_sid, auth_token)
    # client.messages.create(body=message, from_=os.getenv("TWILIO_PHONE"), to=phone_number)
    print(f"SMS alert to {phone_number}: {message}")


def send_email_alert(recipient, subject, contents):
    """Send an email using yagmail."""
    try:
        sender = os.getenv("EMAIL_USER")
        password = os.getenv("EMAIL_PASS")
        if not sender or not password:
            print("Email credentials not configured.")
            return
        yag = yagmail.SMTP(sender, password)
        yag.send(to=recipient, subject=subject, contents=contents)
        print(f"Email alert sent to {recipient}")
    except Exception as e:
        print(f"Email sending error: {e}")


def send_lead_alert(platform, customer_id, user_text, summary="General Inquiry", score="Warm", user_email=None):
    """
    Sends a notification to the business owner based on their saved preferences.
    Only sends if the lead is 'Hot' or contains urgent keywords, unless the user
    has disabled 'notify_critical_only'.
    """
    if not user_email:
        print("No user email provided; cannot send notification.")
        return

    settings = get_user_notification_settings(user_email)

    urgent_keywords = ["refund", "scam", "wait", "stole", "angry", "broken", "help"]
    is_urgent = any(word in user_text.lower() for word in urgent_keywords) or score == "Hot"

    if settings.get("notify_critical_only") and not is_urgent:
        return

    priority_label = "🔥 HOT LEAD" if score == "Hot" else "🚨 URGENT INQUIRY"
    subject = f"{priority_label} on {platform}: {summary}"

    plain_message = f"""
{priority_label}
Platform: {platform}
Customer: {customer_id}
Summary: {summary}
Message: "{user_text}"
    """.strip()

    html_contents = [
        f"<h2>{priority_label}</h2>",
        f"<p><b>Platform:</b> {platform}</p>",
        f"<p><b>Customer ID:</b> {customer_id}</p>",
        f"<p><b>AI Summary:</b> {summary}</p>",
        f"<hr>",
        f"<p><b>Message Received:</b></p>",
        f"<i>\"{user_text}\"</i>",
        f"<br><br>",
        f"<a href='{FRONTEND_APP_URL}'>Open Command Center</a>",
    ]

    if settings.get("email_notify"):
        send_email_alert(user_email, subject, html_contents)

    if settings.get("slack_webhook"):
        send_slack_alert(settings["slack_webhook"], plain_message)

    if settings.get("discord_webhook"):
        send_discord_alert(settings["discord_webhook"], plain_message)

    if settings.get("sms_number"):
        send_sms_alert(settings["sms_number"], plain_message[:160])
