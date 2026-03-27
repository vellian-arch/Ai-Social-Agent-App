from app.services.dashboard_utils import *  # noqa: F401,F403

if __name__ == "__main__":
    import runpy

    runpy.run_module("app.services.dashboard_utils", run_name="__main__")
