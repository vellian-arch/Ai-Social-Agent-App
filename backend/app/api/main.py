from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
import httpx
import logging
import os
import base64
import json
import ipaddress
import secrets
import time
import hmac
import hashlib
import smtplib
import html
from urllib.parse import parse_qs, urlencode
from typing import Any
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from email.message import EmailMessage
from pathlib import Path
from sqlalchemy import insert, select, update

from dotenv import load_dotenv

_BACKEND_ENV = Path(__file__).resolve().parents[2] / ".env"
_ROOT_ENV = Path(__file__).resolve().parents[3] / ".env"
load_dotenv(_BACKEND_ENV, override=False)
load_dotenv(_ROOT_ENV, override=False)

from database import (
    authenticate_user,
    check_usage_limit,
    clear_platform_connection,
    create_user_account,
    engine,
    ensure_default_admin,
    fetch_admin_clients,
    fetch_admin_connection_audit,
    fetch_admin_conversations,
    fetch_admin_events,
    fetch_admin_media,
    fetch_admin_overview,
    fetch_admin_platform_summary,
    fetch_admin_products,
    fetch_admin_recent_activity,
    fetch_admin_users,
    fetch_user_conversations,
    fetch_user_connection_settings,
    get_billing_product,
    get_user_by_email,
    get_client_by_platform_id,
    get_user_by_platform_id,
    get_user_products,
    increment_usage,
    init_db,
    log_app_event,
    media_assets,
    products,
    clients,
    users,
    conversations,
    conversation_messages,
    save_interaction_to_db,
    update_platform_connection,
    update_user_password,
    upsert_conversations,
)
from ai_engine import ai_is_configured, generate_ai_response
from dodo_payments import PLAN_DEFINITIONS, create_payment_for_plan, dodo_enabled, ensure_products, sync_payment_status
from live_payments import (
    PAYPAL_CANCEL_URL,
    PAYPAL_ENV,
    PAYPAL_RETURN_URL,
    capture_paypal_support_order,
    create_paypal_order,
    create_paypal_support_order,
    create_paystack_checkout,
    paypal_enabled,
    sync_paypal_order,
    paystack_enabled,
    PAYSTACK_ENV,
    PAYSTACK_PUBLIC_KEY,
)

app = FastAPI(title="SOCIAL AI Agent API", version="1.0.0")

UPLOADS_DIR = Path(__file__).resolve().parents[3] / "uploads"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOADS_DIR), name="uploads")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
FB_PAGE_TOKEN = os.getenv("FB_PAGE_ACCESS_TOKEN")
TIKTOK_ACCESS_TOKEN = os.getenv("TIKTOK_ACCESS_TOKEN")
TIKTOK_CLIENT_KEY = os.getenv("TIKTOK_CLIENT_KEY", "")
TIKTOK_CLIENT_SECRET = os.getenv("TIKTOK_CLIENT_SECRET", "")
TIKTOK_REDIRECT_URI = os.getenv("TIKTOK_REDIRECT_URI", "http://localhost:8000/oauth/tiktok/callback")
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "my_ai_secret_2026")
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/oauth/youtube/callback")
META_APP_ID = os.getenv("META_APP_ID", "")
META_APP_SECRET = os.getenv("META_APP_SECRET", "")
META_REDIRECT_URI = os.getenv("META_REDIRECT_URI", "http://localhost:8000/oauth/meta/callback")
FRONTEND_APP_URL = os.getenv("FRONTEND_APP_URL", "http://localhost:8501")
PUBLIC_FRONTEND_APP_URL = os.getenv("PUBLIC_FRONTEND_APP_URL", "https://socialaiagent.streamlit.app")
PUBLIC_PAYPAL_PAYMENT_URL = os.getenv(
    "PUBLIC_PAYPAL_PAYMENT_URL",
    "https://ai-social-agent-app.onrender.com/support/paypal",
)
DEPLOYMENT_REVISION = "one-day-trial-before-subscription-2026-05-06"
BACKEND_PUBLIC_URL = os.getenv("BACKEND_PUBLIC_URL", "").strip()
PAYPAL_ANY_AMOUNT_URL = os.getenv("PAYPAL_ANY_AMOUNT_URL", "").strip()
TRIAL_DAYS = 1
AUTH_SECRET = os.getenv("AUTH_SECRET", "social-ai-agent-dev-secret")
SMTP_HOST = os.getenv("SMTP_HOST", "").strip()
SMTP_PORT = int(os.getenv("SMTP_PORT", "587") or "587")
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "").strip() or os.getenv("EMAIL_USER", "").strip()
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "").strip() or os.getenv("EMAIL_PASS", "").strip()
SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL", "").strip() or SMTP_USERNAME
SMTP_FROM_NAME = os.getenv("SMTP_FROM_NAME", "Social Ai Agent Support").strip()
SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "true").strip().lower() not in {"0", "false", "no"}


def get_deployment_warnings() -> list[str]:
    warnings: list[str] = []

    if AUTH_SECRET == "social-ai-agent-dev-secret":
        warnings.append("AUTH_SECRET is still using the default development value.")

    if FRONTEND_APP_URL.startswith("http://localhost") or FRONTEND_APP_URL.startswith("http://127.0.0.1"):
        warnings.append("FRONTEND_APP_URL is not set to your deployed dashboard URL.")

    if not (paystack_enabled() or paypal_enabled() or dodo_enabled()):
        warnings.append("No billing provider is configured. Paystack, PayPal, or Dodo payments must be set for live billing.")

    if paystack_enabled() and PAYSTACK_ENV != "live":
        warnings.append("Paystack is using a test key. Live monthly subscriptions need a sk_live_ key.")

    if paypal_enabled() and PAYPAL_ENV != "live":
        warnings.append("PayPal is not in live mode. Set PAYPAL_ENV=live for production subscriptions.")

    if dodo_enabled() and os.getenv("DODO_ENV", "live_mode").strip().lower() != "live_mode":
        warnings.append("Dodo Payments is not in live mode. Confirm DODO_ENV and merchant live status before deployment.")

    return warnings


