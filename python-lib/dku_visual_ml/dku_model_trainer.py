import dataiku
from dataiku import pandasutils as pdu
import pandas as pd
import logging
from dataikuapi.dss.ml import DSSMLTask
import random
import string
from logging_assist.logging import logger
from dku_visual_ml.custom_configurations import dku_dataset_selection_params
from dku_visual_ml.dku_base import DataikuClientProject
from typing import List, Dict, Any


class VisualMLModelTrainer(DataikuClientProject):
    """
    A class to manage interacting with the Visual ML in dataiku when training Models.
    
    Attributes:
        client: Instance of the Dataiku API client.
        project: The default project from the Dataiku API client.
    """
    
    def __init__(self, visual_ml_config=None, mltask_id=None, analysis_id=None):
        super().__init__()
        logger.info("Initializing a Visual ML training task")
        self.visual_ml_config = visual_ml_config
        self.mltask = None
        if mltask_id and analysis_id:
            self.setup_using_existing_ml_task(mltask_id, analysis_id)

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
        self.mltask.guess(prediction_type=self.visual_ml_config.prediction_type)
        self.mltask.wait_guess_complete()
        logger.debug("Successfully refreshed the ml task")
    
    def setup_using_existing_ml_task(self, mltask_id, analysis_id):
        
        logger.debug(f"Updating the ml task with analysis id {analysis_id} and mltask_id {mltask_id}")
        
        self.mltask = self.project.get_ml_task(mltask_id=mltask_id, analysis_id=analysis_id)
        
        logger.info(f"Successfully update the existing ML task")
        

    def assign_train_test_policy(self):
        logger.info(f"Assigning train test policy")   

        if hasattr(self.visual_ml_config, "policy"):
            if self.visual_ml_config.policy == "explicit_test_set":
                logger.info(f"Configuration specifies test set, assigning")   
                settings = self.mltask.get_settings()
                settings.split_params.set_split_explicit(
                    dku_dataset_selection_params, 
                    dataset_name=self.visual_ml_config.input_dataset,
                    test_dataset_name=self.visual_ml_config.test_dataset_string)
                settings.save()
                logger.info(f"Saved test set to setting")
        
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
        analysis_name = str(self.visual_ml_config.analysis_name)
        new_analysis_defintion['name'] = str(self.visual_ml_config.input_dataset) + "_" + analysis_name
        self.visual_ml_config.analysis_id = analysis_id
        analysis_definition = analysis.set_definition(new_analysis_defintion)
    
    def create_initial_ml_task(self):
        logger.info("Creating an Inital ML Task")
        target_variable = self.visual_ml_config.get_target_variable()
        self.mltask = self.project.create_prediction_ml_task(
                input_dataset=self.visual_ml_config.input_dataset,
                target_variable=target_variable,
                ml_backend_type='PY_MEMORY',  # ML backend to use
                guess_policy='DEFAULT',  # Template to use for setting default parameters
                prediction_type=self.visual_ml_config.prediction_type
            )
        self.ml_task_variables = list(self.mltask.get_settings().get_raw().get('preprocessing').get('per_feature').keys())
        
        analysis_id = self.mltask.get_settings().analysis_id
        self.rename_analysis(analysis_id)

        self.update_visual_ml_task()
        self.enable_glm_algorithm()
        self.configure_variables()

        return self.mltask
        
        
    def update_visual_ml_task(self):
        """
        Updates a visual ML task in Dataiku.
        """
        logger.info("Creating Visual ML task")

        self.assign_train_test_policy()
        self.update_mltask_modelling_params()
        self.disable_existing_variables()
        logger.info("Successfully updated Visual ML task")
    
    def enable_glm_algorithm(self):
        """
        Enables the GLM algorithm for the ML task.
        """
        logger.info("Setting the model to GLM algorithm in ml task settings")
        settings = self.mltask.get_settings()
        settings.disable_all_algorithms()
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
        logger.debug(exposure_variable)
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
                            
        self.update_visual_ml_task()
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
        interaction_variables = self.visual_ml_config.get_interaction_variables()
        first_columns, second_columns = self.process_interaction_columns(interaction_variables)
        
        if hasattr(self.visual_ml_config, 'distribution_function'): # for training
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
                "alpha": self.visual_ml_config.theta,
                "power": self.visual_ml_config.power,
                "var_power": self.visual_ml_config.variance_power
            })
        else: # for init
            algo_settings = settings.get_algorithm_settings(
                'CustomPyPredAlgo_generalized-linear-models_generalized-linear-models_regression'
            )
            algo_settings['params'].update({
                "offset_mode": "OFFSETS/EXPOSURES",
                "offset_columns": [],
                "exposure_columns": [self.visual_ml_config.exposure_column],
                "training_dataset": self.visual_ml_config.input_dataset,
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
            fs['customHandlingCode'] = (
            'from dataiku.base.model_plugin import prepare_for_plugin\n'
            'prepare_for_plugin(\'generalized-linear-models\', \'generalized-linear-models_regression\')\n'
            'from processors.processors import save_base\n'
            'processor = save_base({"base_level": ' + str(base_level) + '})\n')
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
        fs['customHandlingCode'] = (
            'from dataiku.base.model_plugin import prepare_for_plugin\n'
            'prepare_for_plugin(\'generalized-linear-models\', \'generalized-linear-models_regression\')\n'
            'from processors.processors import rebase_mode\n'
            'processor = rebase_mode({"base_level": "' + str(base_level) + '"})\n')
        
        return fs      

         