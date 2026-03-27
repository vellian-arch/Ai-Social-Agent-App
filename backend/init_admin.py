from scripts.init_admin import *  # noqa: F401,F403

if __name__ == "__main__":
    import runpy

    runpy.run_module("scripts.init_admin", run_name="__main__")