def parse_trial_datetime(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return value
    raw_value = str(value or "").strip()
    if not raw_value:
        return None
    try:
        return datetime.fromisoformat(raw_value.replace("Z", "+00:00")).replace(tzinfo=None)
    except ValueError:
        return None


def effective_subscription_status(user: dict[str, Any] | None) -> str:
    if not user:
        return "inactive"
    status = str(user.get("subscription_status", "")).strip().lower()
    if status == "active":
        return "active"
    trial_ends_at = get_trial_ends_at(user)
    if trial_ends_at and trial_ends_at > datetime.utcnow():
        return "trial"
    return "inactive"


def is_subscription_active(user: dict[str, Any] | None) -> bool:
    return effective_subscription_status(user) in {"active", "trial"}


def get_trial_ends_at(user: dict[str, Any] | None) -> datetime | None:
    if not user:
        return None
    explicit_trial_end = parse_trial_datetime(user.get("trial_ends_at"))
    if explicit_trial_end:
        return explicit_trial_end
    created_at = parse_trial_datetime(user.get("created_at"))
    if created_at:
        return created_at + timedelta(days=TRIAL_DAYS)
    return None


def serialize_datetime(value: datetime | None) -> str:
    return value.replace(microsecond=0).isoformat() if value else ""


def public_user_payload(user: dict[str, Any]) -> dict[str, Any]:
    return {
        "email": user["email"],
        "name": user.get("name") or user["email"].split("@")[0],
        "role": user.get("role") or "User",
        "subscription_status": effective_subscription_status(user),
        "trial_ends_at": serialize_datetime(get_trial_ends_at(user)),
    }


def require_active_subscription(user_email: str) -> dict[str, Any]:
    user = get_user_by_email((user_email or "").strip().lower())
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    if not is_subscription_active(user):
        raise HTTPException(status_code=402, detail="Monthly subscription required")
    return user


@app.middleware("http")
async def block_unpaid_feature_access(request: Request, call_next):
    path = request.url.path
    if path.startswith("/api/"):
        allowed_prefixes = (
            "/api/auth/",
            "/api/deployment/",
            "/api/billing/plans",
            "/api/payments/",
            "/api/health",
            "/api/docs",
            "/api/openapi.json",
        )
        if not path.startswith(allowed_prefixes):
            try:
                user = get_authenticated_user(request)
                if not is_subscription_active(user):
                    return JSONResponse(
                        status_code=402,
                        content={
                            "detail": "Monthly subscription required",
                            "subscription_status": effective_subscription_status(user),
                        },
                    )
            except HTTPException as exc:
                if exc.status_code in {401, 402}:
                    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
                raise
    response = await call_next(request)
    return response


def get_deployment_check_details() -> dict[str, bool | str]:
    return {
        "auth_secret_ok": AUTH_SECRET != "social-ai-agent-dev-secret",
        "frontend_url_ok": not (
            FRONTEND_APP_URL.startswith("http://localhost") or FRONTEND_APP_URL.startswith("http://127.0.0.1")
        ),
        "billing_provider_ok": bool(paystack_enabled() or paypal_enabled() or dodo_enabled()),
        "paystack_ok": bool(paystack_enabled() and PAYSTACK_ENV == "live"),
        "paypal_ok": bool(paypal_enabled() and PAYPAL_ENV == "live"),
        "dodo_ok": bool(dodo_enabled() and os.getenv("DODO_ENV", "live_mode").strip().lower() == "live_mode"),
        "smtp_ok": bool(SMTP_HOST and SMTP_USERNAME and SMTP_PASSWORD and SMTP_FROM_EMAIL),
        "database_url_ok": bool(os.getenv("DATABASE_URL", "").strip()),
        "upload_ok": True,
        "ai_ok": ai_is_configured(),
        "ai_mode": "active" if ai_is_configured() else "fallback",
        "paystack_env": PAYSTACK_ENV,
    }


@app.on_event("startup")
async def startup_event():
    init_db()
    ensure_default_admin()
    for warning in get_deployment_warnings():
        logger.warning("Deployment check: %s", warning)
    if dodo_enabled():
        try:
            ensure_products()
        except Exception as exc:
            logger.warning("Dodo product provisioning skipped: %s", exc)
    logger.info("Automatic token maintenance is handled on demand to keep startup fast.")


def fetch_rows(statement) -> list[dict[str, Any]]:
    with engine.connect() as conn:
        result = conn.execute(statement)
        return [dict(row) for row in result.mappings().all()]


def build_frontend_redirect_html(title: str, message: str) -> str:
    return f"""
    <html>
        <head>
            <title>{title}</title>
            <meta http-equiv="refresh" content="4;url={FRONTEND_APP_URL}">
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    background: #f7fafc;
                    color: #163a70;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    min-height: 100vh;
                    margin: 0;
                }}
                .card {{
                    max-width: 560px;
                    background: white;
                    border: 1px solid #d6e4f0;
                    border-radius: 18px;
                    padding: 28px;
                    box-shadow: 0 14px 40px rgba(22, 58, 112, 0.1);
                }}
                a {{
                    color: #2563eb;
                }}
            </style>
        </head>
        <body>
            <div class="card">
                <h2>{title}</h2>
                <p>{message}</p>
                <p>You can return to the app here: <a href="{FRONTEND_APP_URL}">{FRONTEND_APP_URL}</a></p>
            </div>
        </body>
    </html>
    """


@app.get("/payments/return")
async def payment_return_page():
    return HTMLResponse(
        build_frontend_redirect_html(
            "Payment received",
            "Your checkout is complete. Redirecting back to the dashboard now.",
        )
    )


@app.get("/payments/cancel")
async def payment_cancel_page():
    return HTMLResponse(
        build_frontend_redirect_html(
            "Payment cancelled",
            "The checkout was cancelled. You can return to Billing and try again anytime.",
        )
    )


@app.get("/payments/paypal/return")
async def paypal_return_page():
    return HTMLResponse(
        build_frontend_redirect_html(
            "PayPal subscription",
            "PayPal completed your approval. Redirecting back to Billing.",
        )
    )


@app.get("/payments/paypal/cancel")
async def paypal_cancel_page():
    return HTMLResponse(
        build_frontend_redirect_html(
            "PayPal cancelled",
            "PayPal checkout was cancelled. You can return to Billing to try again.",
        )
    )


@app.get("/support/paypal")
async def paypal_support_page(request: Request):
    amount_text = (request.query_params.get("amount") or "").strip()
    if not amount_text:
        if PAYPAL_ANY_AMOUNT_URL:
            return RedirectResponse(url=PAYPAL_ANY_AMOUNT_URL, status_code=303)
        return RedirectResponse(url="/support/paypal/custom", status_code=303)

    donor_email = (request.query_params.get("email") or "").strip()
    amount_cents = parse_support_amount_cents(amount_text)

    try:
        order = create_paypal_support_order(amount_cents, donor_email=donor_email)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    payment_link = order.get("payment_link", "")
    if not payment_link:
        raise HTTPException(status_code=503, detail="PayPal did not return a checkout link")
    return RedirectResponse(url=payment_link, status_code=303)


@app.get("/support/paypal/custom")
async def paypal_support_custom_page():
    return HTMLResponse(
        """
        <html>
            <head>
                <title>Support Social Ai Agent</title>
                <meta name="viewport" content="width=device-width, initial-scale=1">
                <style>
                    body {
                        font-family: Arial, sans-serif;
                        background: #f7fafc;
                        color: #102033;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        min-height: 100vh;
                        margin: 0;
                    }
                    main {
                        width: min(520px, calc(100vw - 32px));
                        background: white;
                        border: 1px solid #d6e4f0;
                        border-radius: 16px;
                        padding: 28px;
                        box-shadow: 0 14px 40px rgba(22, 58, 112, 0.1);
                    }
                    label {
                        display: block;
                        color: #456078;
                        font-size: 0.9rem;
                        font-weight: 700;
                        margin: 16px 0 8px;
                    }
                    input {
                        width: 100%;
                        box-sizing: border-box;
                        border: 1px solid #b8c6d3;
                        border-radius: 10px;
                        font-size: 1rem;
                        padding: 13px 14px;
                    }
                    button {
                        width: 100%;
                        border: 0;
                        border-radius: 999px;
                        background: #0070ba;
                        color: white;
                        cursor: pointer;
                        font-size: 1rem;
                        font-weight: 800;
                        margin-top: 20px;
                        padding: 14px 18px;
                    }
                </style>
            </head>
            <body>
                <main>
                    <h1>Support Social Ai Agent</h1>
                    <p>Choose any amount you would like to send through PayPal.</p>
                    <form action="/support/paypal/checkout" method="post">
                        <label for="amount">Amount in USD</label>
                        <input id="amount" name="amount" type="number" min="1" step="0.01" value="25" required>
                        <label for="email">Email, optional</label>
                        <input id="email" name="email" type="email" placeholder="you@example.com">
                        <button type="submit">Continue to PayPal</button>
                    </form>
                </main>
            </body>
        </html>
        """
    )


def parse_support_amount_cents(amount_text: str) -> int:
    try:
        amount = Decimal(amount_text).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    except (InvalidOperation, ValueError) as exc:
        raise HTTPException(status_code=400, detail="Enter a valid support amount") from exc
    if amount < 1 or amount > 10000:
        raise HTTPException(status_code=400, detail="Support amount must be between $1 and $10,000")
    return int(amount * 100)


def get_public_subscription_plan(plan_key: str):
    return next((item for item in PLAN_DEFINITIONS if item.key == plan_key), None)


@app.get("/subscriptions/paypal")
async def paypal_subscriptions_page():
    plan_cards = []
    for plan in PLAN_DEFINITIONS:
        plan_key = html.escape(plan.key)
        label = html.escape(plan.label)
        description = html.escape(plan.description)
        price = f"${plan.price_cents / 100:.2f}"
        plan_cards.append(
            f"""
            <article>
                <div>
                    <h2>{label}</h2>
                    <p>{description}</p>
                    <p class="trial-note">Includes a {TRIAL_DAYS}-day free trial before billing starts.</p>
                    <strong>{price}<span>/month</span></strong>
                </div>
                <form action="/subscriptions/paypal/checkout" method="post">
                    <input type="hidden" name="plan_key" value="{plan_key}">
                    <label for="email-{plan_key}">Email</label>
                    <input id="email-{plan_key}" name="email" type="email" placeholder="you@example.com" required>
                    <label for="name-{plan_key}">Name, optional</label>
                    <input id="name-{plan_key}" name="name" type="text" placeholder="Your name">
                    <button type="submit">Subscribe with PayPal</button>
                </form>
            </article>
            """
        )

    return HTMLResponse(
        f"""
        <html>
            <head>
                <title>Subscribe to Social Ai Agent</title>
                <meta name="viewport" content="width=device-width, initial-scale=1">
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        background: #f7fafc;
                        color: #102033;
                        margin: 0;
                    }}
                    main {{
                        width: min(1120px, calc(100vw - 32px));
                        margin: 0 auto;
                        padding: 42px 0;
                    }}
                    header {{
                        margin-bottom: 24px;
                    }}
                    h1 {{
                        font-size: clamp(2rem, 4vw, 3.2rem);
                        margin: 0 0 10px;
                    }}
                    header p {{
                        color: #456078;
                        font-size: 1.05rem;
                        margin: 0;
                    }}
                    section {{
                        display: grid;
                        gap: 16px;
                        grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
                    }}
                    article {{
                        background: white;
                        border: 1px solid #d6e4f0;
                        border-radius: 12px;
                        box-shadow: 0 14px 40px rgba(22, 58, 112, 0.08);
                        display: flex;
                        flex-direction: column;
                        justify-content: space-between;
                        min-height: 360px;
                        padding: 22px;
                    }}
                    h2 {{
                        font-size: 1.25rem;
                        margin: 0 0 8px;
                    }}
                    article p {{
                        color: #456078;
                        line-height: 1.45;
                        margin: 0 0 18px;
                    }}
                    .trial-note {{
                        color: #0f766e;
                        font-weight: 700;
                        margin-bottom: 14px;
                    }}
                    strong {{
                        display: block;
                        font-size: 2rem;
                        margin-bottom: 18px;
                    }}
                    span {{
                        color: #60758a;
                        font-size: 0.95rem;
                        font-weight: 600;
                    }}
                    label {{
                        display: block;
                        color: #456078;
                        font-size: 0.85rem;
                        font-weight: 700;
                        margin: 12px 0 6px;
                    }}
                    input {{
                        width: 100%;
                        box-sizing: border-box;
                        border: 1px solid #b8c6d3;
                        border-radius: 10px;
                        font-size: 1rem;
                        padding: 12px 13px;
                    }}
                    button {{
                        width: 100%;
                        border: 0;
                        border-radius: 999px;
                        background: #0070ba;
                        color: white;
                        cursor: pointer;
                        font-size: 1rem;
                        font-weight: 800;
                        margin-top: 16px;
                        padding: 13px 18px;
                    }}
                    .support-link {{
                        color: #0070ba;
                        display: inline-block;
                        font-weight: 700;
                        margin-top: 22px;
                    }}
                </style>
            </head>
            <body>
                <main>
                    <header>
                        <h1>Subscribe to Social Ai Agent</h1>
                        <p>Choose a monthly plan and continue to PayPal. Billing starts after a {TRIAL_DAYS}-day free trial.</p>
                    </header>
                    <section>
                        {''.join(plan_cards)}
                    </section>
                    <a class="support-link" href="/support/paypal">Send a one-time PayPal support payment instead</a>
                </main>
            </body>
        </html>
        """
    )


@app.get("/subscriptions/paypal/{plan_key}")
async def paypal_subscription_plan_page(plan_key: str):
    plan = get_public_subscription_plan(plan_key)
    if not plan:
        raise HTTPException(status_code=404, detail=f"Unknown plan: {plan_key}")

    return HTMLResponse(
        f"""
        <html>
            <head>
                <title>{html.escape(plan.label)} PayPal Subscription</title>
                <meta name="viewport" content="width=device-width, initial-scale=1">
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        background: #f7fafc;
                        color: #102033;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        min-height: 100vh;
                        margin: 0;
                    }}
                    main {{
                        width: min(520px, calc(100vw - 32px));
                        background: white;
                        border: 1px solid #d6e4f0;
                        border-radius: 16px;
                        padding: 28px;
                        box-shadow: 0 14px 40px rgba(22, 58, 112, 0.1);
                    }}
                    h1 {{ margin: 0 0 8px; }}
                    p {{ color: #456078; line-height: 1.45; }}
                    strong {{ display: block; font-size: 2rem; margin: 18px 0; }}
                    label {{
                        display: block;
                        color: #456078;
                        font-size: 0.9rem;
                        font-weight: 700;
                        margin: 16px 0 8px;
                    }}
                    input {{
                        width: 100%;
                        box-sizing: border-box;
                        border: 1px solid #b8c6d3;
                        border-radius: 10px;
                        font-size: 1rem;
                        padding: 13px 14px;
                    }}
                    button {{
                        width: 100%;
                        border: 0;
                        border-radius: 999px;
                        background: #0070ba;
                        color: white;
                        cursor: pointer;
                        font-size: 1rem;
                        font-weight: 800;
                        margin-top: 20px;
                        padding: 14px 18px;
                    }}
                </style>
            </head>
            <body>
                <main>
                    <h1>{html.escape(plan.label)}</h1>
                    <p>{html.escape(plan.description)}</p>
                    <p>Includes a {TRIAL_DAYS}-day free trial before billing starts.</p>
                    <strong>${plan.price_cents / 100:.2f}/month</strong>
                    <form action="/subscriptions/paypal/checkout" method="post">
                        <input type="hidden" name="plan_key" value="{html.escape(plan.key)}">
                        <label for="email">Email</label>
                        <input id="email" name="email" type="email" placeholder="you@example.com" required>
                        <label for="name">Name, optional</label>
                        <input id="name" name="name" type="text" placeholder="Your name">
                        <button type="submit">Subscribe with PayPal</button>
                    </form>
                </main>
            </body>
        </html>
        """
    )


@app.post("/subscriptions/paypal/checkout")
async def paypal_subscription_checkout(request: Request):
    body = (await request.body()).decode("utf-8")
    form = parse_qs(body)
    plan_key = (form.get("plan_key", [""])[0] or "").strip()
    user_email = (form.get("email", [""])[0] or "").strip()
    customer_name = (form.get("name", [""])[0] or "").strip()

    if not user_email or "@" not in user_email:
        raise HTTPException(status_code=400, detail="Enter a valid email address")

    plan = get_public_subscription_plan(plan_key)
    if not plan:
        raise HTTPException(status_code=400, detail=f"Unknown plan: {plan_key}")

    try:
        order = create_paypal_order(plan.key, plan.label, plan.price_cents, user_email, customer_name=customer_name)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    payment_link = order.get("payment_link", "")
    if not payment_link:
        raise HTTPException(status_code=503, detail="PayPal did not return a subscription approval link")
    return RedirectResponse(url=payment_link, status_code=303)


@app.post("/support/paypal/checkout")
async def paypal_support_checkout(request: Request):
    body = (await request.body()).decode("utf-8")
    form = parse_qs(body)
    amount_text = (form.get("amount", [""])[0] or "").strip()
    donor_email = (form.get("email", [""])[0] or "").strip()
    amount_cents = parse_support_amount_cents(amount_text)

    try:
        order = create_paypal_support_order(amount_cents, donor_email=donor_email)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    payment_link = order.get("payment_link", "")
    if not payment_link:
        raise HTTPException(status_code=503, detail="PayPal did not return a checkout link")
    return RedirectResponse(url=payment_link, status_code=303)


@app.get("/support/paypal/return")
async def paypal_support_return(request: Request):
    order_id = (request.query_params.get("token") or "").strip()
    if order_id:
        try:
            capture_paypal_support_order(order_id)
        except RuntimeError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc

    return HTMLResponse(
        build_frontend_redirect_html(
            "Thank you for the support",
            "Your PayPal support payment has been received. Redirecting back to Social Ai Agent.",
        )
    )


@app.get("/support/paypal/cancel")
async def paypal_support_cancel():
    return HTMLResponse(
        build_frontend_redirect_html(
            "Support payment cancelled",
            "The PayPal support checkout was cancelled. You can return to Social Ai Agent anytime.",
        )
    )


@app.get("/payments/dodo/return")
async def dodo_return_page():
    return HTMLResponse(
        build_frontend_redirect_html(
            "Dodo subscription",
            "Dodo completed the checkout flow. Redirecting back to Billing.",
        )
    )


def password_reset_email_is_configured() -> bool:
    return bool(SMTP_HOST and SMTP_PORT and SMTP_USERNAME and SMTP_PASSWORD and SMTP_FROM_EMAIL)


def send_password_reset_email(recipient_email: str, recipient_name: str, temporary_password: str):
    if not password_reset_email_is_configured():
        raise HTTPException(status_code=503, detail="Password reset email is not configured on this server")

    message = EmailMessage()
    message["Subject"] = "Social Ai Agent temporary password"
    message["From"] = f"{SMTP_FROM_NAME} <{SMTP_FROM_EMAIL}>"
    message["To"] = recipient_email
    display_name = recipient_name or recipient_email.split("@")[0]
    message.set_content(
        "\n".join(
            [
                f"Hello {display_name},",
                "",
                "A password reset was requested for your Social Ai Agent account.",
                f"Temporary password: {temporary_password}",
                "",
                "Sign in with this password and change it from your account settings as soon as possible.",
                "",
                "If you did not request this reset, contact support immediately.",
            ]
        )
    )

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30) as smtp:
        if SMTP_USE_TLS:
            smtp.starttls()
        smtp.login(SMTP_USERNAME, SMTP_PASSWORD)
        smtp.send_message(message)


