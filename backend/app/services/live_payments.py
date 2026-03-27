from __future__ import annotations

import os
import uuid
from typing import Any, Optional

import requests

from database import activate_user_subscription, engine, get_billing_product, payment_sessions, upsert_billing_product, upsert_payment_session

PAYSTACK_SECRET_KEY = os.getenv("PAYSTACK_SECRET_KEY", "").strip()
PAYSTACK_PUBLIC_KEY = os.getenv("PAYSTACK_PUBLIC_KEY", "").strip()
PAYSTACK_ENV = "live" if PAYSTACK_SECRET_KEY.startswith("sk_live_") else "test"
PAYSTACK_BASE_URL = "https://api.paystack.co"
BACKEND_PUBLIC_URL = os.getenv("BACKEND_PUBLIC_URL", "").strip()
_DEFAULT_FRONTEND_URL = os.getenv("FRONTEND_APP_URL", "http://localhost:8501").strip()


def _public_return_url(path: str, fallback: str) -> str:
    if BACKEND_PUBLIC_URL:
        return f"{BACKEND_PUBLIC_URL.rstrip('/')}{path}"
    return fallback


def _response_json(response: requests.Response) -> dict[str, Any]:
    try:
        payload = response.json()
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


PAYSTACK_CALLBACK_URL = _public_return_url(
    "/payments/return",
    os.getenv("PAYSTACK_CALLBACK_URL", _DEFAULT_FRONTEND_URL).strip(),
)
PAYSTACK_CURRENCY = os.getenv("PAYSTACK_CURRENCY", "USD").strip().upper() or "USD"

PAYPAL_CLIENT_ID = os.getenv("PAYPAL_CLIENT_ID", "").strip()
PAYPAL_CLIENT_SECRET = os.getenv("PAYPAL_CLIENT_SECRET", "").strip()
PAYPAL_ENV = os.getenv("PAYPAL_ENV", "live").strip().lower()
PAYPAL_BASE_URL = "https://api-m.sandbox.paypal.com" if PAYPAL_ENV == "sandbox" else "https://api-m.paypal.com"
PAYPAL_RETURN_URL = _public_return_url(
    "/payments/paypal/return",
    os.getenv("PAYPAL_RETURN_URL", _DEFAULT_FRONTEND_URL).strip(),
)
PAYPAL_CANCEL_URL = _public_return_url(
    "/payments/paypal/cancel",
    os.getenv("PAYPAL_CANCEL_URL", _DEFAULT_FRONTEND_URL).strip(),
)
DODO_RETURN_URL = _public_return_url(
    "/payments/dodo/return",
    os.getenv("DODO_RETURN_URL", _DEFAULT_FRONTEND_URL).strip(),
)


def paystack_enabled() -> bool:
    return bool(PAYSTACK_SECRET_KEY)


def paypal_enabled() -> bool:
    return bool(PAYPAL_CLIENT_ID and PAYPAL_CLIENT_SECRET)


def _raise_if_non_live_paystack() -> None:
    if not PAYSTACK_SECRET_KEY.startswith("sk_live_") and not PAYSTACK_SECRET_KEY.startswith("sk_test_"):
        raise RuntimeError("Paystack is not configured with a valid secret key.")


def _raise_if_non_live_paypal() -> None:
    if PAYPAL_ENV != "live":
        raise RuntimeError("PayPal is configured for sandbox. Set PAYPAL_ENV=live to accept real payments.")


def _paystack_request(method: str, path: str, data: Optional[dict[str, Any]] = None) -> dict[str, Any]:
    if not paystack_enabled():
        raise RuntimeError("Paystack is not configured")
    _raise_if_non_live_paystack()

    try:
        response = requests.request(
            method,
            f"{PAYSTACK_BASE_URL}{path}",
            headers={"Authorization": f"Bearer {PAYSTACK_SECRET_KEY}", "Content-Type": "application/json"},
            json=data,
            timeout=30,
        )
    except requests.RequestException as exc:
        raise RuntimeError(f"Paystack network request failed: {exc}") from exc
    if response.ok:
        return _response_json(response)

    try:
        payload = response.json()
        message = payload.get("message") or payload.get("error") or response.text
    except Exception:
        message = response.text
    raise RuntimeError(f"Paystack API error ({response.status_code}): {message}")


