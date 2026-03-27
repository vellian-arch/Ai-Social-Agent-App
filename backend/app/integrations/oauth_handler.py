import os
import urllib.parse

from google_auth_oauthlib.flow import Flow


def _resolve_redirect_uri(default_path: str) -> str:
    backend_public_url = os.getenv("BACKEND_PUBLIC_URL", "").strip()
    if backend_public_url:
        return f"{backend_public_url.rstrip('/')}{default_path}"
    return os.getenv("GOOGLE_REDIRECT_URI") or f"http://localhost:8000{default_path}"


def get_google_auth_url(user_email):
    """
    Generate Google OAuth URL for YouTube.
    Returns the URL to redirect the user to.
    """
    redirect_uri = _resolve_redirect_uri("/oauth/youtube/callback")
    client_config = {
        "web": {
            "client_id": os.getenv("GOOGLE_CLIENT_ID"),
            "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [redirect_uri],
        }
    }
    flow = Flow.from_client_config(
        client_config,
        scopes=["https://www.googleapis.com/auth/youtube.force-ssl"],
        redirect_uri=redirect_uri,
    )
    auth_url, _ = flow.authorization_url(
        prompt="consent",
        state=user_email,
        access_type="offline",
        include_granted_scopes="true",
    )
    return auth_url


def get_tiktok_auth_url(user_email):
    """
    Generate TikTok OAuth URL.
    Returns the URL to redirect the user to.
    """
    client_key = os.getenv("TIKTOK_CLIENT_KEY")
    backend_public_url = os.getenv("BACKEND_PUBLIC_URL", "").strip()
    redirect_uri = (
        f"{backend_public_url.rstrip('/')}/oauth/tiktok/callback"
        if backend_public_url
        else os.getenv("TIKTOK_REDIRECT_URI") or "http://localhost:8000/oauth/tiktok/callback"
    )
    params = {
        "client_key": client_key,
        "response_type": "code",
        "scope": "user.info.basic,video.list,message.send",
        "redirect_uri": redirect_uri,
        "state": user_email,
    }
    url = "https://www.tiktok.com/v2/auth/authorize/?" + urllib.parse.urlencode(params)
    return url
