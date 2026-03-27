from app.legacy.webhook_handler import *  # noqa: F401,F403

if __name__ == "__main__":
    import runpy

    runpy.run_module("app.legacy.webhook_handler", run_name="__main__")