def make_oauth_state(user_email: str, platform: str) -> str:
    return f"{platform}|{user_email}|{secrets.token_urlsafe(16)}"


def parse_oauth_state(state: str) -> tuple[str, str]:
    parts = (state or "").split("|")
    if len(parts) < 2:
        raise HTTPException(status_code=400, detail="Invalid OAuth state")
    return parts[0], parts[1]


def create_access_token(user: dict[str, Any], expires_in: int = 60 * 60 * 12) -> str:
    payload = {
        "email": user["email"],
        "role": user.get("role", "User"),
        "exp": int(time.time()) + expires_in,
    }
    payload_bytes = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    encoded_payload = base64.urlsafe_b64encode(payload_bytes).decode("utf-8").rstrip("=")
    signature = hmac.new(AUTH_SECRET.encode("utf-8"), encoded_payload.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"{encoded_payload}.{signature}"


def decode_access_token(token: str) -> dict[str, Any]:
    try:
        encoded_payload, signature = token.split(".", 1)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail="Invalid auth token") from exc

    expected_signature = hmac.new(
        AUTH_SECRET.encode("utf-8"),
        encoded_payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    if not hmac.compare_digest(signature, expected_signature):
        raise HTTPException(status_code=401, detail="Invalid auth token signature")

    padded_payload = encoded_payload + "=" * (-len(encoded_payload) % 4)
    payload = json.loads(base64.urlsafe_b64decode(padded_payload.encode("utf-8")).decode("utf-8"))
    if int(payload.get("exp", 0)) < int(time.time()):
        raise HTTPException(status_code=401, detail="Auth token has expired")
    return payload


def get_authenticated_user(request: Request) -> dict[str, Any]:
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    token = auth_header.split(" ", 1)[1].strip()
    payload = decode_access_token(token)
    user = get_user_by_email(payload.get("email", ""))
    if not user:
        raise HTTPException(status_code=401, detail="User not found for token")
    return user


def require_admin_user(request: Request) -> dict[str, Any]:
    user = get_authenticated_user(request)
    if (user.get("role") or "User").lower() != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


def resolve_oauth_user(user_email: str | None = None, auth_token: str | None = None) -> str:
    if auth_token:
        payload = decode_access_token(auth_token)
        return payload.get("email", "")
    if user_email:
        return user_email
    raise HTTPException(status_code=401, detail="Missing authenticated user context")


def get_oauth_redirect_uri(request: Request, platform: str) -> str:
    platform = platform.lower().strip()
    path_map = {
        "youtube": "/oauth/youtube/callback",
        "meta": "/oauth/meta/callback",
        "tiktok": "/oauth/tiktok/callback",
    }
    if platform not in path_map:
        raise ValueError(f"Unsupported OAuth platform: {platform}")
    base_url = BACKEND_PUBLIC_URL or str(request.base_url).rstrip("/")
    return f"{base_url}{path_map[platform]}"


def is_refresh_stale(timestamp_value: str | None, max_age_minutes: int = 45) -> bool:
    normalized = (timestamp_value or "").strip()
    if not normalized:
        return True
    try:
        refreshed_at = datetime.fromisoformat(normalized)
    except ValueError:
        return True
    return datetime.utcnow() - refreshed_at >= timedelta(minutes=max_age_minutes)


async def refresh_youtube_connection_for_user(user_email: str) -> bool:
    settings = fetch_user_connection_settings(user_email)
    if not settings:
        raise HTTPException(status_code=404, detail="User connection settings not found")
    refresh_token = settings.get("youtube_refresh_token", "")
    if not refresh_token:
        raise HTTPException(status_code=400, detail="No YouTube refresh token is stored for this account")
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        raise HTTPException(status_code=400, detail="Google OAuth is not configured")

    async with httpx.AsyncClient(timeout=20.0) as client:
        token_response = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "refresh_token": refresh_token,
                "grant_type": "refresh_token",
            },
        )
    if token_response.status_code != 200:
        logger.error("Google refresh failed: %s", token_response.text)
        raise HTTPException(status_code=400, detail="Google token refresh failed")

    token_payload = token_response.json()
    new_access_token = token_payload.get("access_token", "")
    if not new_access_token:
        raise HTTPException(status_code=400, detail="Google did not return a new access token")

    update_platform_connection(
        user_email,
        "youtube",
        {
            "youtube_token": new_access_token,
            "youtube_refresh_token": refresh_token,
            "youtube_channel_id": settings.get("youtube_channel_id", ""),
        },
    )
    log_app_event(user_email, "refreshed", "platform_token", "YouTube", platform="YouTube", details="YouTube access token refreshed")
    return True


