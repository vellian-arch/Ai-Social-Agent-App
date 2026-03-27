from app.services.ai_engine import *  # noqa: F401,F403

if __name__ == "__main__":
    import runpy

    runpy.run_module("app.services.ai_engine", run_name="__main__")
