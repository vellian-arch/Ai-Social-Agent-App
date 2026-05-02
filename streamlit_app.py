from __future__ import annotations

import streamlit as st
import sys
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parent / "backend"
ASSETS_DIR = BACKEND_DIR / "app" / "ui" / "assets"

APP_ICON_PATH = ASSETS_DIR / "social_ai_agent_logo.svg"
APP_FAVICON_PATH = ASSETS_DIR / "social_ai_agent_favicon_v3.ico"

st.set_page_config(
    page_title="Social Ai Agent",
    page_icon=str(APP_FAVICON_PATH if APP_FAVICON_PATH.exists() else APP_ICON_PATH),
    layout="wide",
    initial_sidebar_state="expanded",
)

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from dashboard import main  # noqa: E402


if __name__ == "__main__":
    main()
