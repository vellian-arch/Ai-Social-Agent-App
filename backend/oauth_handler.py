from app.integrations.oauth_handler import *  # noqa: F401,F403

if __name__ == "__main__":
    import runpy

    runpy.run_module("app.integrations.oauth_handler", run_name="__main__")
