from flask import Flask
from backend.fetch_api import fetch_api
from backend.services import DataikuDataService
from dotenv import load_dotenv
import os
load_dotenv()

from webaiku.extension import WEBAIKU

app.data_service = DataikuDataService()

WEBAIKU(app, "resource/dist")
WEBAIKU.extend(app, [fetch_api])