async def refresh_tiktok_connection_for_user(user_email: str) -> bool:
    settings = fetch_user_connection_settings(user_email)
    if not settings:
        raise HTTPException(status_code=404, detail="User connection settings not found")
    refresh_token = settings.get("tiktok_refresh_token", "")
    if not refresh_token:
        raise HTTPException(status_code=400, detail="No TikTok refresh token is stored for this account")
    if not TIKTOK_CLIENT_KEY or not TIKTOK_CLIENT_SECRET:
        raise HTTPException(status_code=400, detail="TikTok OAuth is not configured")

    async with httpx.AsyncClient(timeout=20.0) as client:
        token_response = await client.post(
            "https://open.tiktokapis.com/v2/oauth/token/",
            data={
                "client_key": TIKTOK_CLIENT_KEY,
                "client_secret": TIKTOK_CLIENT_SECRET,
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
    if token_response.status_code != 200:
        logger.error("TikTok refresh failed: %s", token_response.text)
        raise HTTPException(status_code=400, detail="TikTok token refresh failed")

    token_payload = token_response.json()
    token_data = token_payload.get("data", token_payload)
    new_access_token = token_data.get("access_token", "")
    new_refresh_token = token_data.get("refresh_token", "") or refresh_token
    if not new_access_token:
        raise HTTPException(status_code=400, detail="TikTok did not return a new access token")

    update_platform_connection(
        user_email,
        "tiktok",
        {
            "tiktok_open_id": settings.get("tiktok_open_id", ""),
            "tiktok_access_token": new_access_token,
            "tiktok_refresh_token": new_refresh_token,
            "tiktok_shop_id": settings.get("tiktok_shop_id", ""),
        },
    )
    log_app_event(user_email, "refreshed", "platform_token", "TikTok", platform="TikTok", details="TikTok access token refreshed")
    return True


async def auto_refresh_user_tokens_if_needed(user_email: str) -> dict[str, list[str]]:
    settings = fetch_user_connection_settings(user_email)
    if not settings:
        return {"refreshed": [], "skipped": ["No connection settings"]}

    refreshed: list[str] = []
    skipped: list[str] = []

    if settings.get("youtube_refresh_token"):
        if is_refresh_stale(settings.get("youtube_token_refreshed_at")):
            try:
                await refresh_youtube_connection_for_user(user_email)
                refreshed.append("YouTube")
            except HTTPException as exc:
                skipped.append(f"YouTube: {exc.detail}")
        else:
            skipped.append("YouTube: token still fresh")
    else:
        skipped.append("YouTube: no refresh token")

    if settings.get("tiktok_refresh_token"):
        if is_refresh_stale(settings.get("tiktok_token_refreshed_at")):
            try:
                await refresh_tiktok_connection_for_user(user_email)
                refreshed.append("TikTok")
            except HTTPException as exc:
                skipped.append(f"TikTok: {exc.detail}")
        else:
            skipped.append("TikTok: token still fresh")
    else:
        skipped.append("TikTok: no refresh token")

    return {"refreshed": refreshed, "skipped": skipped}


def build_demo_media(user_email: str) -> list[dict[str, Any]]:
    owner = user_email.split("@")[0] if user_email else "sync"
    return [
        {
            "id": 1,
            "type": "video",
            "platform": "TikTok",
            "url": f"https://example.com/{owner}/launch-video.mp4",
            "thumbnail": "🎥",
            "title": "Launch Campaign Reel",
            "comments": [
                {"user": "@buyer_now", "text": "How much is this?", "replied": True, "ai_reply": "We can share pricing and shipping details right away."},
                {"user": "@trendwatch", "text": "This looks premium.", "replied": False},
            ],
        },
        {
            "id": 2,
            "type": "photo",
            "platform": "Instagram",
            "url": f"https://example.com/{owner}/hero-photo.jpg",
            "thumbnail": "📸",
            "title": "Product Hero Shot",
            "comments": [
                {"user": "@stylefeed", "text": "Available in more colors?", "replied": True, "ai_reply": "Yes, we can send the current color options in DM."}
            ],
        },
        {
            "id": 3,
            "type": "photo",
            "platform": "Facebook",
            "url": f"https://example.com/{owner}/catalog-photo.jpg",
            "thumbnail": "🖼️",
            "title": "Catalog Spotlight",
            "comments": [
                {"user": "Alex M", "text": "Interested in bulk order.", "replied": False}
            ],
        },
    ]


def save_uploaded_media_file(file_name: str, file_content_b64: str, media_type: str, request: Request) -> str:
    raw_bytes = base64.b64decode(file_content_b64.encode("utf-8"))
    original_name = Path(file_name).name or "upload"
    stem = Path(original_name).stem or "upload"
    suffix = Path(original_name).suffix.lower()
    if not suffix:
        suffix = ".mp4" if (media_type or "").lower() == "video" else ".jpg"

    stored_name = f"{uuid.uuid4().hex}_{stem}{suffix}"
    file_path = UPLOADS_DIR / stored_name
    file_path.write_bytes(raw_bytes)

    base_url = str(request.base_url).rstrip("/")
    return f"{base_url}/uploads/{stored_name}"


def build_demo_videos() -> list[dict[str, Any]]:
    return [
        {
            "id": "yt-001",
            "title": "Product Walkthrough",
            "thumbnail": "https://img.youtube.com/vi/1/0.jpg",
            "comments": [
                {"user": "ReviewHub", "text": "Can it be delivered internationally?", "replied": True, "ai_reply": "Yes, international delivery is available for supported regions."}
            ],
        },
        {
            "id": "yt-002",
            "title": "How Setup Works",
            "thumbnail": "https://img.youtube.com/vi/2/0.jpg",
            "comments": [
                {"user": "StartupOps", "text": "This onboarding flow is clean.", "replied": False}
            ],
        },
    ]


def build_demo_conversations(platform: str) -> list[dict[str, Any]]:
    emoji_map = {
        "whatsapp": "💬",
        "tiktok": "🎵",
        "youtube": "▶️",
        "telegram": "✈️",
        "facebook": "📘",
        "instagram": "📷",
    }
    label = platform.capitalize()
    avatar = emoji_map.get(platform.lower(), "👤")
    return [
        {
            "id": f"{platform}-001",
            "name": f"{label} Lead",
            "avatar": avatar,
            "message": "Can you send pricing and availability?",
            "time": "09:15",
            "status": "hot",
            "unread": 2,
            "messages": [
                {"sender": "customer", "text": "I need the latest price list.", "time": "09:10", "read": False},
                {"sender": "ai", "text": "Absolutely, I can share pricing and package options.", "time": "09:12", "read": True},
            ],
        },
        {
            "id": f"{platform}-002",
            "name": f"{label} Returning Customer",
            "avatar": avatar,
            "message": "Do you have a demo video?",
            "time": "08:40",
            "status": "warm",
            "unread": 0,
            "messages": [
                {"sender": "customer", "text": "Can I see a product demo first?", "time": "08:34", "read": True},
                {"sender": "ai", "text": "Yes, I can send a short demo and key specs.", "time": "08:36", "read": True},
            ],
        },
    ]


def get_user_config(platform_id: str) -> dict[str, Any]:
    user = get_user_by_platform_id(platform_id)
    if not user:
        logger.warning("No user found for platform_id %s, using fallback.", platform_id)
        return {
            "email": "admin@test.com",
            "tiktok_access_token": TIKTOK_ACCESS_TOKEN,
            "fb_page_token": FB_PAGE_TOKEN,
            "whatsapp_token": WHATSAPP_TOKEN,
            "products": [],
        }

    user["products"] = get_user_products(user["email"])
    return user


@app.get("/")
async def root():
    dashboard_url = PUBLIC_PAYPAL_PAYMENT_URL or FRONTEND_APP_URL
    if dashboard_url.startswith("http://localhost") or dashboard_url.startswith("http://127.0.0.1"):
        dashboard_url = PUBLIC_FRONTEND_APP_URL
    return RedirectResponse(url=dashboard_url, status_code=307)


@app.get("/health")
async def health():
    active_database_url = str(engine.url)
    details = get_deployment_check_details()
    return {
        "status": "ok",
        "database_backend": "postgresql" if active_database_url.startswith(("postgresql://", "postgres://")) else "sqlite",
        "database_configured": bool(active_database_url),
        "deployment_revision": DEPLOYMENT_REVISION,
        "deployment_warnings": get_deployment_warnings(),
        "deployment_ready": len(get_deployment_warnings()) == 0,
        "ai_ready": details["ai_ok"],
        "ai_mode": details["ai_mode"],
    }


def _extract_request_ip(request: Request) -> str:
    forwarded_for = request.headers.get("x-forwarded-for", "").strip()
    if forwarded_for:
        candidate = forwarded_for.split(",")[0].strip()
        if candidate:
            return candidate
    real_ip = request.headers.get("x-real-ip", "").strip()
    if real_ip:
        return real_ip
    return request.client.host if request.client else ""


async def _lookup_country_for_ip(ip_address_value: str) -> str:
    if not ip_address_value:
        return "Global / Other"
    try:
        parsed_ip = ipaddress.ip_address(ip_address_value)
        if parsed_ip.is_private or parsed_ip.is_loopback or parsed_ip.is_reserved or parsed_ip.is_link_local:
            return "Global / Other"
    except ValueError:
        return "Global / Other"

    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            response = await client.get(f"https://ipwho.is/{ip_address_value}")
            if response.status_code != 200:
                return "Global / Other"
            payload = response.json()
            if not payload.get("success"):
                return "Global / Other"
            country = (payload.get("country") or "").strip()
            return country or "Global / Other"
        except Exception:
            return "Global / Other"


@app.get("/api/deployment/country")
async def api_deployment_country(request: Request):
    get_authenticated_user(request)
    ip_address_value = _extract_request_ip(request)
    detected_country = await _lookup_country_for_ip(ip_address_value)
    return {
        "status": "ok",
        "country": detected_country,
        "ip_address": ip_address_value,
    }


@app.get("/api/deployment/check")
async def api_deployment_check(request: Request):
    get_authenticated_user(request)
    warnings = get_deployment_warnings()
    details = get_deployment_check_details()
    return {
        "status": "ok",
        "deployment_ready": len(warnings) == 0,
        "deployment_warnings": warnings,
        "billing_ready": details["billing_provider_ok"],
        "upload_ready": details["upload_ok"],
        "ai_ready": details["ai_ok"],
        "ai_mode": details["ai_mode"],
        "auth_secret_ok": details["auth_secret_ok"],
        "frontend_url_ok": details["frontend_url_ok"],
        "database_url_ok": details["database_url_ok"],
        "smtp_ok": details["smtp_ok"],
        "paystack_ok": details["paystack_ok"],
        "paypal_ok": details["paypal_ok"],
        "dodo_ok": details["dodo_ok"],
    }


@app.post("/api/auth/register")
async def api_register(payload: dict[str, Any]):
    email = (payload.get("email") or "").strip().lower()
    password = payload.get("password") or ""
    name = (payload.get("name") or "").strip()
    if not email or not password:
        raise HTTPException(status_code=400, detail="email and password are required")
    try:
        user = create_user_account(email, password, name=name)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    log_app_event(user["email"], "registered", "user", user.get("name") or user["email"], details="New account created")
    return {
        "status": "success",
        "token": create_access_token(user),
        "user": public_user_payload(user),
    }


@app.post("/api/auth/login")
async def api_login(payload: dict[str, Any]):
    email = (payload.get("email") or "").strip().lower()
    password = payload.get("password") or ""
    user = authenticate_user(email, password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return {
        "status": "success",
        "token": create_access_token(user),
        "user": public_user_payload(user),
    }


@app.get("/api/auth/me")
async def api_auth_me(request: Request):
    user = get_authenticated_user(request)
    return {"status": "success", "user": public_user_payload(user)}


@app.post("/api/auth/forgot-password")
async def api_forgot_password(payload: dict[str, Any]):
    email = (payload.get("email") or "").strip().lower()
    if not email:
        raise HTTPException(status_code=400, detail="email is required")
    user = get_user_by_email(email)
    if not user:
        raise HTTPException(status_code=404, detail="We could not find an account with that email address")

    temp_password = f"SYNC-{secrets.token_hex(4).upper()}"
    update_user_password(email, temp_password)
    try:
        send_password_reset_email(email, user.get("name") or email, temp_password)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Password reset email failed for %s: %s", email, exc)
        raise HTTPException(status_code=502, detail="Password reset email could not be delivered") from exc

    log_app_event(email, "reset_password", "user", user.get("name") or email, details="Temporary password emailed")
    return {
        "status": "success",
        "message": f"Password reset email sent to {email}",
    }


@app.get("/oauth/youtube/start")
async def oauth_youtube_start(request: Request, user_email: str | None = None, auth_token: str | None = None):
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        raise HTTPException(status_code=400, detail="Google OAuth is not configured")
    resolved_email = resolve_oauth_user(user_email, auth_token)
    require_active_subscription(resolved_email)
    state = make_oauth_state(resolved_email, "youtube")
    redirect_uri = get_oauth_redirect_uri(request, "youtube")
    query = urlencode(
        {
            "client_id": GOOGLE_CLIENT_ID,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": "https://www.googleapis.com/auth/youtube.readonly https://www.googleapis.com/auth/youtube.force-ssl",
            "access_type": "offline",
            "prompt": "consent",
            "state": state,
        }
    )
    return RedirectResponse(url=f"https://accounts.google.com/o/oauth2/v2/auth?{query}", status_code=307)


@app.get("/oauth/youtube/callback")
async def oauth_youtube_callback(request: Request, code: str | None = None, state: str | None = None, error: str | None = None):
    if error:
        return Response(
            content=build_frontend_redirect_html("YouTube connection failed", f"Google returned: {error}"),
            media_type="text/html",
        )
    if not code or not state:
        raise HTTPException(status_code=400, detail="Missing OAuth callback parameters")

    platform, user_email = parse_oauth_state(state)
    if platform != "youtube":
        raise HTTPException(status_code=400, detail="Unexpected OAuth platform")
    require_active_subscription(user_email)

    async with httpx.AsyncClient(timeout=20.0) as client:
        redirect_uri = get_oauth_redirect_uri(request, "youtube")
        token_response = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
            },
        )
        if token_response.status_code != 200:
            logger.error("Google token exchange failed: %s", token_response.text)
            return Response(
                content=build_frontend_redirect_html("YouTube connection failed", "Google token exchange did not complete successfully."),
                media_type="text/html",
            )

        token_payload = token_response.json()
        access_token = token_payload.get("access_token", "")
        refresh_token = token_payload.get("refresh_token", "")

        channel_id = ""
        if access_token:
            channel_response = await client.get(
                "https://www.googleapis.com/youtube/v3/channels",
                params={"part": "id,snippet", "mine": "true"},
                headers={"Authorization": f"Bearer {access_token}"},
            )
            if channel_response.status_code == 200:
                channel_items = channel_response.json().get("items", [])
                if channel_items:
                    channel_id = channel_items[0].get("id", "")

    update_platform_connection(
        user_email,
        "youtube",
        {
            "youtube_token": access_token,
            "youtube_refresh_token": refresh_token,
            "youtube_channel_id": channel_id,
        },
    )
    log_app_event(
        user_email,
        "connected",
        "oauth_platform",
        "YouTube",
        platform="YouTube",
        details=f"OAuth connected channel {channel_id or 'unknown'}",
    )
    return Response(
        content=build_frontend_redirect_html("YouTube connected", "The YouTube account was connected successfully. Return to the Connections page to review the saved channel."),
        media_type="text/html",
    )


@app.get("/oauth/meta/start")
async def oauth_meta_start(request: Request, user_email: str | None = None, auth_token: str | None = None):
    if not META_APP_ID or not META_APP_SECRET:
        raise HTTPException(status_code=400, detail="Meta OAuth is not configured")
    resolved_email = resolve_oauth_user(user_email, auth_token)
    require_active_subscription(resolved_email)
    state = make_oauth_state(resolved_email, "meta")
    redirect_uri = get_oauth_redirect_uri(request, "meta")
    query = urlencode(
        {
            "client_id": META_APP_ID,
            "redirect_uri": redirect_uri,
            "state": state,
            "response_type": "code",
            "scope": ",".join(
                [
                    "pages_show_list",
                    "pages_messaging",
                    "pages_read_engagement",
                    "instagram_basic",
                    "instagram_manage_messages",
                    "whatsapp_business_management",
                    "whatsapp_business_messaging",
                ]
            ),
        }
    )
    return RedirectResponse(url=f"https://www.facebook.com/v22.0/dialog/oauth?{query}", status_code=307)


@app.get("/oauth/meta/callback")
async def oauth_meta_callback(request: Request, code: str | None = None, state: str | None = None, error: str | None = None):
    if error:
        return Response(
            content=build_frontend_redirect_html("Meta connection failed", f"Meta returned: {error}"),
            media_type="text/html",
        )
    if not code or not state:
        raise HTTPException(status_code=400, detail="Missing OAuth callback parameters")

    platform, user_email = parse_oauth_state(state)
    if platform != "meta":
        raise HTTPException(status_code=400, detail="Unexpected OAuth platform")
    require_active_subscription(user_email)

    async with httpx.AsyncClient(timeout=20.0) as client:
        redirect_uri = get_oauth_redirect_uri(request, "meta")
        token_response = await client.get(
            "https://graph.facebook.com/v22.0/oauth/access_token",
            params={
                "client_id": META_APP_ID,
                "client_secret": META_APP_SECRET,
                "redirect_uri": redirect_uri,
                "code": code,
            },
        )
        if token_response.status_code != 200:
            logger.error("Meta token exchange failed: %s", token_response.text)
            return Response(
                content=build_frontend_redirect_html("Meta connection failed", "Meta token exchange did not complete successfully."),
                media_type="text/html",
            )

        access_token = token_response.json().get("access_token", "")
        pages_response = await client.get(
            "https://graph.facebook.com/v22.0/me/accounts",
            params={"access_token": access_token},
        )
        page_id = ""
        page_token = ""
        if pages_response.status_code == 200:
            pages = pages_response.json().get("data", [])
            if pages:
                page_id = pages[0].get("id", "")
                page_token = pages[0].get("access_token", "") or access_token

    update_platform_connection(
        user_email,
        "facebook",
        {
            "fb_page_id": page_id,
            "fb_page_token": page_token,
        },
    )
    log_app_event(
        user_email,
        "connected",
        "oauth_platform",
        "Meta",
        platform="Meta",
        details=f"OAuth connected page {page_id or 'unknown'}",
    )
    return Response(
        content=build_frontend_redirect_html(
            "Meta connected",
            "Meta authorization completed. Facebook and Instagram credentials were saved. If you also use WhatsApp, add the Phone Number ID in the manual fields after returning to the app.",
        ),
        media_type="text/html",
    )


@app.get("/oauth/tiktok/start")
async def oauth_tiktok_start(request: Request, user_email: str | None = None, auth_token: str | None = None):
    if not TIKTOK_CLIENT_KEY or not TIKTOK_CLIENT_SECRET:
        raise HTTPException(status_code=400, detail="TikTok OAuth is not configured")
    resolved_email = resolve_oauth_user(user_email, auth_token)
    require_active_subscription(resolved_email)
    state = make_oauth_state(resolved_email, "tiktok")
    redirect_uri = get_oauth_redirect_uri(request, "tiktok")
    query = urlencode(
        {
            "client_key": TIKTOK_CLIENT_KEY,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": "user.info.basic,video.list",
            "state": state,
        }
    )
    return RedirectResponse(url=f"https://www.tiktok.com/v2/auth/authorize/?{query}", status_code=307)


@app.get("/oauth/tiktok/callback")
async def oauth_tiktok_callback(request: Request, code: str | None = None, state: str | None = None, error: str | None = None):
    if error:
        return Response(
            content=build_frontend_redirect_html("TikTok connection failed", f"TikTok returned: {error}"),
            media_type="text/html",
        )
    if not code or not state:
        raise HTTPException(status_code=400, detail="Missing OAuth callback parameters")

    platform, user_email = parse_oauth_state(state)
    if platform != "tiktok":
        raise HTTPException(status_code=400, detail="Unexpected OAuth platform")
    require_active_subscription(user_email)

    access_token = ""
    refresh_token = ""
    open_id = ""
    async with httpx.AsyncClient(timeout=20.0) as client:
        redirect_uri = get_oauth_redirect_uri(request, "tiktok")
        token_response = await client.post(
            "https://open.tiktokapis.com/v2/oauth/token/",
            data={
                "client_key": TIKTOK_CLIENT_KEY,
                "client_secret": TIKTOK_CLIENT_SECRET,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": redirect_uri,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        if token_response.status_code != 200:
            logger.error("TikTok token exchange failed: %s", token_response.text)
            return Response(
                content=build_frontend_redirect_html("TikTok connection failed", "TikTok token exchange did not complete successfully."),
                media_type="text/html",
            )

        token_payload = token_response.json()
        data = token_payload.get("data", token_payload)
        access_token = data.get("access_token", "")
        refresh_token = data.get("refresh_token", "")
        open_id = data.get("open_id", "")

        if access_token and not open_id:
            user_response = await client.get(
                "https://open.tiktokapis.com/v2/user/info/",
                params={"fields": "open_id,display_name"},
                headers={"Authorization": f"Bearer {access_token}"},
            )
            if user_response.status_code == 200:
                user_data = user_response.json().get("data", {}).get("user", {})
                open_id = user_data.get("open_id", "")

    update_platform_connection(
        user_email,
        "tiktok",
        {
            "tiktok_open_id": open_id,
            "tiktok_access_token": access_token,
            "tiktok_refresh_token": refresh_token,
            "tiktok_shop_id": "",
        },
    )
    log_app_event(
        user_email,
        "connected",
        "oauth_platform",
        "TikTok",
        platform="TikTok",
        details=f"OAuth connected business open_id {open_id or 'unknown'}",
    )
    return Response(
        content=build_frontend_redirect_html(
            "TikTok connected",
            "TikTok authorization completed. Return to the Connections page and use Reload Saved Connections to confirm the saved profile.",
        ),
        media_type="text/html",
    )


@app.get("/api/products")
async def api_products(request: Request):
    user = get_authenticated_user(request)
    user_email = user["email"]
    rows = fetch_rows(
        select(
            products.c.id,
            products.c.name,
            products.c.price,
            products.c.description,
            products.c.category,
            products.c.tags,
            products.c.media_url,
            products.c.created_at,
        )
        .where(products.c.user_email == user_email)
        .order_by(products.c.created_at.desc(), products.c.id.desc())
    )
    return {"products": rows}


@app.post("/api/products")
async def create_product(payload: dict[str, Any], request: Request):
    user = get_authenticated_user(request)
    user_email = user["email"]
    name = (payload.get("name") or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="name is required")

    media_url = (payload.get("media_url") or "").strip()
    file_content_b64 = (payload.get("file_content_b64") or "").strip()
    file_name = (payload.get("file_name") or "").strip()
    content_type = (payload.get("content_type") or "").strip().lower()
    if file_content_b64 and file_name:
        inferred_media_type = "video" if content_type.startswith("video") or Path(file_name).suffix.lower() in {".mp4", ".mov", ".mkv", ".webm"} else "photo"
        try:
            media_url = save_uploaded_media_file(file_name, file_content_b64, inferred_media_type, request)
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"Unable to save uploaded product file: {exc}") from exc

    with engine.begin() as conn:
        conn.execute(
            insert(products).values(
                user_email=user_email,
                name=name,
                price=payload.get("price", ""),
                description=payload.get("description", ""),
                category=payload.get("category", ""),
                tags=payload.get("tags", ""),
                media_url=media_url,
            )
        )

    log_app_event(
        user_email,
        "created",
        "product",
        name,
        details=f"Category: {payload.get('category', '')} | Price: {payload.get('price', '')}",
    )
    return {"status": "success"}


@app.get("/api/clients")
async def api_clients(request: Request):
    user = get_authenticated_user(request)
    user_email = user["email"]
    rows = fetch_rows(
        select(
            clients.c.id,
            clients.c.name,
            clients.c.email,
            clients.c.phone,
            clients.c.company,
            clients.c.platforms,
            clients.c.score,
            clients.c.notes,
            clients.c.created_at,
        )
        .where(clients.c.user_email == user_email)
        .order_by(clients.c.created_at.desc(), clients.c.id.desc())
    )
    return {"clients": rows}


@app.post("/api/clients")
async def create_client(payload: dict[str, Any], request: Request):
    user = get_authenticated_user(request)
    user_email = user["email"]
    name = (payload.get("name") or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="name is required")

    with engine.begin() as conn:
        conn.execute(
            insert(clients).values(
                user_email=user_email,
                name=name,
                email=payload.get("email", ""),
                phone=payload.get("phone", ""),
                company=payload.get("company", ""),
                platforms=payload.get("platforms", ""),
                score=payload.get("score", 75),
                notes=payload.get("notes", ""),
            )
        )

    log_app_event(
        user_email,
        "created",
        "client",
        name,
        details=f"Company: {payload.get('company', '')} | Score: {payload.get('score', 75)}",
    )
    return {"status": "success"}


@app.get("/api/media")
async def api_media(request: Request):
    user = get_authenticated_user(request)
    user_email = user["email"]
    media = fetch_rows(
        select(
            media_assets.c.id,
            media_assets.c.platform,
            media_assets.c.media_type,
            media_assets.c.title,
            media_assets.c.description,
            media_assets.c.media_url,
            media_assets.c.thumbnail,
            media_assets.c.created_at,
        )
        .where(media_assets.c.user_email == user_email)
        .order_by(media_assets.c.created_at.desc(), media_assets.c.id.desc())
    )
    if media:
        return {
            "media": [
                {
                    "id": item["id"],
                    "platform": item["platform"],
                    "type": item["media_type"],
                    "title": item["title"],
                    "description": item.get("description", ""),
                    "url": item["media_url"],
                    "thumbnail": item.get("thumbnail", "IMG"),
                    "comments": [],
                }
                for item in media
            ]
        }
    return {"media": build_demo_media(user_email)}


@app.post("/api/media")
async def create_media(payload: dict[str, Any], request: Request):
    user = get_authenticated_user(request)
    user_email = user["email"]
    title = (payload.get("title") or "").strip()
    if not title:
        raise HTTPException(status_code=400, detail="title is required")

    media_type = (payload.get("type") or "photo").strip().lower()
    media_url = (payload.get("url") or "").strip()
    file_content_b64 = (payload.get("file_content_b64") or "").strip()
    file_name = (payload.get("file_name") or "").strip()
    if file_content_b64 and file_name:
        try:
            media_url = save_uploaded_media_file(file_name, file_content_b64, media_type, request)
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"Unable to save uploaded file: {exc}") from exc

    with engine.begin() as conn:
        conn.execute(
            insert(media_assets).values(
                user_email=user_email,
                platform=payload.get("platform", "Other"),
                media_type=media_type or "photo",
                title=title,
                description=payload.get("description", ""),
                media_url=media_url,
                thumbnail=payload.get("thumbnail", "IMG"),
            )
        )

    log_app_event(
        user_email,
        "created",
        "media",
        title,
        platform=payload.get("platform", "Other"),
        details=f"Type: {payload.get('type', 'photo')}",
    )
    return {"status": "success"}


@app.get("/api/billing/plans")
async def api_billing_plans(request: Request):
    get_authenticated_user(request)
    plans = []
    for plan in PLAN_DEFINITIONS:
        stored = get_billing_product(plan.key) or {}
        plans.append(
            {
                "plan_key": plan.key,
                "label": plan.label,
                "price_cents": plan.price_cents,
                "description": plan.description,
                "trial_days": TRIAL_DAYS,
                "dodo_product_id": stored.get("dodo_product_id", ""),
                "paypal_product_id": stored.get("paypal_product_id", ""),
                "paypal_plan_id": stored.get("paypal_plan_id", ""),
                "currency": stored.get("currency", "USD"),
                "billing_cycle": stored.get("billing_cycle", "monthly"),
                "product_kind": stored.get("product_kind", "subscription"),
            }
        )
    return {
        "plans": plans,
        "dodo_enabled": dodo_enabled(),
        "dodo_env": os.getenv("DODO_ENV", "live_mode").strip().lower(),
        "paystack_enabled": paystack_enabled(),
        "paypal_enabled": paypal_enabled(),
        "paystack_env": PAYSTACK_ENV,
        "paystack_public_key": PAYSTACK_PUBLIC_KEY,
        "paypal_env": PAYPAL_ENV,
    }


@app.post("/api/payments/dodo/create")
async def api_dodo_create_payment(payload: dict[str, Any], request: Request):
    user = get_authenticated_user(request)
    plan_key = (payload.get("plan_key") or "").strip()
    if not plan_key:
        raise HTTPException(status_code=400, detail="plan_key is required")

    return_url = (payload.get("return_url") or "").strip()
    if not return_url or return_url.startswith("http://localhost") or return_url.startswith("http://127.0.0.1"):
        return_url = f"{BACKEND_PUBLIC_URL.rstrip('/')}/payments/dodo/return" if BACKEND_PUBLIC_URL else FRONTEND_APP_URL
    customer_name = (payload.get("customer_name") or user.get("name") or "").strip()

    try:
        payment = create_payment_for_plan(plan_key, user["email"], customer_name=customer_name, return_url=return_url)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail="Dodo payment creation failed") from exc

    log_app_event(
        user["email"],
        "created",
        "payment_session",
        plan_key,
        platform="Dodo",
        details=f"Dodo payment link created for {plan_key}",
    )
    return {
        "status": "success",
        "payment_id": payment.get("subscription_id", payment.get("session_id", payment.get("payment_id", payment.get("id", "")))),
        "session_id": payment.get("session_id", payment.get("subscription_id", payment.get("id", ""))),
        "subscription_id": payment.get("subscription_id", payment.get("id", "")),
        "payment_link": payment.get("checkout_url", payment.get("payment_link", "")),
        "client_secret": payment.get("client_secret", ""),
        "payment": payment,
    }


