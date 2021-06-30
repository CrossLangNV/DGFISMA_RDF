import os

import uvicorn

# No relative import possible as this is __main__.
from dgfisma_rdf.reporting_obligations.app.main import app

if __name__ == "__main__":
    """
    Note that the application instance itself can be passed instead of the app import string.
    However, this style only works if you are not using multiprocessing (workers=NUM) or reloading (reload=True), so we recommend using the import string style.
    https://www.uvicorn.org/deployment/
    """

    # Other options if automatic reloading is required.
    # uvicorn.run("example:app", host="127.0.0.1", port=80, log_level="info", reload=True)
    port = int(os.environ.get("PORT", 8081))
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="info")
