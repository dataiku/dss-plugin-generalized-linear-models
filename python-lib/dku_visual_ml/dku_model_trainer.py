import dataiku
from dataiku import pandasutils as pdu
import pandas as pd
import logging
from dataikuapi.dss.ml import DSSMLTask
import random
import string
from logging_assist.logging import logger
from dku_visual_ml.custom_configurations import dku_dataset_selection_params, custom_base_none
from dku_visual_ml.dku_base import DataikuClientProject
from glm_handler.dku_model_deployer import ModelDeployer
from typing import List, Dict, Any


class VisualMLModelTrainer(DataikuClientProject):
    """
    A class to manage interacting with the Visual ML in dataiku when training Models.
    
    Attributes:
        client: Instance of the Dataiku API client.
        project: The default project from the Dataiku API client.
    """
    
    def __init__(self, visual_ml_config=None):
        super().__init__()
        logger.info("Initializing a Visual ML training task")
        self.visual_ml_config = visual_ml_config
        self.mltask = None

        logger.info("Initalized a Visual ML training task successfully")
        if visual_ml_config:
            logger.debug(f"With config {self.visual_ml_config.log_configuration()}")
    
    def get_latest_ml_task(self):
        return self.mltask
    
    def update_visual_ml_config(self, visual_ml_config):
        
        logger.info("Updating a Visual ML config for the Visual ML Interaction")
        self.visual_ml_config = visual_ml_config
        logger.info("Successfully updated a Visual ML config")
        
        return None
    
    def _refresh_mltask(self):
        
        logger.debug("Refreshing the ml task")
        self.mltask.guess()
        self.mltask.wait_guess_complete()
        logger.debug("Successfully refreshed the ml task")
    
    def setup_using_existing_ml_task(self, analysis_id):
        
        logger.debug(f"Updating the ml task with analysis id {analysis_id}")
        
        self.analysis= self.project.get_analysis(analysis_id)
        self.mltask_id = self.analysis.list_ml_tasks().get('mlTasks')[0].get('mlTaskId')
        self.mltask = self.analysis.get_ml_task(self.mltask_id)
        self.remove_failed_trainings()
        
        logger.info(f"Successfully update the existing ML task")
        

    def assign_train_test_policy(self):
        logger.info(f"Assigning train test policy")   
     
        if self.visual_ml_config.policy == "explicit_test_set":
            logger.info(f"Configuration specifies test set, asigning")   
            settings = self.mltask.get_settings()
            settings.split_params.set_split_explicit(
                dku_dataset_selection_params, 
                dku_dataset_selection_params, 
                dataset_name=self.visual_ml_config.input_dataset,
                test_dataset_name=self.visual_ml_config.test_dataset_string)
            settings.save()
            logger.info(f"Saved test set to setting")  
              
        else:
            return
        
    def disable_existing_variables(self):
        logger.debug(f"Disabling variables from the ml task config") 
        
        settings = self.mltask.get_settings()
        target_variable = self.visual_ml_config.get_target_variable()
        logger.debug(f"Target Variable is {target_variable}")
        logger.debug(f"Settings are {settings}")
        for feature_name in settings.get_raw()['preprocessing']['per_feature'].keys():
            feature_role = settings.get_raw()['preprocessing']['per_feature'][feature_name].get('role')
            logger.debug(f"feature role is {feature_role}")
            if feature_name != target_variable or (feature_role!="TARGET"):
                settings.reject_feature(feature_name)
        settings.save()
        
        logger.info(f"Successfully disabled all variables from the ml task config other than {target_variable}") 
        return
    
    def rename_analysis(self, analysis_id):
        
        analysis = self.project.get_analysis(analysis_id)
        new_analysis_defintion = analysis.get_definition().get_raw()
        experiment_name = str(self.visual_ml_config.experiment_name)
        new_analysis_defintion['name'] = str(self.visual_ml_config.input_dataset) + "_" + experiment_name
        analysis_definition = analysis.set_definition(new_analysis_defintion)
    
    def create_initial_ml_task(self):
        logger.info("Creating an Inital ML Task")
        target_variable = self.visual_ml_config.get_target_variable()
        self.mltask = self.project.create_prediction_ml_task(
                input_dataset=self.visual_ml_config.input_dataset,
                target_variable=target_variable,
                ml_backend_type='PY_MEMORY',  # ML backend to use
                guess_policy='DEFAULT'  # Template to use for setting default parameters
            )
        
        self.ml_task_variables = list(self.mltask.get_settings().get_raw().get('preprocessing').get('per_feature').keys())
        
        analysis_id = self.mltask.get_settings().analysis_id
        self.rename_analysis(analysis_id)
        logger.info("Inital ML Task Created")
        return self.mltask
        
        
    def create_visual_ml_task(self):
        """
        Creates a new visual ML task in Dataiku.
        """
        logger.info("Creating Visual ML task")
        
       
        # Create a new ML Task to predict the variable from the specified dataset
        if not self.mltask:
            logger.info("Creating a new ML task")
            target = self.visual_ml_config.get_target_variable()
            self.mltask = self.create_inital_ml_task(target)
        else:
            logger.info("ML task already exists")
            self._refresh_mltask()
            
        self.assign_train_test_policy()
        self.update_mltask_modelling_params()
        self.disable_existing_variables()
        logger.info("Successfully created Visual ML task")
    
    def enable_glm_algorithm(self):
        """
        Enables the GLM algorithm for the ML task.
        """
        logger.info("Setting the model to GLM algorithm in ml task settings")
        settings = self.mltask.get_settings()
        settings.disable_all_algorithms()
        
        # Assuming GLM is represented as 'GLM_REGRESSION' or 'GLM_CLASSIFICATION', adjust as necessary
        settings.set_algorithm_enabled("CustomPyPredAlgo_generalized-linear-models_generalized-linear-models_regression", True)
        settings.save()
        logger.info("Successfully set the model to GLM algorithm in ml task settings")
        
        
    def _process_variables(self, settings: Any, variables: List[str], include: bool):
            action = "Including" if include else "Excluding"
            logger.debug(f"{action} variables: {variables}")

            for variable in variables:
                self._process_single_variable(settings, variable, include)

    def _process_single_variable(self, settings: Any, variable: str, include: bool):
            logger.debug(f"Processing variable: {variable}")
            
            fs = settings.get_feature_preprocessing(variable)
            variable_type = self.visual_ml_config.get_variable_type(variable)
            base_level = self.visual_ml_config.variables[variable].get('base_level', None)

            if variable_type == 'categorical':
                fs = self.update_to_categorical(fs, base_level)
            elif variable_type == 'numerical':
                fs = self.update_to_numeric(fs, base_level)
                
            if include:
                settings.use_feature(variable)
            else:
                settings.reject_feature(variable)
                logger.debug(f"Rejecting feature {variable} from Dataiku ML task settings")


                
    def set_included_variables(self):
        logger.debug("Updating the Dataiku ML task settings for included variables")
        
        settings = self.mltask.get_settings()
        model_features = self.visual_ml_config.get_model_features()
        excluded_variables = self.visual_ml_config.get_excluded_features()

        self._process_variables(settings, model_features, include=True)
        self._process_variables(settings, excluded_variables, include=False)

        settings.save()
        logger.debug("Successfully updated the Dataiku ML task settings for included/excluded variables")


                    
    def set_exposure_variable(self):
        logger.debug("Updating the Dataiku ML task settings for exposure variables")
        exposure_variable = self.visual_ml_config.get_exposure_variable()
        settings = self.mltask.get_settings()
        settings.use_feature(exposure_variable)
        fs = settings.get_feature_preprocessing(exposure_variable)
        fs = self.update_to_numeric(fs, None)
        settings.save()
        logger.debug("Successfully updated the Dataiku ML task settings for exposure variables")
    
    def configure_variables(self):
        """
        Configures the variables for the ML task, setting the type of processing for each.
        """
        logger.info("Setting the variables and preprocecssing for each variable")
        
        self.set_included_variables()
        self.set_exposure_variable()
        self.set_target_variable()
        
        logger.debug('***Updated settings are:***')
        settings = self.mltask.get_settings()
        for feature in settings.get_raw().get('preprocessing').get('per_feature'):
            logger.info(f"Feature {feature} {settings.get_raw().get('preprocessing').get('per_feature').get(feature).get('role')} ")
        
        logger.info("Successfully set the variables and preprocecssing for each variable") 
        
        return settings
    
    def set_target_variable(self):
        """
        Sets the target variable for the ML task.
        """
        logger.info("Setting the target variables in the dataiku ML task")
        settings = self.mltask.get_settings()
        target_variable = self.visual_ml_config.get_target_variable()
        feature_settings = settings.get_feature_preprocessing(target_variable)
        feature_settings['role'] = "TARGET"
        settings.save()
        logger.info(f"Succesfully set the target variables to {target_variable} for model training")
        return
    
    def set_code_env_settings(self,code_env_string):
        settings = self.mltask.get_settings()
        settings.mltask_settings['envSelection']['envMode'] = 'EXPLICIT_ENV'
        settings.mltask_settings['envSelection']['envName'] = code_env_string
        settings.save()
        logger.info(f"set code env settings to {self.mltask.get_settings().mltask_settings.get('envSelection')} ")
    
    def remove_failed_trainings(self):
        
        ids = self.mltask.get_trained_models_ids()
        for model_id in ids:
            state = self.mltask.get_trained_model_details(model_id).details.get('trainInfo').get('state')
            if state == "FAILED":
                self.mltask.delete_trained_model(model_id)
        
    
    def get_latest_model(self):
        """
        Retrieves the ID of the latest trained model.

        This function iterates through all the model IDs obtained from the ML task,
        comparing their start times to find the most recently trained model. It returns
        the ID of this model.

        Returns:
            str: The ID of the latest trained model.
        """
        logger.info("Retrieving the latest model ID.")
        latest_model_id = None
        latest_start_time = 0
        ids = self.mltask.get_trained_models_ids()
        if not ids:
            logger.warning("No trained models found.")
            return None

        for model_id in ids:
            details = self.mltask.get_trained_model_details(model_id).get_raw()
            start_time = details['trainInfo']['startTime']
            if start_time > latest_start_time:
                latest_start_time = start_time
                latest_model_id = model_id
                logger.debug(f"New latest model found: {model_id} with start time {start_time}")

        if latest_model_id is None:
            logger.warning("Failed to find the latest model.")
        else:
            logger.info(f"Latest model ID: {latest_model_id}")
        return latest_model_id
    
    def check_failure_get_error_message(self, latest_model_id):
        
        status = self.mltask.get_trained_model_details(latest_model_id).details.get('trainInfo').get('state')
        try:
            message = self.mltask.get_trained_model_details(latest_model_id).details.get('trainInfo').get('failure').get('message', None)
        except:
            message = None
        return status, message
    
    
    def train_model(self, code_env_string, session_name=None):
        """
        Trains the model with the current configuration and then deploys it.

        Args:
            code_env_string (str): A string specifying the code environment settings.
            session_name (str, optional): The name of the training session. Defaults to None.

        Trains the model by setting the code environment, starting the training process,
        waiting for it to complete, and then deploying the trained model.
        """
        logging.info("Starting model training.")
                            
        self.create_visual_ml_task()
        self.enable_glm_algorithm()
        settings_new = self.configure_variables()
        self.set_code_env_settings(code_env_string)
        self.mltask.start_train(session_name=session_name)
        details = self.mltask.wait_train_complete()
        logging.info("Model training completed. Deploying the model.")
        
        latest_model_id = self.get_latest_model()
        status, error_message = self.check_failure_get_error_message(latest_model_id)
        
        if status == "FAILED":
            if error_message == "Failed to train : <class 'numpy.linalg.LinAlgError'> : Matrix is singular.":
                error_message = error_message + "Check colinearity of variables added to the model"
            self.remove_failed_trainings()
            return None, error_message
        else:
            return None, error_message
    
    def process_interaction_columns(self, interaction_columns):
        print(f"interaction columns are {interaction_columns}")
        interaction_columns_first = []
        interaction_columns_second = []
        
        for interaction in interaction_columns:
            first = interaction['first']
            second = interaction['second']
            interaction_columns_first.append(first)
            interaction_columns_second.append(second)
            
        return interaction_columns_first, interaction_columns_second
        
    def update_mltask_modelling_params(self):
        """
        Updates the modeling parameters based on the distribution function, link function, elastic net penalty, l1 ratio
        and any special variables like exposure or offset.
        """
        settings = self.mltask.get_settings()
        settings.get_raw()['modeling']['skipExpensiveReports'] = True
        exposure_variable = self.visual_ml_config.get_exposure_variable()
        interaction_variables = self.visual_ml_config.get_interaction_variables()
        first_columns, second_columns = self.process_interaction_columns(interaction_variables)
            
        offset_variable = None
        
        algo_settings = settings.get_algorithm_settings(
            'CustomPyPredAlgo_generalized-linear-models_generalized-linear-models_regression'
        )
        algo_settings['params'].update({
            f"{self.visual_ml_config.distribution_function}_link": self.visual_ml_config.link_function,
            "family_name": self.visual_ml_config.distribution_function,
            "penalty": [self.visual_ml_config.elastic_net_penalty],
            "l1_ratio": [self.visual_ml_config.l1_ratio],
            "interaction_columns_first":first_columns,
            "interaction_columns_second":second_columns,
        })
        
        # Handle exposure and offset variables
        if offset_variable and exposure_variable:
            algo_settings['params'].update({
                "offset_mode": "OFFSETS/EXPOSURES",
                "offset_columns": [offset_variable],
                "exposure_columns": [exposure_variable],
                "training_dataset": self.visual_ml_config.input_dataset,
            })
        elif exposure_variable:
            algo_settings['params'].update({
                "offset_mode": "OFFSETS/EXPOSURES",
                "offset_columns": [],
                "exposure_columns": [exposure_variable],
                "training_dataset": self.visual_ml_config.input_dataset,
            })
        elif offset_variable:
            algo_settings['params'].update({
                "offset_mode": "OFFSETS",
                "offset_columns": [offset_variable],
                "training_dataset": self.visual_ml_config.input_dataset,
            })
        else:
            algo_settings['params'].update({
                "offset_mode": "BASIC",
            })
        
        settings.save()
        return
    
    def update_to_numeric(self, fs, base_level):
    
        fs['generate_derivative'] = False
        if base_level is None:
            fs['numerical_handling'] = 'REGULAR'
        else:
            fs['numerical_handling'] = 'CUSTOM'
        fs['missing_handling'] = 'IMPUTE'
        fs['missing_impute_with'] = 'MEAN'
        fs['impute_constant_value'] = 0.0
        fs['keep_regular'] = False
        fs['rescaling'] = "NONE"
        fs['quantile_bin_nb_bins'] = 4
        fs['binarize_threshold_mode'] = 'MEDIAN'
        fs['binarize_constant_threshold'] = 0.0
        fs['datetime_cyclical_periods'] = []
        fs['role'] = 'INPUT'
        fs['type'] = 'NUMERIC'
        if base_level is None:
            fs['customHandlingCode'] = ''
        else:
            fs['customHandlingCode'] = ('import pandas as pd\n'
            'import numpy as np\n'
            'class save_base():\n'
            '    """This processor applies no transformation but saves a base level\n'
            '    """\n'
            '    def __init__(self):\n'
            '        self.mode_column = None\n'
            '    def fit(self, series):\n'
            '        # define the base level\n'
            '        self.mode_column = '+ str(base_level) + '\n'
            '        self.modalities = np.unique(series)\n'
            '    def transform(self, series):\n'
            '        return pd.DataFrame(series)\n'
            '    \n'
            'processor = save_base()')
        fs['customProcessorWantsMatrix'] = True
        fs['sendToInput'] = 'main'
        return fs
    
    def update_to_categorical(self, fs, base_level):
        
        fs['missing_impute_with']= 'MODE'
        fs['type']= 'CATEGORY'
        fs['category_handling'] = "CUSTOM"
        fs['missing_handling'] = 'IMPUTE'
        fs['dummy_clip'] = 'MAX_NB_CATEGORIES'
        fs['cumulative_proportion'] = 0.95
        fs['min_samples'] = 10
        fs['max_nb_categories'] = 100
        fs['max_cat_safety'] = 200
        fs['nb_bins_hashing'] = 1048576
        fs['hash_whole_categories'] = True
        fs['dummy_drop'] = 'AUTO'
        fs['impact_method'] = 'M_ESTIMATOR'
        fs['impact_m'] = 10
        fs['impact_kfold'] = True
        fs['impact_kfold_k'] = 5
        fs['impact_kfold_seed'] = 1337
        fs['ordinal_order'] = 'COUNT'
        fs['ordinal_ascending'] = False
        fs['ordinal_default_mode'] = 'HIGHEST'
        fs['ordinal_default_value'] = 0
        fs['frequency_default_mode'] = 'EXPLICIT'
        fs['frequency_default_value'] = 0.0
        fs['frequency_normalized'] = True
        fs['role'] = 'INPUT'
        fs['customHandlingCode'] = ''
        fs['customProcessorWantsMatrix'] = False
        fs['sendToInput'] = 'main'
        fs['customHandlingCode'] = ('import numpy as np\n'
        'import pandas as pd\n'
        'class rebase_mode():\n'
        '    """This processor applies dummy vectorisation, but drops the dummy column with the mode. Only applies to categorical variables\n'
        '    """\n'
        '    def __init__(self):\n'
        '        self.mode_column = None\n'
        '    def fit(self, series):\n'
        '        # identify the mode of the column, returns as a text value\n'
        '        self.modalities = np.unique(series)\n'
        '        self.mode_column = "' + base_level + '"\n'
        '        self.columns = set(self.modalities)\n'
        '        self.columns = list(self.columns)\n'
        '        self.columns.remove(self.mode_column)\n'
        '        self.column_name = series.name\n'
        '    def transform(self, series):\n'
        '        to_replace={m: self.mode_column for m in np.unique(series) if m not in self.modalities}\n'
        '        new_series = series.replace(to_replace=to_replace)\n'
        '        # obtains the dummy encoded dataframe, but drops the dummy column with the mode identified\n'
        '        df = pd.get_dummies(new_series.values)\n'
        '        if self.mode_column in df:\n'
        '            df = df.drop(self.mode_column, axis = 1)\n'
        '        for c in self.columns:\n'
        '            if c not in df.columns:\n'
        '                df[c] = 0\n'
        '        df = df[self.columns]\n'
        '        return df\n'
        'processor = rebase_mode()')
        
        return fs      

         