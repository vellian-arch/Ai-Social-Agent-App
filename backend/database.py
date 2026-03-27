from app.core.database import *  # noqa: F401,F403

if __name__ == "__main__":
    import runpy

    runpy.run_module("app.core.database", run_name="__main__")