def _paystack_get_or_create_plan(plan_key: str, plan_label: str, price_cents: int) -> str:
    stored = get_billing_product(plan_key) or {}
    plan_code = stored.get("paystack_plan_code", "")
    if plan_code:
        return plan_code

    payload = {
        "name": plan_label,
        "interval": "monthly",
        "amount": price_cents,
        "description": f"Monthly subscription for {plan_label}",
    }
    response = _paystack_request("POST", "/plan", data=payload)
    plan_code = (response.get("data") or {}).get("plan_code", "")
    if plan_code:
        upsert_billing_product(
            plan_key=plan_key,
            plan_label=plan_label,
            dodo_product_id=stored.get("dodo_product_id", ""),
            price_cents=price_cents,
            paypal_product_id=stored.get("paypal_product_id", ""),
            paypal_plan_id=stored.get("paypal_plan_id", ""),
            paystack_plan_code=plan_code,
            currency=PAYSTACK_CURRENCY,
            billing_cycle="monthly",
            product_kind="subscription",
        )
    return plan_code


def create_paystack_checkout(plan_key: str, plan_label: str, price_cents: int, user_email: str, customer_name: str = "") -> dict[str, Any]:
    plan_code = _paystack_get_or_create_plan(plan_key, plan_label, price_cents)
    if not plan_code:
        raise RuntimeError(f"Unable to create a Paystack plan for {plan_label}")

    reference = f"paystack_{uuid.uuid4().hex}"
    response = _paystack_request(
        "POST",
        "/transaction/initialize",
        data={
            "email": user_email,
            "amount": price_cents,
            "plan": plan_code,
            "reference": reference,
            "callback_url": PAYSTACK_CALLBACK_URL,
            "metadata": {
                "plan_key": plan_key,
                "plan_label": plan_label,
                "user_email": user_email,
                "customer_name": customer_name or user_email.split("@")[0],
            },
        },
    )
    session = response.get("data") or {}
    checkout_url = session.get("authorization_url", "")
    if reference:
        upsert_payment_session(
            session_id=reference,
            user_email=user_email,
            plan_key=plan_key,
            plan_label=plan_label,
            dodo_product_id="",
            checkout_url=checkout_url,
            payment_status=session.get("status", "pending"),
            price_cents=price_cents,
            currency=PAYSTACK_CURRENCY,
        )
    return {
        "reference": reference,
        "authorization_url": checkout_url,
        "payment_link": checkout_url,
        "data": session,
    }


def get_paystack_transaction(reference: str) -> dict[str, Any]:
    return _paystack_request("GET", f"/transaction/verify/{reference}")


def sync_paystack_transaction(reference: str) -> dict[str, Any]:
    transaction = get_paystack_transaction(reference)
    stored = None
    with engine.connect() as conn:
        stored = conn.execute(
            payment_sessions.select().where(payment_sessions.c.session_id == reference)
        ).mappings().first()
    data = transaction.get("data") or {}
    status = (data.get("status") or "").lower()
    if stored:
        upsert_payment_session(
            session_id=reference,
            user_email=stored["user_email"],
            plan_key=stored["plan_key"],
            plan_label=stored["plan_label"],
            dodo_product_id="",
            checkout_url=data.get("authorization_url", stored.get("checkout_url", "")),
            payment_status=status or stored.get("payment_status", ""),
            price_cents=int(stored.get("price_cents") or 0),
            currency=stored.get("currency", PAYSTACK_CURRENCY),
        )
        if status == "success":
            activate_user_subscription(stored["user_email"], stored["plan_label"])
    return transaction


