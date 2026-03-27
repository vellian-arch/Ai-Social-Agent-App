from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Optional

import requests

from database import activate_user_subscription, get_billing_product, get_payment_session, upsert_billing_product, upsert_payment_session

DODO_API_KEY = os.getenv("DODO_PAYMENTS_API_KEY", "").strip()
DODO_ENV = os.getenv("DODO_ENV", "live_mode").strip().lower()
DODO_BASE_URL = "https://test.dodopayments.com" if DODO_ENV == "test_mode" else "https://live.dodopayments.com"
DODO_CURRENCY = os.getenv("DODO_CURRENCY", "USD").strip().upper() or "USD"
DODO_RETURN_URL = os.getenv("DODO_RETURN_URL", "").strip()


def _safe_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _response_json(response: requests.Response) -> dict[str, Any]:
    try:
        payload = response.json()
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


@dataclass(frozen=True)
class BillingPlan:
    key: str
    label: str
    price_cents: int
    description: str


PLAN_DEFINITIONS = [
    BillingPlan("plan_1", "1 Platform", 3000, "Access for a single connected platform."),
    BillingPlan("plan_2", "2 Platforms", 5000, "Access for two connected platforms."),
    BillingPlan("plan_3", "3 Platforms", 8000, "Access for three connected platforms."),
    BillingPlan("plan_4", "4 Platforms", 10000, "Access for four connected platforms."),
    BillingPlan("plan_5", "5 Platforms", 12000, "Access for five connected platforms."),
    BillingPlan("plan_6", "All 6 Platforms", 13000, "Access for all supported platforms."),
]


def dodo_enabled() -> bool:
    return bool(DODO_API_KEY)


def _request(method: str, path: str, *, json: Optional[dict[str, Any]] = None, params: Optional[dict[str, Any]] = None) -> dict[str, Any]:
    if not dodo_enabled():
        raise RuntimeError("Dodo Payments is not configured")

    try:
        response = requests.request(
            method,
            f"{DODO_BASE_URL}{path}",
            headers={
                "Authorization": f"Bearer {DODO_API_KEY}",
                "Content-Type": "application/json",
            },
            json=json,
            params=params,
            timeout=30,
        )
    except requests.RequestException as exc:
        raise RuntimeError(f"Dodo network request failed: {exc}") from exc
    if response.ok:
        return _response_json(response)

    try:
        error_payload = _response_json(response)
        error_code = str(error_payload.get("code", "")).upper()
        error_message = error_payload.get("message") or response.text
    except Exception:
        error_code = ""
        error_message = response.text

    if error_code == "MERCHANT_NOT_LIVE":
        raise RuntimeError("Dodo live payments are not enabled for this merchant yet. Switch DODO_ENV to test_mode or enable live mode in Dodo.")

    raise RuntimeError(f"Dodo API error ({response.status_code}): {error_message}")


def list_products() -> list[dict[str, Any]]:
    payload = _request("GET", "/products", params={"page_size": 100, "recurring": True})
    return payload.get("items", [])


def create_product(plan: BillingPlan) -> dict[str, Any]:
    payload = {
        "name": plan.label,
        "description": plan.description,
        "recurring": True,
        "billing_cycle": "monthly",
        "price": {
            "currency": DODO_CURRENCY,
            "discount": 0,
            "price": plan.price_cents,
            "purchasing_power_parity": True,
            "payment_frequency_count": 1,
            "payment_frequency_interval": "Month",
            "subscription_period_count": 1,
            "subscription_period_interval": "Month",
            "tax_inclusive": False,
            "trial_period_days": 0,
            "type": "recurring_price",
        },
        "license_key_enabled": False,
        "tax_category": "saas",
        "metadata": {"plan_key": plan.key, "source": "ai-social-agent"},
    }
    return _request("POST", "/products", json=payload)


