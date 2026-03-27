from app.legacy.master_controller import *  # noqa: F401,F403

if __name__ == "__main__":
    import runpy

    runpy.run_module("app.legacy.master_controller", run_name="__main__")