def _paypal_request(method: str, path: str, *, access_token: str, json: Optional[dict[str, Any]] = None, data: Optional[dict[str, Any]] = None) -> dict[str, Any]:
    _raise_if_non_live_paypal()
    try:
        response = requests.request(
            method,
            f"{PAYPAL_BASE_URL}{path}",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
                "PayPal-Request-Id": uuid.uuid4().hex,
            },
            json=json,
            data=data,
            timeout=30,
        )
    except requests.RequestException as exc:
        raise RuntimeError(f"PayPal network request failed: {exc}") from exc
    if response.ok:
        return _response_json(response)

    try:
        payload = response.json()
        message = payload.get("message") or payload.get("name") or response.text
    except Exception:
        message = response.text
    raise RuntimeError(f"PayPal API error ({response.status_code}): {message}")


def _paypal_access_token() -> str:
    if not paypal_enabled():
        raise RuntimeError("PayPal is not configured")
    _raise_if_non_live_paypal()
    try:
        response = requests.post(
            f"{PAYPAL_BASE_URL}/v1/oauth2/token",
            auth=(PAYPAL_CLIENT_ID, PAYPAL_CLIENT_SECRET),
            data={"grant_type": "client_credentials"},
            headers={"Accept": "application/json", "Accept-Language": "en_US"},
            timeout=30,
        )
    except requests.RequestException as exc:
        raise RuntimeError(f"PayPal auth request failed: {exc}") from exc
    if response.ok:
        return _response_json(response).get("access_token", "")
    raise RuntimeError(f"PayPal auth failed ({response.status_code}): {response.text}")


def _paypal_get_or_create_product(plan_key: str, plan_label: str, price_cents: int) -> str:
    stored = get_billing_product(plan_key) or {}
    product_id = stored.get("paypal_product_id", "")
    if product_id:
        return product_id

    access_token = _paypal_access_token()
    response = _paypal_request(
        "POST",
        "/v1/catalogs/products",
        access_token=access_token,
        json={
            "name": plan_label,
            "description": f"Monthly subscription for {plan_label}",
            "type": "SERVICE",
            "category": "SOFTWARE",
            "home_url": PAYPAL_RETURN_URL,
        },
    )
    product_id = response.get("id", "")
    if product_id:
        upsert_billing_product(
            plan_key=plan_key,
            plan_label=plan_label,
            dodo_product_id=stored.get("dodo_product_id", ""),
            price_cents=price_cents,
            paypal_product_id=product_id,
            paypal_plan_id=stored.get("paypal_plan_id", ""),
            currency="USD",
            billing_cycle="monthly",
            product_kind="subscription",
        )
    return product_id


def _paypal_get_or_create_plan(plan_key: str, plan_label: str, price_cents: int, product_id: str) -> str:
    stored = get_billing_product(plan_key) or {}
    plan_id = stored.get("paypal_plan_id", "")
    if plan_id:
        return plan_id

    access_token = _paypal_access_token()
    response = _paypal_request(
        "POST",
        "/v1/billing/plans",
        access_token=access_token,
        json={
            "product_id": product_id,
            "name": plan_label,
            "description": f"Monthly subscription for {plan_label}",
            "status": "ACTIVE",
            "billing_cycles": [
                {
                    "frequency": {"interval_unit": "MONTH", "interval_count": 1},
                    "tenure_type": "REGULAR",
                    "sequence": 1,
                    "total_cycles": 0,
                    "pricing_scheme": {
                        "fixed_price": {
                            "value": f"{price_cents / 100:.2f}",
                            "currency_code": "USD",
                        }
                    },
                }
            ],
            "payment_preferences": {
                "auto_bill_outstanding": True,
                "setup_fee_failure_action": "CONTINUE",
                "payment_failure_threshold": 3,
            },
        },
    )
    plan_id = response.get("id", "")
    if plan_id:
        upsert_billing_product(
            plan_key=plan_key,
            plan_label=plan_label,
            dodo_product_id=stored.get("dodo_product_id", ""),
            price_cents=price_cents,
            paypal_product_id=product_id,
            paypal_plan_id=plan_id,
            currency="USD",
            billing_cycle="monthly",
            product_kind="subscription",
        )
    return plan_id


