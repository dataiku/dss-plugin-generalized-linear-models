import logging
from typing import Any, Dict
import dataiku
import pandas as pd
from dataiku.customwebapp import get_webapp_config
import os
import pwd
from typing import Optional

class DataikuApi:
    def __init__(self):
        self._default_project = None
        self._default_project_key = None
        self._client = dataiku.api_client()

    def setup(self, default_project_key: str):
        self._default_project_key = default_project_key

    @property
    def client(self):
        if self._client is None:
            raise Exception("Please set the client before using it.")
        else:
            return self._client

    @property
    def default_project(self):
        try:
            return self.client.get_default_project()
        except Exception as err:
            if self._default_project_key:
                return self.client.get_project(self._default_project_key)
            else:
                raise Exception("Please define the default project before using it.")

    @property
    def plugin_code_env(self):
        plugin = self.client.get_plugin('generalized-linear-models')
        webapp_config = get_webapp_config()
        plugin_code_env = webapp_config.get("plugin_code_env", None)
        if plugin_code_env:
            return plugin_code_env
        try:
            return plugin.get_settings().get_raw()['codeEnvName']
        except Exception as e:
            if "unauthorizedexception" in str(e).lower():
                raise Exception("Could not retrieve the plugin code environment name. Please run backend as admin or set the plugin_code_env in the webapp settings.")
            else:
                raise

dataiku_api = DataikuApi()