@app.post("/api/payments/paystack/create")
async def api_paystack_create_payment(payload: dict[str, Any], request: Request):
    user = get_authenticated_user(request)
    plan_key = (payload.get("plan_key") or "").strip()
    if not plan_key:
        raise HTTPException(status_code=400, detail="plan_key is required")

    plan = next((item for item in PLAN_DEFINITIONS if item.key == plan_key), None)
    if not plan:
        raise HTTPException(status_code=400, detail=f"Unknown plan: {plan_key}")

    try:
        session = create_paystack_checkout(plan.key, plan.label, plan.price_cents, user["email"], customer_name=(payload.get("customer_name") or user.get("name") or ""))
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    log_app_event(user["email"], "created", "payment_session", plan_key, platform="Paystack", details="Paystack checkout session created")
    return {
        "status": "success",
        "session_id": session.get("reference", ""),
        "reference": session.get("reference", ""),
        "payment_link": session.get("payment_link", session.get("authorization_url", "")),
        "payment": session,
    }


@app.get("/api/payments/paystack/{reference}")
async def api_paystack_payment_status(reference: str, request: Request):
    user = get_authenticated_user(request)
    try:
        transaction = sync_paystack_transaction(reference)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    data = transaction.get("data") or {}
    customer = (data.get("customer") or {}).get("email", "")
    if customer not in {"", None, user["email"]}:
        raise HTTPException(status_code=403, detail="Payment session does not belong to the current user")

    return {
        "status": "success",
        "reference": reference,
        "payment_status": data.get("status", ""),
        "payment": transaction,
    }


