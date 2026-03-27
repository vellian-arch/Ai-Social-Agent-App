from app.workers.youtube_worker import *  # noqa: F401,F403

if __name__ == "__main__":
    import runpy

    runpy.run_module("app.workers.youtube_worker", run_name="__main__")