def ensure_products() -> list[dict[str, Any]]:
    if not dodo_enabled():
        return []

    local_records = []
    missing_plans = []
    for plan in PLAN_DEFINITIONS:
        stored = get_billing_product(plan.key)
        if stored and stored.get("dodo_product_id") and stored.get("product_kind", "subscription") == "subscription" and stored.get("billing_cycle", "monthly") == "monthly":
            local_records.append(
                {
                    "plan_key": plan.key,
                    "plan_label": plan.label,
                    "price_cents": plan.price_cents,
                    "dodo_product_id": stored.get("dodo_product_id", ""),
                    "paypal_product_id": stored.get("paypal_product_id", ""),
                    "paypal_plan_id": stored.get("paypal_plan_id", ""),
                }
            )
        else:
            missing_plans.append(plan)

    if not missing_plans:
        return local_records

    created_or_found: list[dict[str, Any]] = []
    existing_products = []
    try:
        existing_products = list_products()
    except Exception:
        existing_products = []

    for plan in missing_plans:
        stored = get_billing_product(plan.key)
        product_id = (stored or {}).get("dodo_product_id", "")
        product = None

        if product_id:
            product = next((item for item in existing_products if item.get("product_id") == product_id), None)

        if product is None:
            product = next(
                (
                    item
                    for item in existing_products
                    if item.get("name") == plan.label
                    and _safe_int(item.get("price"), default=-1) == plan.price_cents
                ),
                None,
            )

        if product is None:
            product = create_product(plan)
            product_id = product.get("product_id") or product.get("brand_id") or ""
        else:
            product_id = product.get("product_id") or product.get("brand_id") or product_id

        if product_id:
            upsert_billing_product(
                plan_key=plan.key,
                plan_label=plan.label,
                dodo_product_id=product_id,
                price_cents=plan.price_cents,
                paypal_product_id=(stored or {}).get("paypal_product_id", ""),
                paypal_plan_id=(stored or {}).get("paypal_plan_id", ""),
                currency=DODO_CURRENCY,
                billing_cycle="monthly",
                product_kind="subscription",
            )

        created_or_found.append(
            {
                "plan_key": plan.key,
                "plan_label": plan.label,
                "price_cents": plan.price_cents,
                "dodo_product_id": product_id,
            }
        )

    return local_records + created_or_found


def _billing_payload(user_email: str) -> dict[str, Any]:
    return {
        "country": "US",
        "city": "New York",
        "state": "NY",
        "street": "N/A",
        "zipcode": "00000",
    }


def create_payment_for_plan(plan_key: str, user_email: str, customer_name: str = "", return_url: str = "") -> dict[str, Any]:
    if not dodo_enabled():
        raise RuntimeError("Dodo Payments is not configured")

    plan = next((item for item in PLAN_DEFINITIONS if item.key == plan_key), None)
    if not plan:
        raise ValueError(f"Unknown plan: {plan_key}")

    stored = get_billing_product(plan_key)
    product_id = (stored or {}).get("dodo_product_id", "")
    if not product_id:
        ensure_products()
        stored = get_billing_product(plan_key)
        product_id = (stored or {}).get("dodo_product_id", "")
    if not product_id:
        raise RuntimeError(f"No Dodo product is configured for {plan.label}")

    payload = {
        "customer_id": user_email,
        "product_id": product_id,
        "payment_link": True,
        "return_url": return_url or DODO_RETURN_URL or "",
        "show_saved_payment_methods": True,
        "metadata": {
            "plan_key": plan.key,
            "plan_label": plan.label,
            "user_email": user_email,
            "source": "ai-social-agent",
        },
    }

    payment = _request("POST", "/subscriptions", json=payload)
    subscription_id = payment.get("subscription_id") or payment.get("id") or payment.get("session_id", "")
    payment_id = payment.get("payment_id", "")
    payment_link = payment.get("payment_link", "") or payment.get("checkout_url", "")
    session_key = subscription_id or payment_id

    if session_key:
        upsert_payment_session(
            session_id=session_key,
            user_email=user_email,
            plan_key=plan.key,
            plan_label=plan.label,
            dodo_product_id=product_id,
            checkout_url=payment_link,
            payment_status=payment.get("status", "requires_payment_method"),
            price_cents=plan.price_cents,
            currency=DODO_CURRENCY,
        )

    return payment


def get_payment(payment_id: str) -> dict[str, Any]:
    if not dodo_enabled():
        raise RuntimeError("Dodo Payments is not configured")
    return _request("GET", f"/subscriptions/{payment_id}")


def sync_payment_status(payment_id: str) -> dict[str, Any]:
    payment = get_payment(payment_id)
    status = (payment.get("status") or "").lower()
    session = get_payment_session(payment_id)
    if session:
        upsert_payment_session(
            session_id=payment_id,
            user_email=session["user_email"],
            plan_key=session["plan_key"],
            plan_label=session["plan_label"],
            dodo_product_id=session["dodo_product_id"],
            checkout_url=session.get("checkout_url", payment.get("payment_link", "")),
            payment_status=status or session.get("payment_status", ""),
            price_cents=int(session.get("price_cents") or 0),
            currency=session.get("currency", DODO_CURRENCY),
        )
        if status in {"active", "approved"}:
            activate_user_subscription(session["user_email"], session["plan_label"])
    return payment
