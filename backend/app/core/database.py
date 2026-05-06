from __future__ import annotations

import base64
import hashlib
import hmac
import logging
import os
import secrets
from datetime import datetime, timedelta
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional

from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Integer,
    inspect,
    MetaData,
    String,
    Table,
    Text,
    UniqueConstraint,
    create_engine,
    select,
    text,
    insert,
    update,
)
from sqlalchemy.engine import Engine, Row
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql import func
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration / Engine
# ---------------------------------------------------------------------------

DB_FILENAME = "ai_business_memory.db"
FALLBACK_DB_FILENAME = "ai_business_memory_runtime.db"
DB_PATH = str(Path(__file__).resolve().parents[2] / DB_FILENAME)
_env_database_url = os.getenv("DATABASE_URL", "").strip()
if _env_database_url:
    DATABASE_URL = _env_database_url
else:
    # Local sqlite fallback using SQLAlchemy URI
    DATABASE_URL = f"sqlite:///{FALLBACK_DB_FILENAME}"

# Create engine with recommended options for both backends.
_engine_kwargs: Dict[str, Any] = {"future": True}
if DATABASE_URL.startswith("sqlite"):
    # Needed for SQLite + SQLAlchemy when used in threaded contexts (dev).
    _engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    # Use pool_pre_ping to keep connections healthy with Postgres/Neon.
    _engine_kwargs["pool_pre_ping"] = True

engine: Engine = create_engine(DATABASE_URL, **_engine_kwargs)

if not DATABASE_URL.startswith("sqlite"):
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as exc:
        logger.warning("Primary database unreachable, falling back to local SQLite: %s", exc)
        DATABASE_URL = f"sqlite:///{FALLBACK_DB_FILENAME}"
        _engine_kwargs = {"future": True, "connect_args": {"check_same_thread": False}}
        engine = create_engine(DATABASE_URL, **_engine_kwargs)

# Shared metadata
metadata = MetaData()

# ---------------------------------------------------------------------------
# Table definitions (SQLAlchemy Core)
# ---------------------------------------------------------------------------

users = Table(
    "users",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("email", String(255), unique=True, index=True),
    Column("password", Text),
    Column("subscription_status", String(64), server_default="inactive"),
    Column("trial_ends_at", DateTime),
    Column("message_count", Integer, server_default="0"),
    Column("message_limit", Integer, server_default="1000"),
    Column("phone_id", Text),
    Column("fb_page_id", Text),
    Column("tiktok_open_id", Text),
    Column("youtube_token", Text),
    Column("youtube_refresh_token", Text),
    Column("youtube_channel_id", Text),
    Column("tiktok_access_token", Text),
    Column("tiktok_refresh_token", Text),
    Column("tiktok_shop_id", Text),
    Column("fb_page_token", Text),
    Column("whatsapp_token", Text),
    Column("telegram_bot_token", Text),
    Column("ai_active_whatsapp", Integer, server_default="1"),
    Column("ai_active_messenger", Integer, server_default="1"),
    Column("ai_active_tiktok", Integer, server_default="1"),
    Column("ai_active_youtube", Integer, server_default="1"),
    Column("system_prompt", Text, server_default="You are a professional business assistant."),
    Column("name", Text, server_default=""),
    Column("role", Text, server_default="User"),
    Column("youtube_token_refreshed_at", Text, server_default=""),
    Column("tiktok_token_refreshed_at", Text, server_default=""),
    Column("created_at", DateTime, server_default=func.current_timestamp()),
)

leads = Table(
    "leads",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("phone_id", Text),
    Column("platform", Text, server_default="WhatsApp"),
    Column("customer_number", Text),
    Column("last_message", Text),
    Column("ai_reply", Text),
    Column("lead_score", Text, server_default="Warm"),
    Column("summary", Text, server_default="General Inquiry"),
    Column("timestamp", DateTime, server_default=func.current_timestamp()),
    Column("follow_up_count", Integer, server_default="0"),
    Column("last_interaction", DateTime, server_default=func.current_timestamp()),
    Column("is_active", Integer, server_default="1"),
)

products = Table(
    "products",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("user_email", Text),
    Column("name", Text),
    Column("price", Text),
    Column("description", Text),
    Column("category", Text),
    Column("tags", Text),
    Column("media_url", Text),
    Column("created_at", DateTime, server_default=func.current_timestamp()),
)

clients = Table(
    "clients",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("user_email", Text),
    Column("name", Text),
    Column("email", Text),
    Column("phone", Text),
    Column("company", Text),
    Column("platforms", Text),
    Column("score", Integer),
    Column("notes", Text),
    Column("created_at", DateTime, server_default=func.current_timestamp()),
)

media_assets = Table(
    "media_assets",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("user_email", Text),
    Column("platform", Text),
    Column("media_type", Text),
    Column("title", Text),
    Column("description", Text),
    Column("media_url", Text),
    Column("thumbnail", Text),
    Column("created_at", DateTime, server_default=func.current_timestamp()),
)

