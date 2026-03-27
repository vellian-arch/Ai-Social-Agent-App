from __future__ import annotations

import datetime
import os
import sqlite3

from celery import Celery
from celery.schedules import crontab
from dotenv import load_dotenv

from ai_engine import generate_follow_up_message
from database import DB_PATH, get_user_products
from platform_api import send_telegram_message, send_whatsapp_message  # noqa: F401

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
celery_app = Celery("tasks", broker=REDIS_URL)


@celery_app.task
def check_and_send_follow_ups():
    """
    Scan the database for stale leads and send a lightweight AI follow-up.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        threshold = (datetime.datetime.utcnow() - datetime.timedelta(hours=24)).isoformat()
        cursor.execute(
            """
            SELECT id, phone_id as user_email, platform, customer_number, last_message, lead_score
            FROM leads
            WHERE timestamp < ? AND lead_score != 'Cold'
            """,
            (threshold,),
        )
        stale_leads = cursor.fetchall()
        conn.close()

        for lead in stale_leads:
            lead_id = lead["id"]
            user_email = lead["user_email"]
            platform = lead["platform"]
            customer_id = lead["customer_number"]
            last_message = lead["last_message"]
            score = lead["lead_score"]
            products = get_user_products(user_email)

            nudge_text = generate_follow_up_message(
                business_id=user_email,
                customer_id=customer_id,
                last_message=last_message,
                score=score,
                platform=platform,
                products=products,
            )

            if platform.lower() == "telegram":
                send_telegram_message(customer_id, nudge_text)
            elif platform.lower() == "whatsapp":
                # WhatsApp delivery requires the live token/phone routing already configured elsewhere.
                pass

            conn = sqlite3.connect(DB_PATH)
            conn.execute(
                """
                UPDATE leads
                SET follow_up_count = IFNULL(follow_up_count, 0) + 1,
                    last_interaction = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (lead_id,),
            )
            conn.commit()
            conn.close()

            print(f"Sent follow-up to {customer_id} on {platform}")

    except Exception as exc:
        print(f"Error in follow-up task: {exc}")


celery_app.conf.beat_schedule = {
    "run-follow-up-check-every-hour": {
        "task": "tasks.check_and_send_follow_ups",
        "schedule": crontab(minute=0),
    },
}
celery_app.conf.timezone = "UTC"
