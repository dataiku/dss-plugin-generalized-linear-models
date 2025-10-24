import dataiku
import pandas as pd
from logging_assist.logging import logger

class DataikuClientProject:
    """
    A base class to initialize Dataiku client and project
    """
    
    def __init__(self):
        self.client = dataiku.api_client()
        self.project = self.client.get_default_project()
        logger.info(f"Dataiku client and project initialized for project {self.project.project_key}")

    def format_ml_task(self, ml_task_config):
        glm_algo_name = 'CustomPyPredAlgo_generalized-linear-models_generalized-linear-models_regression'
        ml_task = self.project.get_ml_task(analysis_id=ml_task_config['analysisId'], mltask_id=ml_task_config['mlTaskId'])
        settings = ml_task.get_settings()
        split_params = settings.split_params.get_raw()
        is_valid = True
        if split_params['ttPolicy'] == 'SPLIT_SINGLE_DATASET':
            test_set = ""
            split_policy = "random"
        elif split_params['ttPolicy'] == 'EXPLICIT_TEST_SET':
            test_set = "REPLACE_ME"
            split_policy = "explicit"
        else:
            test_set = ""
            split_policy = ""
            is_valid = False
        enabled_algorithms = settings.get_enabled_algorithm_names()
        enabled_algorithm_settings = settings.get_enabled_algorithm_settings()
        if glm_algo_name not in enabled_algorithms:
            is_valid = False
            exposure_column = ""
        else:
            algorithm_settings = enabled_algorithm_settings[glm_algo_name]
            exposure_columns = algorithm_settings['params']['exposure_columns']
            if len(exposure_columns) == 1:
                exposure_column = exposure_columns[0]
            else:
                exposure_column = ""
                is_valid = False
        target_variable = settings.get_raw()['targetVariable']
        ml_task_formatted = {"analysisName": ml_task_config['analysisName'],
                            "analysisId": ml_task_config['analysisId'],
                            "mlTaskId": ml_task_config['mlTaskId'],
                            "trainSet": ml_task_config['inputDataset'],
                            "testSet": test_set,
                            "splitPolicy": split_policy,
                            "isValid": is_valid,
                            "exposureColumn": exposure_column,
                            "targetColumn": target_variable}
        return ml_task_formatted

    def get_ml_tasks(self):
        ml_tasks = self.project.list_ml_tasks()
        ml_tasks_formatted = []
        for ml_task_config in ml_tasks['mlTasks']:
            if ml_task_config['taskType'] == 'PREDICTION':
                ml_task_formatted = self.format_ml_task(ml_task_config)
                ml_tasks_formatted.append(ml_task_formatted)
        return ml_tasks_formatted
    
    def get_ml_task_config(self, ml_task_id):
        ml_tasks = self.project.list_ml_tasks()
        matching_configs = [config for config in ml_tasks['mlTasks'] if config['mlTaskId']==ml_task_id]
        if len(matching_configs) == 1:
            return matching_configs[0]
        else:
            raise ValueError(f"Ml Task Id {ml_task_id} not found")

    def get_datasets(self):
        datasets = self.project.list_datasets()
        dataset_names = [{'name': dataset['name']} for dataset in datasets]
        return dataset_names
    
    def get_variables_for_dataset(self, dataset_name):
        dataset = dataiku.Dataset(dataset_name)
        columns = dataset.get_config()['schema']['columns']
        df = dataset.get_dataframe(limit=100)
        numeric_columns = []
        for column in columns:
            col_name = column['name']
            if col_name in df.columns:
                if pd.api.types.is_numeric_dtype(df[col_name]):
                    numeric_columns.append({'name': col_name})
        return numeric_columns