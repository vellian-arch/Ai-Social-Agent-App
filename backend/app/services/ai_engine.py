from __future__ import annotations

import json
import logging
import os
import re
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from typing import Any, Iterable

from dotenv import load_dotenv

from database import get_business_config, get_user_products, save_interaction_to_db
from notifications import send_lead_alert

load_dotenv()

logger = logging.getLogger(__name__)
_EXECUTOR = ThreadPoolExecutor(max_workers=2)

try:
    from google import genai  # type: ignore
    from google.genai import types  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    genai = None  # type: ignore[assignment]
    types = None  # type: ignore[assignment]


def extract_order_id(text: str) -> str | None:
    """Detect a likely order ID in incoming text."""
    match = re.search(r"\b\d{10,20}\b", text or "")
    return match.group(0) if match else None


def ai_is_configured() -> bool:
    return bool(os.getenv("GEMINI_API_KEY", "").strip() and genai is not None)


def _product_lines(products: Iterable[dict[str, Any]]) -> str:
    lines: list[str] = []
    for product in products:
        name = product.get("name", "Product")
        price = product.get("price", "")
        description = (product.get("description") or "")[:120]
        tags = product.get("tags", "")
        lines.append(f"- {name} (${price}): {description} Tags: {tags}")
    return "\n".join(lines) if lines else "No products in inventory yet."


def _fallback_reply(
    user_text: str,
    platform: str,
    products: list[dict[str, Any]] | None,
    system_prompt: str,
) -> tuple[str, str, str, str | None]:
    message = (user_text or "").lower()
    catalog = products or []
    top_product = catalog[0].get("name") if catalog else None
    order_id = extract_order_id(user_text)

    if any(word in message for word in ("price", "cost", "how much", "pricing")):
        reply = "Thanks for asking. I can share pricing, package options, and the best fit for your needs right away."
        score = "Hot"
        summary = "Pricing question"
        suggested_product = top_product
    elif any(word in message for word in ("demo", "video", "show", "walkthrough")):
        reply = f"Absolutely. I can share a quick demo and a short walkthrough for {top_product or 'the product'}."
        score = "Warm"
        summary = "Demo request"
        suggested_product = top_product
    elif any(word in message for word in ("available", "stock", "availability")):
        reply = f"Yes, {top_product or 'the item'} is available and I can confirm the latest details for you."
        score = "Hot"
        summary = "Availability check"
        suggested_product = top_product
    elif order_id:
        reply = f"Thanks. I found order reference {order_id} and I’m checking the status for you now."
        score = "Hot"
        summary = "Order lookup"
        suggested_product = None
    else:
        reply = (
            f"Thanks for reaching out on {platform}. "
            f"{top_product or 'Our team'} is ready to help with pricing, product details, and next steps."
        )
        score = "Warm"
        summary = "General inquiry"
        suggested_product = top_product

    if system_prompt.strip():
        reply = reply.strip()

    return reply, score, summary, suggested_product


def _parse_model_response(raw_text: str, order_id: str | None) -> tuple[str, str, str, str | None, str | None]:
    try:
        cleaned = (raw_text or "").replace("```json", "").replace("```", "").strip()
        data = json.loads(cleaned)
        reply = data.get("reply", "How can I help you?")
        score = data.get("score", "Warm")
        summary = data.get("summary", "Inquiry received")
        suggested_product = data.get("suggested_product")
        detected_order_id = data.get("detected_order_id") or order_id
        return reply, score, summary, detected_order_id, suggested_product
    except Exception:
        return "", "Warm", "Direct inquiry", order_id, None


def _send_hot_lead_alert(
    platform: str,
    customer_id: str,
    user_text: str,
    summary: str,
    lead_score: str,
    user_email: str,
    detected_order: str | None,
    suggested_product: str | None,
) -> None:
    try:
        alert_text = f"🔥 HOT LEAD/ORDER: {summary}"
        if detected_order:
            alert_text += f" (Order ID: {detected_order})"
        if suggested_product:
            alert_text += f" Suggested: {suggested_product}"
        send_lead_alert(platform, customer_id, user_text, alert_text, lead_score, user_email)
    except Exception as alert_err:  # pragma: no cover - notification should not break replies
        logger.warning("Lead alert failed: %s", alert_err)


def _generate_gemini_text(full_prompt: str, model_name: str, system_prompt: str) -> str:
    if genai is None:
        raise RuntimeError("Gemini client is unavailable")
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY", "").strip())
    config = types.GenerateContentConfig(
        system_instruction=system_prompt,
        response_mime_type="application/json",
    )
    response = client.models.generate_content(
        model=model_name,
        contents=full_prompt,
        config=config,
    )
    return getattr(response, "text", "") or ""


def _generate_follow_up_gemini_text(prompt: str, model_name: str, system_prompt: str) -> str:
    if genai is None:
        raise RuntimeError("Gemini client is unavailable")
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY", "").strip())
    config = types.GenerateContentConfig(system_instruction=system_prompt)
    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
        config=config,
    )
    return getattr(response, "text", "") or ""


