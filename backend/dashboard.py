from pathlib import Path

from dotenv import load_dotenv

_BACKEND_ENV = Path(__file__).resolve().parent / ".env"
_ROOT_ENV = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(_BACKEND_ENV, override=False)
load_dotenv(_ROOT_ENV, override=False)

from app.api.main import *  # noqa: F401,F403
from app.ui.dashboard import main

if __name__ == "__main__":
    main()