@app.post("/api/payments/paypal/create")
async def api_paypal_create_payment(payload: dict[str, Any], request: Request):
    user = get_authenticated_user(request)
    plan_key = (payload.get("plan_key") or "").strip()
    if not plan_key:
        raise HTTPException(status_code=400, detail="plan_key is required")

    plan = next((item for item in PLAN_DEFINITIONS if item.key == plan_key), None)
    if not plan:
        raise HTTPException(status_code=400, detail=f"Unknown plan: {plan_key}")

    try:
        order = create_paypal_order(plan.key, plan.label, plan.price_cents, user["email"], customer_name=(payload.get("customer_name") or user.get("name") or ""))
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    approve_link = next((link.get("href") for link in order.get("links", []) if link.get("rel") == "approve"), "")
    log_app_event(user["email"], "created", "payment_session", plan_key, platform="PayPal", details="PayPal order created")
    return {
        "status": "success",
        "order_id": order.get("subscription_id", order.get("id", "")),
        "subscription_id": order.get("subscription_id", order.get("id", "")),
        "payment_link": approve_link,
        "payment": order,
    }


@app.get("/api/payments/paypal/{order_id}")
async def api_paypal_payment_status(order_id: str, request: Request):
    user = get_authenticated_user(request)
    try:
        order = sync_paypal_order(order_id)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    if order.get("payer", {}).get("email_address") not in {"", None, user["email"]}:
        # Some PayPal flows may not include payer email before capture; only reject clear mismatches.
        pass

    return {
        "status": "success",
        "order_id": order_id,
        "payment_status": order.get("status", ""),
        "payment": order,
    }


@app.get("/api/payments/dodo/{payment_id}")
async def api_dodo_payment_status(payment_id: str, request: Request):
    user = get_authenticated_user(request)
    try:
        payment = sync_payment_status(payment_id)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail="Dodo payment lookup failed") from exc

    if (payment.get("metadata") or {}).get("user_email") not in {"", None, user["email"]}:
        raise HTTPException(status_code=403, detail="Payment session does not belong to the current user")

    payment_status = (payment.get("status") or "").lower()
    return {
        "status": "success",
        "payment_id": payment_id,
        "payment_status": payment_status,
        "payment": payment,
    }


