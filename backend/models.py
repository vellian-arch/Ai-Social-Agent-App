from app.models import *  # noqa: F401,F403

if __name__ == "__main__":
    import runpy

    runpy.run_module("app.models", run_name="__main__")
