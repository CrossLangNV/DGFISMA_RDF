import uvicorn

from reporting_obligations.app.main import app

if __name__ == "__main__":
    """
    Note that the application instance itself can be passed instead of the app import string.
    However, this style only works if you are not using multiprocessing (workers=NUM) or reloading (reload=True), so we recommend using the import string style.
    https://www.uvicorn.org/deployment/
    """

    if 0:
        uvicorn.run("example:app", host="127.0.0.1", port=80, log_level="info", reload=True)
    else:
        uvicorn.run(app, host="127.0.0.1", port=8080, log_level="info")