def generate_ai_response(
    business_id,
    customer_id,
    user_text,
    platform="Social Media",
    products=None,
):
    """
    Generate an AI response using Gemini when configured.
    Falls back to a deterministic local assistant so replies always work.
    """
    biz_config = get_business_config(business_id) or {}
    user_email = biz_config.get("email", "admin@test.com")
    system_prompt = biz_config.get("system_prompt", "You are a professional business assistant.")

    if products is None:
        products = get_user_products(user_email)
    products = products or []

    order_id = extract_order_id(user_text)
    fallback_reply, fallback_score, fallback_summary, fallback_product = _fallback_reply(
        user_text,
        platform,
        products,
        system_prompt,
    )

    ai_reply = fallback_reply
    lead_score = fallback_score
    summary = fallback_summary
    detected_order = order_id
    suggested_product = fallback_product

    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    model_name = os.getenv("GEMINI_MODEL", "gemini-1.5-flash").strip() or "gemini-1.5-flash"
    timeout_seconds = float(os.getenv("GEMINI_TIMEOUT_SECONDS", "12") or "12")
    if api_key and genai is not None:
        try:
            product_list_str = _product_lines(products)
            shop_context = ""
            if order_id:
                shop_context = (
                    f"\nCRITICAL: The user provided Order ID: {order_id}. "
                    "Acknowledge that you are looking up this order status."
                )

            full_prompt = f"""
Role: {system_prompt}
Platform: {platform}

Your business's product catalog:
{product_list_str}

{shop_context}

Customer Message: "{user_text}"

You must return a JSON object with exactly these keys:
1. "reply": A helpful, concise response. If there are products, try to suggest relevant ones based on the customer's message. Be friendly and professional.
2. "score": Evaluate as "Hot" (wants to buy/order issue), "Warm" (asking questions), or "Cold" (spam).
3. "summary": A 5-10 word summary of intent.
4. "detected_order_id": The Order ID found, or null.
5. "suggested_product": If you recommended a specific product from the catalog, include its name; otherwise null.

Return ONLY raw JSON.
"""
            future = _EXECUTOR.submit(_generate_gemini_text, full_prompt, model_name, system_prompt)
            try:
                raw_text = future.result(timeout=timeout_seconds)
            except FuturesTimeoutError:
                logger.warning("Gemini reply timed out after %ss, using fallback assistant.", timeout_seconds)
                raw_text = ""
            response_text = raw_text
            parsed_reply, parsed_score, parsed_summary, parsed_detected, parsed_product = _parse_model_response(
                response_text,
                order_id,
            )
            if parsed_reply:
                ai_reply = parsed_reply
            lead_score = parsed_score or fallback_score
            summary = parsed_summary or fallback_summary
            detected_order = parsed_detected or order_id
            suggested_product = parsed_product or suggested_product
            if not parsed_reply:
                ai_reply = fallback_reply
        except Exception as exc:
            logger.warning("Gemini reply failed, using fallback assistant: %s", exc)

    save_interaction_to_db(
        user_email,
        platform,
        customer_id,
        user_text,
        ai_reply,
        lead_score,
        summary,
    )

    if lead_score == "Hot" or detected_order:
        _send_hot_lead_alert(
            platform,
            customer_id,
            user_text,
            summary,
            lead_score,
            user_email,
            detected_order,
            suggested_product,
        )

    return ai_reply


def generate_follow_up_message(
    business_id,
    customer_id,
    last_message,
    score,
    platform="Social Media",
    products=None,
):
    """Generate a short follow-up nudge for stale leads."""
    biz_config = get_business_config(business_id) or {}
    user_email = biz_config.get("email", "admin@test.com")
    system_prompt = biz_config.get("system_prompt", "You are a professional business assistant.")
    if products is None:
        products = get_user_products(user_email)
    products = products or []

    top_product = products[0].get("name") if products else None
    fallback = (
        f"Hi! I wanted to check in about your interest{f' in {top_product}' if top_product else ''}. "
        "If you'd like, I can send a quick update or answer any questions."
    )

    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    model_name = os.getenv("GEMINI_MODEL", "gemini-1.5-flash").strip() or "gemini-1.5-flash"
    timeout_seconds = float(os.getenv("GEMINI_TIMEOUT_SECONDS", "12") or "12")
    if api_key and genai is not None:
        try:
            prompt = f"""
You are an AI business assistant.
The customer {customer_id} last messaged: "{last_message}" and their lead score is {score}.
Generate a friendly follow-up message to re-engage them.
Keep it short and polite. Do not be pushy.
If there are products that might interest them, mention one briefly.
"""
            future = _EXECUTOR.submit(_generate_follow_up_gemini_text, prompt, model_name, system_prompt)
            try:
                response_text = future.result(timeout=timeout_seconds)
            except FuturesTimeoutError:
                logger.warning("Gemini follow-up timed out after %ss, using fallback.", timeout_seconds)
                response_text = ""
            if response_text.strip():
                return response_text.strip()
        except Exception as exc:
            logger.warning("Gemini follow-up generation failed, using fallback: %s", exc)

    return fallback
