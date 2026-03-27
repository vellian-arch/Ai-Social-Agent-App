from app.services.notifications import *  # noqa: F401,F403

if __name__ == "__main__":
    import runpy

    runpy.run_module("app.services.notifications", run_name="__main__")
