import logging
from typing import Any, Dict
import dataiku
from dataiku.customwebapp import get_webapp_config
import pandas as pd
from dataiku.customrecipe import get_recipe_config
import os
import pwd
from typing import Optional

class DataikuApi:
    def __init__(self):
        self._webapp_config = None
        self._default_project = None
        self._default_project_key = None
        self._client = dataiku.api_client()

    def setup(self, webapp_config: Dict, default_project_key: str):
        print(os.environ["DKU_CURRENT_PROJECT_KEY"])
        self._webapp_config = webapp_config
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
    def default_project_key(self):
        try:
            return dataiku.get_custom_variables()["projectKey"]
        except Exception as err:
            if self._default_project_key:
                return self._default_project_key
            else:
                raise Exception("Please define the default project before using it.")

    @client.setter
    def client(self, c: Any):
        raise Exception(
            "If working outside of Dataiku, Client can only be set through the function setup()"
        )

    @property
    def webapp_config(self):
        try:
            self._webapp_config = get_webapp_config()
            return self._webapp_config
        except:
            return self._webapp_config

    @property
    def plugin_code_env(self):
        plugin = self.client.get_plugin('generalized-linear-models')
        return plugin.get_settings().get_raw()['codeEnvName']

    def get_root_lib_path(self):
        paths = os.environ.get("PYTHONPATH")
        if paths:
            target_directory = "project-python-libs"
            paths_splitted = paths.split(":")
            logger.info("DEBUG SPLITTED PATHS")
            logger.info(os.environ)
            logger.info(paths_splitted)
            for path in paths_splitted:
                if target_directory in path:
                    return os.path.join(
                        path.split(target_directory)[0],
                        target_directory,
                        self.default_project_key,
                    )
        return None

dataiku_api = DataikuApi()
