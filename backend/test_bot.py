from scripts.test_bot import *  # noqa: F401,F403

if __name__ == "__main__":
    import runpy

    runpy.run_module("scripts.test_bot", run_name="__main__")