def _split_customer_name(customer_name: str, fallback: str) -> dict[str, str]:
    raw_name = (customer_name or fallback).strip() or fallback
    parts = [part for part in raw_name.split(" ") if part]
    if not parts:
        parts = [fallback]
    first_name = parts[0]
    last_name = parts[-1] if len(parts) > 1 else parts[0]
    return {"given_name": first_name, "surname": last_name}


def create_paypal_order(plan_key: str, plan_label: str, price_cents: int, user_email: str, customer_name: str = "") -> dict[str, Any]:
    access_token = _paypal_access_token()
    product_id = _paypal_get_or_create_product(plan_key, plan_label, price_cents)
    if not product_id:
        raise RuntimeError(f"Unable to create a PayPal product for {plan_label}")

    plan_id = _paypal_get_or_create_plan(plan_key, plan_label, price_cents, product_id)
    if not plan_id:
        raise RuntimeError(f"Unable to create a PayPal billing plan for {plan_label}")

    subscription = _paypal_request(
        "POST",
        "/v1/billing/subscriptions",
        access_token=access_token,
        json={
            "plan_id": plan_id,
            "subscriber": {
                "email_address": user_email,
                "name": _split_customer_name(customer_name, user_email.split("@")[0]),
            },
            "application_context": {
                "brand_name": "Social Ai Agent",
                "return_url": PAYPAL_RETURN_URL,
                "cancel_url": PAYPAL_CANCEL_URL,
                "shipping_preference": "NO_SHIPPING",
                "user_action": "SUBSCRIBE_NOW",
            },
        },
    )
    subscription_id = subscription.get("id", "")
    approve_url = next((link.get("href") for link in subscription.get("links", []) if link.get("rel") in {"approve", "payer-action"}), "")
    if subscription_id:
        upsert_payment_session(
            session_id=subscription_id,
            user_email=user_email,
            plan_key=plan_key,
            plan_label=plan_label,
            dodo_product_id="",
            checkout_url=approve_url,
            payment_status=subscription.get("status", "APPROVAL_PENDING"),
            price_cents=price_cents,
            currency="USD",
        )
    return {
        **subscription,
        "payment_link": approve_url,
        "subscription_id": subscription_id,
    }


def capture_paypal_order(order_id: str) -> dict[str, Any]:
    access_token = _paypal_access_token()
    return _paypal_request("GET", f"/v1/billing/subscriptions/{order_id}", access_token=access_token)


def sync_paypal_order(order_id: str) -> dict[str, Any]:
    access_token = _paypal_access_token()
    order = _paypal_request("GET", f"/v1/billing/subscriptions/{order_id}", access_token=access_token)
    stored = None
    with engine.connect() as conn:
        stored = conn.execute(
            payment_sessions.select().where(payment_sessions.c.session_id == order_id)
        ).mappings().first()
    if stored:
        current_status = (order.get("status") or "").upper()
        upsert_payment_session(
            session_id=order_id,
            user_email=stored["user_email"],
            plan_key=stored["plan_key"],
            plan_label=stored["plan_label"],
            dodo_product_id="",
            checkout_url=stored.get("checkout_url", ""),
            payment_status=current_status,
            price_cents=int(stored.get("price_cents") or 0),
            currency=stored.get("currency", "USD"),
        )
        if current_status in {"ACTIVE", "APPROVED"}:
            activate_user_subscription(stored["user_email"], stored["plan_label"])
    return order
