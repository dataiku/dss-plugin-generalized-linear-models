from flask import Flask, jsonify
from .fetch_api import fetch_api
from dotenv import load_dotenv
import os
import logging
from .services import MockDataService, DataikuDataService

load_dotenv()

from webaiku.extension import WEBAIKU

app = Flask(__name__)
app.logger.setLevel(logging.DEBUG)

@app.errorhandler(Exception)
def handle_exception(e):
    """
    This function acts as a global safety net to catch all unhandled exceptions.
    """
    app.logger.exception(f"An unhandled exception occurred: {e}")
    return jsonify(error="An internal server error occurred. Please check the logs."), 500

if os.getenv('FLASK_ENV') == 'development':
    app.logger.info("Running in DEVELOPMENT mode, using Mock Service.")
    app.data_service = MockDataService()
else:
    app.logger.info("Running in PRODUCTION mode, using Dataiku Service.")
    app.data_service = DataikuDataService()

WEBAIKU(
    app, "webapps/vue_template", int(os.getenv("VITE_API_PORT"))
)

WEBAIKU.extend(app, [fetch_api])

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.getenv("VITE_API_PORT")), debug=True)
