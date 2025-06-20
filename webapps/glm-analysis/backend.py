from flask import Flask
from backend.fetch_api import fetch_api
from backend.services import DataikuDataService
from dotenv import load_dotenv
import os
load_dotenv()

from webaiku.extension import WEBAIKU

app.data_service = DataikuDataService()

@app.errorhandler(Exception)
def handle_exception(e):
    """
    This function acts as a global safety net to catch all unhandled exceptions.
    """
    app.logger.exception(f"An unhandled exception occurred: {e}")
    return jsonify(error="An internal server error occurred. Please check the logs."), 500

WEBAIKU(app, "resource/dist")
WEBAIKU.extend(app, [fetch_api])