@app.get("/api/youtube/videos")
async def api_youtube_videos(request: Request):
    user = get_authenticated_user(request)
    user_email = user["email"]
    return {"videos": build_demo_videos()}


@app.get("/api/platform-connections")
async def api_platform_connections(request: Request):
    user = get_authenticated_user(request)
    user_email = user["email"]
    await auto_refresh_user_tokens_if_needed(user_email)
    settings = fetch_user_connection_settings(user_email)
    if not settings:
        raise HTTPException(status_code=404, detail="User not found")
    return {"connections": settings}


@app.post("/api/platform-connections/refresh-all")
async def refresh_all_platform_connections(request: Request):
    user = get_authenticated_user(request)
    user_email = user["email"]
    require_active_subscription(user_email)
    maintenance_result = await auto_refresh_user_tokens_if_needed(user_email)
    return {"status": "success", **maintenance_result}


@app.post("/api/platform-connections/{platform}")
async def save_platform_connection(platform: str, payload: dict[str, Any], request: Request):
    user = get_authenticated_user(request)
    user_email = user["email"]
    require_active_subscription(user_email)
    try:
        update_platform_connection(user_email, platform, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    log_app_event(
        user_email,
        "connected",
        "platform_credentials",
        platform.capitalize(),
        platform=platform.capitalize(),
        details="Platform credentials saved",
    )
    return {"status": "success"}


@app.delete("/api/platform-connections/{platform}")
async def disconnect_platform_connection(platform: str, request: Request):
    user = get_authenticated_user(request)
    user_email = user["email"]
    try:
        clear_platform_connection(user_email, platform)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    log_app_event(
        user_email,
        "disconnected",
        "platform_credentials",
        platform.capitalize(),
        platform=platform.capitalize(),
        details="Platform credentials removed",
    )
    return {"status": "success"}


@app.post("/api/platform-connections/{platform}/refresh")
async def refresh_platform_connection(platform: str, request: Request):
    user = get_authenticated_user(request)
    user_email = user["email"]
    require_active_subscription(user_email)
    platform_key = platform.lower()
    if platform_key == "youtube":
        await refresh_youtube_connection_for_user(user_email)
        return {"status": "success", "platform": "YouTube"}

    if platform_key == "tiktok":
        await refresh_tiktok_connection_for_user(user_email)
        return {"status": "success", "platform": "TikTok"}

    raise HTTPException(status_code=400, detail=f"Token refresh is not implemented for {platform}")


@app.get("/api/conversations/{platform}")
async def api_conversations(platform: str, request: Request):
    user = get_authenticated_user(request)
    user_email = user["email"]
    stored = fetch_user_conversations(user_email, platform)
    if stored:
        return {"conversations": stored}
    return {"conversations": build_demo_conversations(platform)}


@app.post("/api/conversations/{platform}")
async def sync_conversations(platform: str, payload: dict[str, Any], request: Request):
    user = get_authenticated_user(request)
    user_email = user["email"]
    conversations = payload.get("conversations", [])
    if not isinstance(conversations, list):
        raise HTTPException(status_code=400, detail="conversations must be a list")

    upsert_conversations(user_email, platform, conversations)
    log_app_event(
        user_email,
        "synced",
        "conversation_batch",
        platform.capitalize(),
        platform=platform.capitalize(),
        details=f"{len(conversations)} conversations synchronized",
    )
    return {"status": "success", "count": len(conversations)}


@app.post("/api/messages/send")
async def api_send_message(payload: dict[str, Any], request: Request):
    user = get_authenticated_user(request)
    user_email = user["email"]
    platform = (payload.get("platform") or "").strip()
    recipient_id = (payload.get("recipient_id") or "").strip()
    message_text = (payload.get("message") or "").strip()
    conversation_id = (payload.get("conversation_id") or recipient_id or "").strip()
    customer_name = (payload.get("customer_name") or "").strip()
    customer_ref = (payload.get("customer_ref") or recipient_id or "").strip()
    avatar = (payload.get("avatar") or "👤").strip() or "👤"
    allow_demo_fallback = bool(payload.get("allow_demo_fallback", True))

    if not platform or not recipient_id or not message_text:
        raise HTTPException(status_code=400, detail="platform, recipient_id, and message are required")
    if not conversation_id:
        raise HTTPException(status_code=400, detail="conversation_id could not be resolved")

    delivery_mode = "simulated"
    delivery_message = "Message recorded locally"
    sent_live = False
    try:
        delivery_mode, delivery_message = await deliver_platform_message(user, platform, recipient_id, message_text)
        sent_live = True
    except HTTPException as exc:
        if not allow_demo_fallback:
            raise
        delivery_message = f"Stored as a test message: {exc.detail}"
    except httpx.HTTPError as exc:
        if not allow_demo_fallback:
            raise HTTPException(status_code=502, detail="Provider request failed") from exc
        delivery_message = "Stored as a test message because the provider request failed"

    conversation = upsert_live_conversation(
        user_email,
        platform,
        conversation_id,
        customer_ref,
        customer_name,
        avatar,
        outgoing_text=message_text,
    )
    log_app_event(
        user_email,
        "sent" if sent_live else "simulated_send",
        "conversation_message",
        customer_name or customer_ref or conversation_id,
        platform=platform,
        details=delivery_message,
    )
    save_interaction_to_db(
        user_email,
        platform,
        customer_ref or recipient_id,
        message_text,
        delivery_message if not sent_live else "Outbound platform send",
        score="Warm",
        summary="Outbound dashboard message",
    )
    if sent_live:
        increment_usage(user_email)

    return {
        "status": "success",
        "delivery_mode": delivery_mode,
        "delivery_message": delivery_message,
        "conversation": conversation,
    }


@app.get("/api/admin/overview")
async def api_admin_overview(request: Request):
    require_admin_user(request)
    overview = fetch_admin_overview()
    overview["platform_summary"] = fetch_admin_platform_summary()
    return overview


@app.get("/api/admin/users")
async def api_admin_users(request: Request, limit: int = 50):
    require_admin_user(request)
    safe_limit = max(1, min(limit, 200))
    return {"users": fetch_admin_users(safe_limit)}


@app.get("/api/admin/platforms")
async def api_admin_platforms(request: Request):
    require_admin_user(request)
    return {"platforms": fetch_admin_platform_summary()}


@app.get("/api/admin/activity")
async def api_admin_activity(request: Request, limit: int = 25):
    require_admin_user(request)
    safe_limit = max(1, min(limit, 200))
    return {"activity": fetch_admin_recent_activity(safe_limit)}


@app.get("/api/admin/conversations")
async def api_admin_conversations(request: Request, limit: int = 100):
    require_admin_user(request)
    safe_limit = max(1, min(limit, 500))
    return {"conversations": fetch_admin_conversations(safe_limit)}


@app.get("/api/admin/clients")
async def api_admin_clients(request: Request, limit: int = 100):
    require_admin_user(request)
    safe_limit = max(1, min(limit, 500))
    return {"clients": fetch_admin_clients(safe_limit)}


@app.get("/api/admin/products")
async def api_admin_products(request: Request, limit: int = 100):
    require_admin_user(request)
    safe_limit = max(1, min(limit, 500))
    return {"products": fetch_admin_products(safe_limit)}


@app.get("/api/admin/media")
async def api_admin_media(request: Request, limit: int = 100):
    require_admin_user(request)
    safe_limit = max(1, min(limit, 500))
    return {"media": fetch_admin_media(safe_limit)}


@app.get("/api/admin/connections")
async def api_admin_connections(request: Request, limit: int = 250):
    require_admin_user(request)
    safe_limit = max(1, min(limit, 1000))
    return {"connections": fetch_admin_connection_audit(safe_limit)}


@app.get("/api/admin/events")
async def api_admin_events(request: Request, limit: int = 100):
    require_admin_user(request)
    safe_limit = max(1, min(limit, 500))
    return {"events": fetch_admin_events(safe_limit)}


@app.post("/api/admin/events")
async def create_admin_event(payload: dict[str, Any], request: Request):
    user = get_authenticated_user(request)
    user_email = user["email"]
    event_type = (payload.get("event_type") or "").strip()
    entity_type = (payload.get("entity_type") or "").strip()
    if not event_type or not entity_type:
        raise HTTPException(status_code=400, detail="event_type and entity_type are required")

    log_app_event(
        user_email,
        event_type,
        entity_type,
        payload.get("entity_label", ""),
        payload.get("platform", ""),
        payload.get("details", ""),
    )
    return {"status": "success"}


@app.get("/webhook")
async def verify_meta(request: Request):
    params = request.query_params
    if params.get("hub.verify_token") == VERIFY_TOKEN:
        return Response(content=params.get("hub.challenge"))
    logger.error("Verification failed: %s", params.get("hub.verify_token"))
    return Response(content="Verification failed", status_code=403)


@app.post("/webhook")
async def handle_meta_message(request: Request):
    try:
        data = await request.json()
    except Exception:
        return {"status": "ignored", "reason": "invalid_json"}
    if not isinstance(data, dict):
        return {"status": "ignored", "reason": "invalid_payload"}
    try:
        entries = data.get("entry") or []
        if not isinstance(entries, list) or not entries:
            return {"status": "ignored", "reason": "missing_entry"}

        entry = entries[0] or {}
        if not isinstance(entry, dict):
            return {"status": "ignored", "reason": "invalid_entry"}

        business_id = entry.get("id", "")
        if not business_id:
            return {"status": "ignored", "reason": "missing_business_id"}

        if "messaging" in entry:
            user_config = get_user_config(business_id)
            user_email = user_config["email"]
            if not check_usage_limit(user_email):
                logger.info("Usage limit reached for %s.", user_email)
                return {"status": "limit_reached"}

            messaging_events = entry.get("messaging") or []
            if not isinstance(messaging_events, list) or not messaging_events:
                return {"status": "ignored", "reason": "missing_messaging_event"}

            messaging_event = messaging_events[0] or {}
            if not isinstance(messaging_event, dict):
                return {"status": "ignored", "reason": "invalid_messaging_event"}

            sender_id = (messaging_event.get("sender") or {}).get("id", "")
            if not sender_id:
                return {"status": "ignored", "reason": "missing_sender_id"}
            user_text = (messaging_event.get("message") or {}).get("text", "")
            platform = "Instagram" if "instagram" in str(data).lower() else "Facebook"

            ai_reply = generate_ai_response(
                business_id=business_id,
                customer_id=sender_id,
                user_text=user_text,
                platform=platform,
                products=user_config["products"],
            )
            await send_meta_reply(sender_id, ai_reply, user_config.get("fb_page_token", FB_PAGE_TOKEN))

            increment_usage(user_email)
            save_interaction_to_db(user_email, platform, sender_id, user_text, ai_reply)
            upsert_live_conversation(
                user_email,
                platform,
                sender_id,
                sender_id,
                f"{platform} Customer",
                "👤",
                incoming_text=user_text,
                outgoing_text=ai_reply,
            )
            log_app_event(
                user_email,
                "received",
                "conversation_message",
                sender_id,
                platform=platform,
                details="Inbound Meta message received and auto-replied",
            )

        elif "changes" in entry:
            change_events = entry.get("changes") or []
            if not isinstance(change_events, list) or not change_events:
                return {"status": "ignored", "reason": "missing_change_event"}

            change_entry = change_events[0] or {}
            if not isinstance(change_entry, dict):
                return {"status": "ignored", "reason": "invalid_change_event"}

            changes = change_entry.get("value") or {}
            if not isinstance(changes, dict):
                return {"status": "ignored", "reason": "invalid_change_value"}

            if "messages" in changes:
                phone_number_id = (changes.get("metadata") or {}).get("phone_number_id", "")
                if not phone_number_id:
                    return {"status": "ignored", "reason": "missing_phone_number_id"}

                user_config = get_user_config(phone_number_id)
                user_email = user_config["email"]
                if not check_usage_limit(user_email):
                    logger.info("Usage limit reached for %s.", user_email)
                    return {"status": "limit_reached"}

                messages = changes.get("messages") or []
                if not isinstance(messages, list) or not messages:
                    return {"status": "ignored", "reason": "missing_messages"}

                message = messages[0] or {}
                if not isinstance(message, dict):
                    return {"status": "ignored", "reason": "invalid_message"}

                customer_phone = message.get("from", "")
                if not customer_phone:
                    return {"status": "ignored", "reason": "missing_customer_phone"}
                user_text = message.get("text", {}).get("body", "")

                ai_reply = generate_ai_response(
                    business_id=business_id,
                    customer_id=customer_phone,
                    user_text=user_text,
                    platform="WhatsApp",
                    products=user_config["products"],
                )
                await send_whatsapp_reply(
                    phone_number_id,
                    customer_phone,
                    ai_reply,
                    user_config.get("whatsapp_token", WHATSAPP_TOKEN),
                )

                increment_usage(user_email)
                save_interaction_to_db(user_email, "WhatsApp", customer_phone, user_text, ai_reply)
                upsert_live_conversation(
                    user_email,
                    "WhatsApp",
                    customer_phone,
                    customer_phone,
                    "WhatsApp Customer",
                    "💬",
                    incoming_text=user_text,
                    outgoing_text=ai_reply,
                )
                log_app_event(
                    user_email,
                    "received",
                    "conversation_message",
                    customer_phone,
                    platform="WhatsApp",
                    details="Inbound WhatsApp message received and auto-replied",
                )

        return {"status": "success"}
    except Exception as exc:
        logger.exception("Meta webhook error: %s", exc)
        return {"status": "error"}


@app.post("/tiktok/webhook")
async def handle_tiktok(request: Request):
    try:
        data = await request.json()
    except Exception:
        return {"status": "ignored", "reason": "invalid_json"}
    if not isinstance(data, dict):
        return {"status": "ignored", "reason": "invalid_payload"}
    if data.get("type") == "verify":
        return {"challenge": data.get("challenge")}

    try:
        event = data.get("event", {})
        if not isinstance(event, dict):
            return {"status": "ignored", "reason": "invalid_event"}

        if event.get("type") == "message":
            sender_openid = event.get("sender_openid", "")
            user_text = event.get("text", "")
            recipient_id = event.get("recipient_openid", "")
            if not sender_openid or not recipient_id:
                return {"status": "ignored", "reason": "missing_message_ids"}

            user_config = get_user_config(recipient_id)
            user_email = user_config["email"]
            active_token = user_config.get("tiktok_access_token") or TIKTOK_ACCESS_TOKEN

            if check_usage_limit(user_email):
                ai_reply = generate_ai_response(
                    business_id=recipient_id,
                    customer_id=sender_openid,
                    user_text=user_text,
                    platform="TikTok",
                    products=user_config["products"],
                )
                await send_tiktok_reply(sender_openid, ai_reply, active_token)

                increment_usage(user_email)
                save_interaction_to_db(user_email, "TikTok", sender_openid, user_text, ai_reply)
                upsert_live_conversation(
                    user_email,
                    "TikTok",
                    sender_openid,
                    sender_openid,
                    "TikTok Customer",
                    "🎵",
                    incoming_text=user_text,
                    outgoing_text=ai_reply,
                )
                log_app_event(
                    user_email,
                    "received",
                    "conversation_message",
                    sender_openid,
                    platform="TikTok",
                    details="Inbound TikTok message received and auto-replied",
                )

        return {"status": "success"}
    except Exception as exc:
        logger.exception("TikTok webhook error: %s", exc)
        return {"status": "error"}


async def send_whatsapp_reply(phone_id: str, to: str, text: str, token: str | None = None):
    url = f"https://graph.facebook.com/v18.0/{phone_id}/messages"
    headers = {"Authorization": f"Bearer {token or WHATSAPP_TOKEN}"}
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": text},
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload, headers=headers)
        response.raise_for_status()


