from app.api.main import app  # noqa: F401

if __name__ == "__main__":
    import uvicorn

    # Run the app with the same invocation used in the README / instructions.
    uvicorn.run(app, host="0.0.0.0", port=8000)
