from app.services.live_payments import *  # noqa: F401,F403

if __name__ == "__main__":
    import runpy

    runpy.run_module("app.services.live_payments", run_name="__main__")