conversations = Table(
    "conversations",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("user_email", Text),
    Column("platform", Text),
    Column("external_id", Text),
    Column("customer_name", Text),
    Column("customer_ref", Text),
    Column("avatar", Text),
    Column("status", Text, server_default="warm"),
    Column("unread", Integer, server_default="0"),
    Column("last_message", Text),
    Column("last_message_time", Text),
    Column("updated_at", DateTime, server_default=func.current_timestamp()),
    UniqueConstraint("user_email", "platform", "external_id", name="uq_user_platform_external"),
)

conversation_messages = Table(
    "conversation_messages",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("conversation_id", Integer),
    Column("sender", Text),
    Column("message", Text),
    Column("sent_at", Text),
    Column("is_read", Integer, server_default="0"),
)

app_events = Table(
    "app_events",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("user_email", Text),
    Column("event_type", Text),
    Column("entity_type", Text),
    Column("entity_label", Text),
    Column("platform", Text),
    Column("details", Text),
    Column("created_at", DateTime, server_default=func.current_timestamp()),
)

billing_products = Table(
    "billing_products",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("plan_key", String(64), unique=True, index=True),
    Column("plan_label", Text),
    Column("dodo_product_id", Text),
    Column("paypal_product_id", Text),
    Column("paypal_plan_id", Text),
    Column("paypal_trial_days", Integer, server_default="0"),
    Column("paystack_plan_code", Text),
    Column("price_cents", Integer),
    Column("currency", String(8), server_default="USD"),
    Column("billing_cycle", String(16), server_default="monthly"),
    Column("product_kind", String(16), server_default="subscription"),
    Column("created_at", DateTime, server_default=func.current_timestamp()),
    Column("updated_at", DateTime, server_default=func.current_timestamp()),
)

payment_sessions = Table(
    "payment_sessions",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("session_id", Text, unique=True, index=True),
    Column("user_email", Text, index=True),
    Column("plan_key", String(64)),
    Column("plan_label", Text),
    Column("dodo_product_id", Text),
    Column("checkout_url", Text),
    Column("payment_status", Text),
    Column("currency", String(8), server_default="USD"),
    Column("price_cents", Integer),
    Column("created_at", DateTime, server_default=func.current_timestamp()),
    Column("updated_at", DateTime, server_default=func.current_timestamp()),
)

notifications = Table(
    "notifications",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("user_email", Text, unique=True, index=True),
    Column("email_notify", Integer, server_default="1"),
    Column("slack_webhook", Text),
    Column("discord_webhook", Text),
    Column("sms_number", Text),
    Column("notify_critical_only", Integer, server_default="1"),
    Column("created_at", DateTime, server_default=func.current_timestamp()),
)

# Token fields and refresh mapping kept for compatibility
TOKEN_FIELDS = {
    "youtube_token",
    "youtube_refresh_token",
    "tiktok_access_token",
    "tiktok_refresh_token",
    "fb_page_token",
    "whatsapp_token",
    "telegram_bot_token",
}
REFRESH_TIMESTAMP_FIELDS = {
    "youtube_token": "youtube_token_refreshed_at",
    "tiktok_access_token": "tiktok_token_refreshed_at",
}

# ---------------------------------------------------------------------------
# Encryption / password helpers (kept from original logic)
# ---------------------------------------------------------------------------


@lru_cache(maxsize=1)
def get_encryption_key() -> bytes:
    raw_key = os.getenv("TOKEN_ENCRYPTION_KEY", "").strip()
    if raw_key:
        try:
            Fernet(raw_key.encode("utf-8"))
            return raw_key.encode("utf-8")
        except ValueError:
            logger.warning("TOKEN_ENCRYPTION_KEY is invalid; deriving token encryption key from AUTH_SECRET.")

    fallback_secret = os.getenv("AUTH_SECRET", "social-ai-agent-dev-secret").encode("utf-8")
    derived = hashlib.sha256(fallback_secret).digest()
    return base64.urlsafe_b64encode(derived)


def get_cipher() -> Fernet:
    return Fernet(get_encryption_key())


def encrypt_sensitive_value(value: Optional[str]) -> str:
    normalized = (value or "").strip()
    if not normalized:
        return ""
    if normalized.startswith("enc:"):
        return normalized
    token = get_cipher().encrypt(normalized.encode("utf-8")).decode("utf-8")
    return f"enc:{token}"


def decrypt_sensitive_value(value: Optional[str]) -> str:
    normalized = (value or "").strip()
    if not normalized:
        return ""
    if not normalized.startswith("enc:"):
        return normalized
    encrypted_token = normalized.split("enc:", 1)[1]
    try:
        return get_cipher().decrypt(encrypted_token.encode("utf-8")).decode("utf-8")
    except InvalidToken:
        return ""


def decrypt_user_secret_fields(record: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not record:
        return record
    hydrated = dict(record)
    for field in TOKEN_FIELDS:
        if field in hydrated:
            hydrated[field] = decrypt_sensitive_value(hydrated.get(field))
    return hydrated


def current_timestamp_iso() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat()


def hash_password(password: str, salt: Optional[str] = None) -> str:
    salt = salt or secrets.token_hex(16)
    derived = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 120000)
    return f"{salt}${derived.hex()}"


