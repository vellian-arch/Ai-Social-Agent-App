from scripts.register_user import *  # noqa: F401,F403

if __name__ == "__main__":
    import runpy

    runpy.run_module("scripts.register_user", run_name="__main__")