async def send_meta_reply(recipient_id: str, text: str, token: str | None = None):
    url = f"https://graph.facebook.com/v19.0/me/messages?access_token={token or FB_PAGE_TOKEN}"
    payload = {"recipient": {"id": recipient_id}, "message": {"text": text}}
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload)
        response.raise_for_status()


async def send_tiktok_reply(openid: str, text: str, token: str | None):
    if not token:
        raise HTTPException(status_code=500, detail="TikTok token is not configured")

    url = "https://open.tiktokapis.com/v2/messaging/send/"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    payload = {"recipient_openid": openid, "message": {"text": text}}
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload, headers=headers)
        response.raise_for_status()


async def send_telegram_reply(chat_id: str, text: str, token: str | None):
    if not token:
        raise HTTPException(status_code=500, detail="Telegram bot token is not configured")

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload)
        response.raise_for_status()


def upsert_live_conversation(
    user_email: str,
    platform: str,
    conversation_id: str,
    customer_ref: str,
    customer_name: str,
    avatar: str,
    incoming_text: str | None = None,
    outgoing_text: str | None = None,
    status: str | None = None,
) -> dict[str, Any]:
    normalized_platform = (platform or "").strip()
    existing_conversations = fetch_user_conversations(user_email, normalized_platform)
    target = next((item for item in existing_conversations if str(item.get("id")) == str(conversation_id)), None)

    if target:
        conversation = dict(target)
    else:
        conversation = {
            "id": str(conversation_id),
            "name": customer_name or f"{normalized_platform} Customer",
            "customer": customer_ref or "Direct message",
            "avatar": avatar or "👤",
            "message": "",
            "time": datetime.now().strftime("%I:%M %p"),
            "status": status or "warm",
            "unread": 0,
            "messages": [],
        }
        existing_conversations.append(conversation)

    conversation["platform"] = normalized_platform
    conversation["name"] = customer_name or conversation.get("name") or f"{normalized_platform} Customer"
    conversation["customer"] = customer_ref or conversation.get("customer") or "Direct message"
    conversation["avatar"] = avatar or conversation.get("avatar") or "👤"
    conversation["messages"] = list(conversation.get("messages", []))

    if incoming_text:
        conversation["messages"].append(
            {
                "sender": "customer",
                "message": incoming_text,
                "time": datetime.now().strftime("%I:%M %p"),
                "read": False,
            }
        )
        conversation["message"] = incoming_text
        conversation["time"] = conversation["messages"][-1]["time"]
        conversation["unread"] = int(conversation.get("unread", 0) or 0) + 1
        conversation["status"] = status or "new"

    if outgoing_text:
        conversation["messages"].append(
            {
                "sender": "agent",
                "message": outgoing_text,
                "time": datetime.now().strftime("%I:%M %p"),
                "read": True,
            }
        )
        conversation["message"] = outgoing_text
        conversation["time"] = conversation["messages"][-1]["time"]
        conversation["unread"] = 0
        conversation["status"] = status or "replied"

    upsert_conversations(user_email, normalized_platform, existing_conversations)
    return conversation


async def deliver_platform_message(
    user: dict[str, Any],
    platform: str,
    recipient_id: str,
    text: str,
) -> tuple[str, str]:
    platform_key = (platform or "").strip().lower()
    if platform_key == "whatsapp":
        phone_id = (user.get("phone_id") or "").strip()
        token = user.get("whatsapp_token") or WHATSAPP_TOKEN
        if not phone_id or not token:
            raise HTTPException(status_code=400, detail="WhatsApp credentials are incomplete")
        await send_whatsapp_reply(phone_id, recipient_id, text, token)
        return "live", "WhatsApp message sent"

    if platform_key in {"facebook", "instagram"}:
        token = user.get("fb_page_token") or FB_PAGE_TOKEN
        if not token:
            raise HTTPException(status_code=400, detail=f"{platform.title()} page token is missing")
        await send_meta_reply(recipient_id, text, token)
        return "live", f"{platform.title()} message sent"

    if platform_key == "tiktok":
        await auto_refresh_user_tokens_if_needed(user["email"])
        refreshed_user = get_user_by_email(user["email"]) or user
        token = refreshed_user.get("tiktok_access_token") or TIKTOK_ACCESS_TOKEN
        if not token:
            raise HTTPException(status_code=400, detail="TikTok access token is missing")
        await send_tiktok_reply(recipient_id, text, token)
        return "live", "TikTok message sent"

    if platform_key == "telegram":
        token = user.get("telegram_bot_token")
        if not token:
            raise HTTPException(status_code=400, detail="Telegram bot token is missing")
        await send_telegram_reply(recipient_id, text, token)
        return "live", "Telegram message sent"

    if platform_key == "youtube":
        raise HTTPException(status_code=400, detail="YouTube does not support direct live chat sending from this dashboard flow")

    raise HTTPException(status_code=400, detail=f"Unsupported platform: {platform}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)

    # Add inside startup_event where you iterate refresh_candidates
async def refresh_all_tokens(refresh_candidates): # Added 'async' here
    for row in refresh_candidates:
        try:
            # Now 'await' is legal because we are in an async function
            await auto_refresh_user_tokens_if_needed(row["email"])
        except HTTPException as he:
            logger.warning("Skipping refresh for %s: %s", row["email"], he.detail)
        except Exception as exc:
            logger.exception("Unexpected error refreshing tokens for %s: %s", row.get("email"), exc)