def verify_password(password: str, stored_value: Optional[str]) -> bool:
    if not stored_value:
        return False
    if "$" not in stored_value:
        return hmac.compare_digest(stored_value, password)
    salt, expected_hash = stored_value.split("$", 1)
    candidate_hash = hash_password(password, salt).split("$", 1)[1]
    return hmac.compare_digest(candidate_hash, expected_hash)


# ---------------------------------------------------------------------------
# Low-level helpers for executing queries and mapping rows to dicts
# ---------------------------------------------------------------------------


def _row_to_dict(row: Row) -> Dict[str, Any]:
    # Row may be a RowMapping; convert to plain dict
    try:
        return dict(row._mapping)  # type: ignore[attr-defined]
    except Exception:
        # fallback
        return dict(row)


def execute_fetchall(stmt, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    with engine.connect() as conn:
        result = conn.execute(stmt, params or {})
        return [_row_to_dict(r) for r in result.mappings().all()]


def execute_fetchone(stmt, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    with engine.connect() as conn:
        result = conn.execute(stmt, params or {})
        row = result.mappings().first()
        return _row_to_dict(row) if row is not None else None


def execute_commit(stmt, params: Optional[Dict[str, Any]] = None) -> None:
    with engine.begin() as conn:
        conn.execute(stmt, params or {})


# ---------------------------------------------------------------------------
# Public API: Schema management and data helpers (keeps original function names)
# ---------------------------------------------------------------------------


def init_db() -> None:
    """
    Create all tables defined in metadata. This is safe to run against both
    SQLite (dev) and Postgres (Neon) and will create missing tables/columns.
    """
    metadata.create_all(engine)
    _ensure_user_columns()
    _ensure_billing_product_columns()


def _ensure_user_columns() -> None:
    inspector = inspect(engine)
    if "users" not in inspector.get_table_names():
        return

    required_columns = {
        "trial_ends_at": DateTime,
    }

    with engine.begin() as conn:
        existing_columns = {
            column["name"]
            for column in inspector.get_columns("users")
        }
        for column_name, column_type in required_columns.items():
            if column_name in existing_columns:
                continue
            try:
                ddl_type = column_type().compile(dialect=engine.dialect)
                conn.execute(text(f'ALTER TABLE users ADD COLUMN "{column_name}" {ddl_type}'))
            except Exception:
                logger.warning("User schema migration skipped for column %s", column_name)


def _ensure_billing_product_columns() -> None:
    inspector = inspect(engine)
    if "billing_products" not in inspector.get_table_names():
        return

    required_columns = {
        "paypal_product_id": Text,
        "paypal_plan_id": Text,
        "paypal_trial_days": Integer,
        "paystack_plan_code": Text,
    }

    with engine.begin() as conn:
        existing_columns = {
            column["name"]
            for column in inspector.get_columns("billing_products")
        }
        for column_name, column_type in required_columns.items():
            if column_name in existing_columns:
                continue
            try:
                ddl_type = column_type().compile(dialect=engine.dialect)
                conn.execute(text(f'ALTER TABLE billing_products ADD COLUMN "{column_name}" {ddl_type}'))
            except Exception:
                # Another process may have raced us or the backend may be using a
                # database that does not support this exact ALTER syntax.
                logger.warning("Billing schema migration skipped for column %s", column_name)


def ensure_default_admin() -> None:
    """Seed a default admin user for local/demo testing if one does not exist."""
    existing = execute_fetchone(select(users.c.id).where(users.c.email == "saintvellian@gmail.com"))
    if existing:
        # Update fields if missing
        stmt = (
            update(users)
            .where(users.c.email == "saintvellian@gmail.com")
            .values(
                name=func.coalesce(func.nullif(users.c.name, ""), "Saint Vellian"),
                role=func.coalesce(func.nullif(users.c.role, ""), "Admin"),
            )
        )
        # password update only if empty: do a separate read/check
        user = get_user_by_email("saintvellian@gmail.com")
        if user and (not user.get("password")):
            stmt = stmt.values(password=hash_password("password123"))
        execute_commit(stmt)
        return

    execute_commit(
        insert(users).values(
            email="saintvellian@gmail.com",
            password=hash_password("password123"),
            name="Saint Vellian",
            role="Admin",
            subscription_status="inactive",
            message_count=0,
            message_limit=1000,
        )
    )


def fetch_admin_overview() -> Dict[str, int]:
    with engine.connect() as conn:
        stats: Dict[str, int] = {}
        stats["users"] = conn.execute(select(func.count()).select_from(users)).scalar_one()
        stats["active_subscriptions"] = conn.execute(
            select(func.count()).select_from(users).where(func.lower(users.c.subscription_status) == "active")
        ).scalar_one()
        stats["leads"] = conn.execute(select(func.count()).select_from(leads)).scalar_one()
        stats["products"] = conn.execute(select(func.count()).select_from(products)).scalar_one()
        stats["clients"] = conn.execute(select(func.count()).select_from(clients)).scalar_one()
        stats["media_assets"] = conn.execute(select(func.count()).select_from(media_assets)).scalar_one()
        stats["conversations"] = conn.execute(select(func.count()).select_from(conversations)).scalar_one()
        stats["unread_messages"] = conn.execute(select(func.coalesce(func.sum(conversations.c.unread), 0))).scalar_one()
        stats["events"] = conn.execute(select(func.count()).select_from(app_events)).scalar_one()
        stats["ai_replies"] = conn.execute(
            select(func.count()).select_from(leads).where(leads.c.ai_reply.isnot(None)).where(func.trim(leads.c.ai_reply) != "")
        ).scalar_one()
        stats["messages_used"] = conn.execute(select(func.coalesce(func.sum(users.c.message_count), 0))).scalar_one()
        stats["message_capacity"] = conn.execute(select(func.coalesce(func.sum(users.c.message_limit), 0))).scalar_one()
        return stats


def fetch_admin_users(limit: int = 50) -> List[Dict[str, Any]]:
    stmt = select(
        users.c.id,
        users.c.email,
        users.c.subscription_status,
        users.c.message_count,
        users.c.message_limit,
        users.c.phone_id,
        users.c.fb_page_id,
        users.c.tiktok_open_id,
        users.c.created_at,
    ).order_by(users.c.created_at.desc(), users.c.id.desc()).limit(limit)
    return execute_fetchall(stmt)


def fetch_admin_connection_audit(limit: int = 250) -> List[Dict[str, Any]]:
    stmt = select(
        users.c.email,
        users.c.name,
        users.c.role,
        users.c.phone_id,
        users.c.fb_page_id,
        users.c.tiktok_open_id,
        users.c.youtube_channel_id,
        users.c.youtube_refresh_token,
        users.c.youtube_token_refreshed_at,
        users.c.tiktok_refresh_token,
        users.c.tiktok_token_refreshed_at,
        users.c.whatsapp_token,
        users.c.fb_page_token,
        users.c.telegram_bot_token,
        users.c.created_at,
    ).order_by(users.c.created_at.desc(), users.c.id.desc()).limit(limit)
    rows = execute_fetchall(stmt)
    audits: List[Dict[str, Any]] = []
    for row in rows:
        user = decrypt_user_secret_fields(row)
        created_at = user.get("created_at", "")
        owner_name = user.get("name", "") or user.get("email", "").split("@")[0]
        role = user.get("role", "User")
        # Build connection rows (same structure as original)
        connection_rows = [
            {
                "owner_email": user.get("email", ""),
                "owner_name": owner_name,
                "role": role,
                "platform": "WhatsApp",
                "connected": bool((user.get("phone_id") or "").strip() and (user.get("whatsapp_token") or "").strip()),
                "account_ref": user.get("phone_id", ""),
                "auto_refresh_ready": False,
                "last_refreshed_at": "",
                "health": "Connected" if (user.get("phone_id") or "").strip() and (user.get("whatsapp_token") or "").strip() else "Missing credentials",
                "created_at": created_at,
            },
            {
                "owner_email": user.get("email", ""),
                "owner_name": owner_name,
                "role": role,
                "platform": "Facebook",
                "connected": bool((user.get("fb_page_id") or "").strip() and (user.get("fb_page_token") or "").strip()),
                "account_ref": user.get("fb_page_id", ""),
                "auto_refresh_ready": False,
                "last_refreshed_at": "",
                "health": "Connected" if (user.get("fb_page_id") or "").strip() and (user.get("fb_page_token") or "").strip() else "Missing credentials",
                "created_at": created_at,
            },
            {
                "owner_email": user.get("email", ""),
                "owner_name": owner_name,
                "role": role,
                "platform": "Instagram",
                "connected": bool((user.get("fb_page_id") or "").strip() and (user.get("fb_page_token") or "").strip()),
                "account_ref": user.get("fb_page_id", ""),
                "auto_refresh_ready": False,
                "last_refreshed_at": "",
                "health": "Connected" if (user.get("fb_page_id") or "").strip() and (user.get("fb_page_token") or "").strip() else "Missing credentials",
                "created_at": created_at,
            },
            {
                "owner_email": user.get("email", ""),
                "owner_name": owner_name,
                "role": role,
                "platform": "Telegram",
                "connected": bool((user.get("telegram_bot_token") or "").strip()),
                "account_ref": "Bot token saved" if (user.get("telegram_bot_token") or "").strip() else "",
                "auto_refresh_ready": False,
                "last_refreshed_at": "",
                "health": "Connected" if (user.get("telegram_bot_token") or "").strip() else "Missing credentials",
                "created_at": created_at,
            },
            {
                "owner_email": user.get("email", ""),
                "owner_name": owner_name,
                "role": role,
                "platform": "YouTube",
                "connected": bool((user.get("youtube_channel_id") or "").strip() and (user.get("youtube_token") or "").strip()),
                "account_ref": user.get("youtube_channel_id", ""),
                "auto_refresh_ready": bool((user.get("youtube_refresh_token") or "").strip()),
                "last_refreshed_at": user.get("youtube_token_refreshed_at", ""),
                "health": (
                    "Auto-refresh ready"
                    if (user.get("youtube_channel_id") or "").strip()
                    and (user.get("youtube_token") or "").strip()
                    and (user.get("youtube_refresh_token") or "").strip()
                    else "Manual reconnect risk"
                    if (user.get("youtube_channel_id") or "").strip() and (user.get("youtube_token") or "").strip()
                    else "Missing credentials"
                ),
                "created_at": created_at,
            },
            {
                "owner_email": user.get("email", ""),
                "owner_name": owner_name,
                "role": role,
                "platform": "TikTok",
                "connected": bool((user.get("tiktok_open_id") or "").strip() and (user.get("tiktok_access_token") or "").strip()),
                "account_ref": user.get("tiktok_open_id", ""),
                "auto_refresh_ready": bool((user.get("tiktok_refresh_token") or "").strip()),
                "last_refreshed_at": user.get("tiktok_token_refreshed_at", ""),
                "health": (
                    "Auto-refresh ready"
                    if (user.get("tiktok_open_id") or "").strip()
                    and (user.get("tiktok_access_token") or "").strip()
                    and (user.get("tiktok_refresh_token") or "").strip()
                    else "Manual reconnect risk"
                    if (user.get("tiktok_open_id") or "").strip() and (user.get("tiktok_access_token") or "").strip()
                    else "Missing credentials"
                ),
                "created_at": created_at,
            },
        ]
        audits.extend(connection_rows)
    return audits


def fetch_admin_platform_summary() -> List[Dict[str, Any]]:
    stmt = select(leads.c.platform, func.count().label("interactions")).group_by(leads.c.platform).order_by(text("interactions DESC, platform ASC"))
    return execute_fetchall(stmt)


def fetch_admin_recent_activity(limit: int = 25) -> List[Dict[str, Any]]:
    stmt = (
        select(
            leads.c.phone_id.label("user_email"),
            leads.c.platform,
            leads.c.customer_number,
            leads.c.last_message,
            leads.c.ai_reply,
            leads.c.lead_score,
            leads.c.summary,
            leads.c.timestamp,
        )
        .order_by(leads.c.timestamp.desc(), leads.c.id.desc())
        .limit(limit)
    )
    return execute_fetchall(stmt)


def fetch_admin_conversations(limit: int = 100) -> List[Dict[str, Any]]:
    stmt = (
        select(
            conversations.c.user_email,
            conversations.c.platform,
            conversations.c.external_id,
            conversations.c.customer_name,
            conversations.c.customer_ref,
            conversations.c.status,
            conversations.c.unread,
            conversations.c.last_message,
            conversations.c.last_message_time,
            conversations.c.updated_at,
        )
        .order_by(conversations.c.updated_at.desc(), conversations.c.id.desc())
        .limit(limit)
    )
    return execute_fetchall(stmt)


def fetch_admin_clients(limit: int = 100) -> List[Dict[str, Any]]:
    stmt = select(clients.c.user_email, clients.c.name, clients.c.email, clients.c.phone, clients.c.company, clients.c.platforms, clients.c.score, clients.c.notes, clients.c.created_at).order_by(clients.c.created_at.desc(), clients.c.id.desc()).limit(limit)
    return execute_fetchall(stmt)


def fetch_admin_products(limit: int = 100) -> List[Dict[str, Any]]:
    stmt = select(products.c.user_email, products.c.name, products.c.price, products.c.category, products.c.tags, products.c.created_at).order_by(products.c.created_at.desc(), products.c.id.desc()).limit(limit)
    return execute_fetchall(stmt)


def fetch_admin_media(limit: int = 100) -> List[Dict[str, Any]]:
    stmt = select(media_assets.c.user_email, media_assets.c.platform, media_assets.c.media_type, media_assets.c.title, media_assets.c.media_url, media_assets.c.created_at).order_by(media_assets.c.created_at.desc(), media_assets.c.id.desc()).limit(limit)
    return execute_fetchall(stmt)


def fetch_admin_events(limit: int = 100) -> List[Dict[str, Any]]:
    stmt = select(app_events.c.user_email, app_events.c.event_type, app_events.c.entity_type, app_events.c.entity_label, app_events.c.platform, app_events.c.details, app_events.c.created_at).order_by(app_events.c.created_at.desc(), app_events.c.id.desc()).limit(limit)
    return execute_fetchall(stmt)


def fetch_user_connection_settings(email: str) -> Optional[Dict[str, Any]]:
    stmt = select(
        users.c.email,
        users.c.phone_id,
        users.c.fb_page_id,
        users.c.tiktok_open_id,
        users.c.youtube_token,
        users.c.youtube_refresh_token,
        users.c.youtube_channel_id,
        users.c.tiktok_access_token,
        users.c.tiktok_refresh_token,
        users.c.tiktok_shop_id,
        users.c.fb_page_token,
        users.c.whatsapp_token,
        users.c.telegram_bot_token,
        users.c.youtube_token_refreshed_at,
        users.c.tiktok_token_refreshed_at,
    ).where(users.c.email == email)
    row = execute_fetchone(stmt)
    return decrypt_user_secret_fields(row) if row else None


def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    normalized = (email or "").strip().lower()
    stmt = select(users).where(func.lower(users.c.email) == normalized)
    row = execute_fetchone(stmt)
    return decrypt_user_secret_fields(row) if row else None


def create_user_account(email: str, password: str, name: str = "", role: str = "User") -> Optional[Dict[str, Any]]:
    normalized_email = (email or "").strip().lower()
    if not normalized_email or not password:
        raise ValueError("email and password are required")
    if get_user_by_email(normalized_email):
        raise ValueError("An account with this email already exists")
    stmt = insert(users).values(
        email=normalized_email,
        password=hash_password(password),
        name=(name or normalized_email.split("@")[0]).strip(),
        role=role,
        subscription_status="trial",
        trial_ends_at=datetime.utcnow() + timedelta(days=1),
    )
    try:
        execute_commit(stmt)
    except IntegrityError as ex:
        raise ValueError("An account with this email already exists") from ex
    return get_user_by_email(normalized_email)


def authenticate_user(email: str, password: str) -> Optional[Dict[str, Any]]:
    user = get_user_by_email((email or "").strip().lower())
    if not user or not verify_password(password, user.get("password")):
        return None
    # If stored password was plaintext (no $), upgrade it
    if user.get("password") and "$" not in user.get("password", ""):
        update_user_password(user["email"], password)
        user = get_user_by_email(user["email"])
    return user


def update_user_password(email: str, new_password: str) -> Optional[Dict[str, Any]]:
    normalized_email = (email or "").strip().lower()
    stmt = update(users).where(func.lower(users.c.email) == normalized_email).values(password=hash_password(new_password))
    execute_commit(stmt)
    return get_user_by_email(normalized_email)


def update_platform_connection(email: str, platform: str, payload: Dict[str, Any]) -> None:
    platform_key = (platform or "").strip().lower()
    field_map = {
        "whatsapp": ["phone_id", "whatsapp_token"],
        "facebook": ["fb_page_id", "fb_page_token"],
        "instagram": ["fb_page_id", "fb_page_token"],
        "tiktok": ["tiktok_open_id", "tiktok_access_token", "tiktok_refresh_token", "tiktok_shop_id"],
        "youtube": ["youtube_token", "youtube_refresh_token", "youtube_channel_id"],
        "telegram": ["telegram_bot_token"],
    }
    fields = field_map.get(platform_key)
    if not fields:
        raise ValueError(f"Unsupported platform: {platform}")
    values: Dict[str, Any] = {}
    for field in fields:
        field_value = (payload.get(field) or "").strip()
        values[field] = encrypt_sensitive_value(field_value) if field in TOKEN_FIELDS else field_value
        refresh_field = REFRESH_TIMESTAMP_FIELDS.get(field)
        if refresh_field and field_value:
            values[refresh_field] = current_timestamp_iso()
    stmt = update(users).where(users.c.email == email).values(**values)
    execute_commit(stmt)


def clear_platform_connection(email: str, platform: str) -> None:
    platform_key = (platform or "").strip().lower()
    field_map = {
        "whatsapp": ["phone_id", "whatsapp_token"],
        "facebook": ["fb_page_id", "fb_page_token"],
        "instagram": ["fb_page_id", "fb_page_token"],
        "tiktok": ["tiktok_open_id", "tiktok_access_token", "tiktok_refresh_token", "tiktok_shop_id"],
        "youtube": ["youtube_token", "youtube_refresh_token", "youtube_channel_id"],
        "telegram": ["telegram_bot_token"],
    }
    fields = field_map.get(platform_key)
    if not fields:
        raise ValueError(f"Unsupported platform: {platform}")
    values = {field: "" for field in fields}
    # add refresh timestamp fields if any
    for field in fields:
        if field in REFRESH_TIMESTAMP_FIELDS:
            values[REFRESH_TIMESTAMP_FIELDS[field]] = ""
    stmt = update(users).where(users.c.email == email).values(**values)
    execute_commit(stmt)


def fetch_user_conversations(user_email: str, platform: str) -> List[Dict[str, Any]]:
    stmt = select(conversations).where(conversations.c.user_email == user_email).where(func.lower(conversations.c.platform) == platform.lower()).order_by(conversations.c.updated_at.desc(), conversations.c.id.desc())
    conv_rows = execute_fetchall(stmt)
    results: List[Dict[str, Any]] = []
    for conv in conv_rows:
        conv_id = conv["id"]
        msg_stmt = select(conversation_messages.c.sender, conversation_messages.c.message, conversation_messages.c.sent_at, conversation_messages.c.is_read).where(conversation_messages.c.conversation_id == conv_id).order_by(conversation_messages.c.id.asc())
        message_rows = execute_fetchall(msg_stmt)
        results.append(
            {
                "id": conv.get("external_id"),
                "name": conv.get("customer_name") or f"{platform.capitalize()} Customer",
                "customer": conv.get("customer_ref") or "Direct message",
                "avatar": conv.get("avatar") or "👤",
                "message": conv.get("last_message") or "",
                "time": conv.get("last_message_time") or "",
                "status": conv.get("status") or "warm",
                "unread": int(conv.get("unread", 0) or 0),
                "messages": [
                    {
                        "sender": msg.get("sender"),
                        "message": msg.get("message"),
                        "time": msg.get("sent_at"),
                        "read": bool(msg.get("is_read")),
                    }
                    for msg in message_rows
                ],
            }
        )
    return results


def upsert_conversations(user_email: str, platform: str, conversations_list: List[Dict[str, Any]]) -> None:
    platform_name = (platform or "").strip()
    platform_key = platform_name.lower()
    with engine.begin() as conn:
        for conversation in conversations_list:
            external_id = str(conversation.get("id") or "")
            if not external_id:
                continue
            # Try insert, if conflict update (SQLite and Postgres handled by SQLAlchemy upsert emulation is complex).
            # For portability, do a simple existence check then insert or update.
            existing = conn.execute(
                select(conversations.c.id)
                .where(conversations.c.user_email == user_email)
                .where(func.lower(conversations.c.platform) == platform_key)
                .where(conversations.c.external_id == external_id)
            ).mappings().first()
            if existing:
                conv_id = existing["id"]
                conn.execute(
                    update(conversations)
                    .where(conversations.c.id == conv_id)
                    .values(
                        customer_name=conversation.get("name", ""),
                        customer_ref=conversation.get("customer", ""),
                        avatar=conversation.get("avatar", "👤"),
                        status=conversation.get("status", "warm"),
                        unread=int(conversation.get("unread", 0) or 0),
                        last_message=conversation.get("message", ""),
                        last_message_time=conversation.get("time", ""),
                        updated_at=func.current_timestamp(),
                    )
                )
            else:
                res = conn.execute(
                    insert(conversations).values(
                        user_email=user_email,
                        platform=platform_name,
                        external_id=external_id,
                        customer_name=conversation.get("name", ""),
                        customer_ref=conversation.get("customer", ""),
                        avatar=conversation.get("avatar", "👤"),
                        status=conversation.get("status", "warm"),
                        unread=int(conversation.get("unread", 0) or 0),
                        last_message=conversation.get("message", ""),
                        last_message_time=conversation.get("time", ""),
                    )
                )
                conv_id = res.inserted_primary_key[0] if res.inserted_primary_key else None

            # Delete old messages and re-insert
            if conv_id is not None:
                conn.execute(conversation_messages.delete().where(conversation_messages.c.conversation_id == conv_id))
                for message in conversation.get("messages", []):
                    conn.execute(
                        insert(conversation_messages).values(
                            conversation_id=conv_id,
                            sender=message.get("sender", "customer"),
                            message=message.get("message") or message.get("text") or "",
                            sent_at=message.get("time", ""),
                            is_read=1 if message.get("read", False) else 0,
                        )
                    )


def log_app_event(user_email: str, event_type: str, entity_type: str, entity_label: str = "", platform: str = "", details: str = "") -> None:
    stmt = insert(app_events).values(user_email=user_email, event_type=event_type, entity_type=entity_type, entity_label=entity_label, platform=platform, details=details)
    execute_commit(stmt)


# --- SAAS USAGE & QUOTA HELPERS ---


def check_usage_limit(email: str) -> bool:
    row = execute_fetchone(select(users.c.message_count, users.c.message_limit).where(users.c.email == email))
    if row:
        return int(row["message_count"] or 0) < int(row["message_limit"] or 0)
    return False


def increment_usage(email: str) -> None:
    stmt = update(users).where(users.c.email == email).values(message_count=users.c.message_count + 1)
    execute_commit(stmt)


# --- INTERACTION & INTEL STORAGE ---


def save_interaction_to_db(email: str, platform: str, customer: str, msg: str, reply: str, score: str = "Warm", summary: str = "...") -> None:
    stmt = insert(leads).values(phone_id=email, platform=platform, customer_number=customer, last_message=msg, ai_reply=reply, lead_score=score, summary=summary)
    execute_commit(stmt)


def get_billing_product(plan_key: str) -> Optional[Dict[str, Any]]:
    stmt = select(billing_products).where(billing_products.c.plan_key == plan_key)
    row = execute_fetchone(stmt)
    return row


def upsert_billing_product(
    plan_key: str,
    plan_label: str,
    dodo_product_id: str,
    price_cents: int,
    paypal_product_id: str = "",
    paypal_plan_id: str = "",
    paystack_plan_code: str = "",
    paypal_trial_days: Optional[int] = None,
    currency: str = "USD",
    billing_cycle: str = "monthly",
    product_kind: str = "subscription",
) -> None:
    existing = get_billing_product(plan_key)
    values = {
        "plan_key": plan_key,
        "plan_label": plan_label,
        "dodo_product_id": dodo_product_id,
        "paypal_product_id": paypal_product_id,
        "paypal_plan_id": paypal_plan_id,
        "paystack_plan_code": paystack_plan_code,
        "price_cents": price_cents,
        "currency": currency,
        "billing_cycle": billing_cycle,
        "product_kind": product_kind,
        "updated_at": func.current_timestamp(),
    }
    if paypal_trial_days is not None:
        values["paypal_trial_days"] = paypal_trial_days
    if existing:
        stmt = update(billing_products).where(billing_products.c.plan_key == plan_key).values(**values)
    else:
        stmt = insert(billing_products).values(**values)
    execute_commit(stmt)


def upsert_payment_session(
    session_id: str,
    user_email: str,
    plan_key: str,
    plan_label: str,
    dodo_product_id: str,
    checkout_url: str,
    payment_status: str,
    price_cents: int,
    currency: str = "USD",
) -> None:
    existing = execute_fetchone(select(payment_sessions.c.id).where(payment_sessions.c.session_id == session_id))
    values = {
        "session_id": session_id,
        "user_email": user_email,
        "plan_key": plan_key,
        "plan_label": plan_label,
        "dodo_product_id": dodo_product_id,
        "checkout_url": checkout_url,
        "payment_status": payment_status,
        "currency": currency,
        "price_cents": price_cents,
        "updated_at": func.current_timestamp(),
    }
    if existing:
        stmt = update(payment_sessions).where(payment_sessions.c.session_id == session_id).values(**values)
    else:
        stmt = insert(payment_sessions).values(**values)
    execute_commit(stmt)


def get_payment_session(session_id: str) -> Optional[Dict[str, Any]]:
    stmt = select(payment_sessions).where(payment_sessions.c.session_id == session_id)
    return execute_fetchone(stmt)


def update_payment_session_status(session_id: str, payment_status: str) -> None:
    stmt = update(payment_sessions).where(payment_sessions.c.session_id == session_id).values(
        payment_status=payment_status,
        updated_at=func.current_timestamp(),
    )
    execute_commit(stmt)


def activate_user_subscription(email: str, plan_label: str = "") -> None:
    stmt = update(users).where(users.c.email == email).values(subscription_status="active")
    execute_commit(stmt)


# --- USER CONFIGURATION RETRIEVAL (for webhooks) ---


def get_user_by_platform_id(platform_id: str) -> Optional[Dict[str, Any]]:
    stmt = select(users).where((users.c.phone_id == platform_id) | (users.c.fb_page_id == platform_id) | (users.c.tiktok_open_id == platform_id))
    row = execute_fetchone(stmt)
    return decrypt_user_secret_fields(row) if row else None


def get_user_products(user_email: str) -> List[Dict[str, Any]]:
    stmt = select(products.c.name, products.c.price, products.c.description, products.c.category, products.c.tags, products.c.media_url).where(products.c.user_email == user_email)
    return execute_fetchall(stmt)


def get_client_by_platform_id(platform_id: str) -> Optional[Dict[str, Any]]:
    # Interaction rows store the account owner email in `phone_id`, so this
    # lookup should only match the actual customer/platform identifier.
    stmt = select(leads).where(leads.c.customer_number == platform_id).order_by(leads.c.timestamp.desc()).limit(1)
    row = execute_fetchone(stmt)
    return row


# --- LEGACY HELPERS (for backward compatibility) ---


def get_business_config(biz_id: str) -> Optional[Dict[str, Any]]:
    return get_user_by_platform_id(biz_id)


def get_business_products(email: str) -> List[Dict[str, Any]]:
    return get_user_products(email)


def save_lead_interaction(email: str, platform: str, customer: str, msg: str, reply: str, score: str = "Warm", summary: str = "...") -> None:
    save_interaction_to_db(email, platform, customer, msg, reply, score, summary)


# --- PLATFORM TOKEN UPDATES ---


def update_tiktok_tokens(email: str, access_token: str, refresh_token: Optional[str] = None) -> None:
    values = {"tiktok_access_token": encrypt_sensitive_value(access_token)}
    if refresh_token:
        values["tiktok_refresh_token"] = encrypt_sensitive_value(refresh_token)
    stmt = update(users).where(users.c.email == email).values(**values)
    execute_commit(stmt)


def update_youtube_tokens(email: str, access_token: str, refresh_token: Optional[str] = None, channel_id: Optional[str] = None) -> None:
    values: Dict[str, Any] = {"youtube_token": encrypt_sensitive_value(access_token)}
    if refresh_token is not None:
        values["youtube_refresh_token"] = encrypt_sensitive_value(refresh_token)
    if channel_id is not None:
        values["youtube_channel_id"] = channel_id
    stmt = update(users).where(users.c.email == email).values(**values)
    execute_commit(stmt)


# --- MAIN EXECUTION / DEVELOPMENT HELPER ---


if __name__ == "__main__":
    # Development helper: reset DB when run directly (mimic prior behavior)
    if DATABASE_URL.startswith("sqlite") and os.path.exists(DB_FILENAME):
        os.remove(DB_FILENAME)
        print("Schema updated. Database reset.")

    init_db()
    # Seed admin
    with engine.begin() as conn:
        existing_admin = conn.execute(select(users.c.id).where(users.c.email == "saintvellian@gmail.com")).mappings().first()
        if not existing_admin:
            conn.execute(
                insert(users).values(
                    email="saintvellian@gmail.com",
                    password=hash_password("password123"),
                    name="Saint Vellian",
                    role="Admin",
                    phone_id="admin_001",
                    fb_page_id="fb_page_123",
                    tiktok_open_id="tiktok_open_123",
                    tiktok_shop_id="SHOP_12345",
                    whatsapp_token=encrypt_sensitive_value(os.getenv("WHATSAPP_TOKEN", "demo_whatsapp_token")),
                    fb_page_token=encrypt_sensitive_value(os.getenv("FB_PAGE_ACCESS_TOKEN", "demo_fb_token")),
                    subscription_status="active",
                )
            )
    print("🚀 Database Initialized with SQLAlchemy and full platform support.")
