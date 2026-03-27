from app.integrations.platform_api import *  # noqa: F401,F403

if __name__ == "__main__":
    import runpy

    runpy.run_module("app.integrations.platform_api", run_name="__main__")
