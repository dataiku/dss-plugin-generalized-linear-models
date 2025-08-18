# Create a new file: backend/services.py
import pandas as pd
from flask import current_app
import time
import random
import dataiku

# You would import your actual logic and dummy data here
from .local_config import *
from .dataiku_api import dataiku_api
from .api_utils import calculate_base_levels, get_model_train_set, get_model_test_set, get_model_predicted_base, get_model_base_values_modalities_types, get_model_relativities, get_model_relativities_interaction, get_model_variable_level_stats, format_models
from dataiku.customwebapp import get_webapp_config
from chart_formatters.lift_chart import LiftChartFormatter
from model_cache.model_cache import ModelCache
from dku_visual_ml.dku_model_trainer import VisualMLModelTrainer
from dku_visual_ml.dku_model_retrival import VisualMLModelRetriver
from glm_handler.glm_data_handler import GlmDataHandler
from dku_visual_ml.dku_train_model_config import DKUVisualMLConfig
from dku_visual_ml.dku_model_deployer import VisualMLModelDeployer

class MockDataService:
    """
    Dev backend service with dummy data
    """
    def train_model(self, request_json: dict):
        current_app.logger.info("Local set up: No model training completed")
        time.sleep(2)
        return {'message': 'Model training initiated successfully.'}
    
    def deploy_model(self, request_json: dict):
        current_app.logger.info("Local set up: No model deployment completed")
        time.sleep(2)
        return {'message': 'Model deployed successfully.'}
    
    def delete_model(self, request_json: dict):
        current_app.logger.info("Local set up: No model deletion completed")
        time.sleep(1)
        return {'message': 'Model deleted successfully.'}

    def get_latest_mltask_params(self, request_json: dict):
        current_app.logger.info("Getting Latest ML task set up parameters")
        full_model_id = request_json["id"]
        if full_model_id== "model_interaction":
            setup_params = interaction_setup_params
        else:
            setup_params = random.choice([dummy_setup_params, dummy_setup_params_2])
        current_app.logger.info(f"Returning Params {setup_params}")
        return setup_params
    
    def get_variables(self, request_json: dict):
        return dummy_variables
    
    def get_models(self):
        return dummy_models
    
    def get_predicted_base(self, request_json: dict):
        time.sleep(1)
        variable = request_json['variable']
        dummy_df_variable = dummy_df_data[dummy_df_data['definingVariable'] == variable]
        return dummy_df_variable.to_dict('records')
    
    def get_base_values(self, request_json: dict):
        current_app.logger.info("Running Locally")
        return dummy_base_values

    def get_lift_data(self, request_json: dict):
        time.sleep(1)
        return dummy_lift_data.to_dict('records')
    
    def get_relativities(self, request_json: dict):
        return dummy_relativites.to_dict('records')
    
    def get_variable_level_stats(self, request_json: dict):
        time.sleep(1)
        current_app.logger.info("Getting Variable Level Stats")
        return dummy_variable_level_stats
    
    def get_model_metrics(self, request_json: dict):
        return dummy_model_metrics

    def export_model(self, request_json: dict):
        data = {'Name': ['John', 'Alice', 'Bob'], 'Age': [30, 25, 35]}
        df = pd.DataFrame(data)

        # Convert DataFrame to CSV format
        csv_data = df.to_csv(index=False).encode('utf-8')

        return csv_data
    
    def export_variable_level_stats(self, request_json: dict):
        # Convert DataFrame to CSV format
        csv_data = dummy_variable_level_stats.to_csv(index=False).encode('utf-8')

        return csv_data
    
    def export_lift_chart(self, request_json: dict):
        # Convert DataFrame to CSV format
        csv_data = dummy_variable_level_stats.to_csv(index=False).encode('utf-8')

        return csv_data
    
    def export_one_way(self, request_json: dict):
        current_app.logger.info("Exporting one way graphs")
        csv_data = variable_level_stats_df.to_csv(index=False).encode('utf-8')
        return csv_data
    
    def get_excluded_columns(self):
        exposure_column = "Exposure"
        target_column = "ClaimAmount"
        
        cols_json = {
            "target_column": target_column,
            "exposure_column": exposure_column
        }
        return cols_json
    
    def get_dataset_columns(self):
        dataset_name = "claim_train"
        exposure_column = "exposure"
        
        current_app.logger.info(f"Training Dataset name selected is: {dataset_name}")
        
        df = dataiku.Dataset(dataset_name).get_dataframe(limit=100000)
        cols_json = calculate_base_levels(df, exposure_column)

        current_app.logger.info(f"Successfully retrieved column for dataset '{dataset_name}': {[col['column'] for col in cols_json]}")

        return cols_json
    
    def update_config(self, request_json):
        return {'message': 'Settings updated.'}
    
    
class DataikuDataService:
    """
    Real Prod service connected to a visual analysis
    """
    def __init__(self):
        self.model_cache = ModelCache()
        self.visual_ml_config = DKUVisualMLConfig()
        self.visual_ml_trainer = VisualMLModelTrainer(self.visual_ml_config)
        self.data_handler = GlmDataHandler()
        if self.visual_ml_config.create_new_analysis:
            self.visual_ml_trainer.create_initial_ml_task()
        else:
            self.visual_ml_trainer.setup_using_existing_ml_task(
                self.visual_ml_config.analysis_id
            )
        self.visual_ml_deployer = VisualMLModelDeployer(self.visual_ml_trainer.mltask, self.visual_ml_config.saved_model_id)
    
    def train_model(self, request_json: dict):
        current_app.logger.info(f"Initalising Model Training with request {request_json}")
    
        self.visual_ml_config.update_model_parameters(request_json)

        current_app.logger.debug("Creating Visual ML Trainer")
        self.visual_ml_trainer.update_visual_ml_config(self.visual_ml_config)

        model_details, error_message = self.visual_ml_trainer.train_model(
            code_env_string=dataiku_api.plugin_code_env,
            session_name=self.visual_ml_config.model_name_string
        )
        current_app.logger.debug(f"Model error message is {error_message}")
        current_app.logger.debug(f"Model details are {model_details}")
        
        if not error_message:
            current_app.logger.info("Model trained and cache updated")
            return {'message': 'Model training completed successfully.'}
        else:
            current_app.logger.debug(f"Model training error: {error_message}")
            raise ValueError(f"Model training error: {error_message}")
    
    def deploy_model(self, request_json: dict):
        current_app.logger.info(f"Initalising Model Deployment with request {request_json}")
    
        model_id = request_json['id']
        self.visual_ml_deployer.set_new_active_version(model_id, self.visual_ml_config.input_dataset, self.visual_ml_config.analysis_name)

        return {'message': 'Model deployed successfully.'}
    
    def delete_model(self, request_json: dict):
        current_app.logger.info(f"Deleting Model with request {request_json}")
    
        model_id = request_json['id']
        self.visual_ml_deployer.delete_model(model_id)
        model_retriver = VisualMLModelRetriver(model_id)
        model_retriver.delete_model(model_id)

        return {'message': 'Model deleted successfully.'}
    
    def get_latest_mltask_params(self, request_json: dict):
        current_app.logger.info("Getting Latest ML task set up parameters")
        full_model_id = request_json["id"]
        
        current_app.logger.info(f"Recieved request for latest params for: {full_model_id}")
        
        model_retriver = VisualMLModelRetriver(full_model_id)
        setup_params = model_retriver.get_setup_params()
    
        current_app.logger.info(f"Returning setup params {setup_params}")
        return setup_params
    
    def get_variables(self, request_json: dict):
        full_model_id = request_json["id"]
        try:
            model_retriever = VisualMLModelRetriver(full_model_id)
            variables = model_retriever.get_features_used_in_modelling()

        except ValueError as e:
            current_app.logger.error(f"Validation Error: {e}")
            raise ValueError(f"Validation Error: {e}")
        
        if variables is None:
            raise ValueError("No variables returned.")
        else: 
            return variables

    def get_models(self):
        latest_ml_task = self.visual_ml_trainer.get_latest_ml_task()
        
        if latest_ml_task is None:
            raise ValueError("ML task not initialized")

        current_app.logger.info(f"Mltask has : {len(self.visual_ml_trainer.mltask.get_trained_models_ids())} Models")
        
        models = format_models(latest_ml_task)
        current_app.logger.info(f"models from global ML task is {models}")
        return models
    
    def get_predicted_base(self, request_json: dict):
        current_app.logger.info("Received a new request for data prediction.")
        current_app.logger.info(request_json)
        full_model_id = request_json["id"]
        train_test = request_json['trainTest']
        dataset = 'train' if train_test else 'test'
        variable = request_json['variable']

        current_app.logger.info(f"Model ID received: {full_model_id}")
        creation_args = {"data_handler": self.data_handler,
                        "model_cache": self.model_cache,
                        "full_model_id": full_model_id,
                        "variable": variable}
        predicted_base_variable = self.model_cache.get_or_create_cached_item(full_model_id, f'predicted_base_variable_{variable}', get_model_predicted_base, **creation_args)
        predicted_base_variable = predicted_base_variable[predicted_base_variable['dataset']==dataset]
        
        current_app.logger.info(f"Successfully generated predictions. Sample is {predicted_base_variable}")
        
        return predicted_base_variable.to_dict('records')
    
    def get_base_values(self, request_json: dict):
        full_model_id = request_json["id"]
        current_app.logger.info(f"Request received for base_values for {full_model_id}")

        creation_args = {"data_handler": self.data_handler,
                        "model_cache": self.model_cache,
                        "full_model_id": full_model_id}
        base_values = self.model_cache.get_or_create_cached_item(full_model_id, 'base_values_modalities_types', get_model_base_values_modalities_types, **creation_args)['base_values']
        
        current_app.logger.info(base_values)

        base_values = [{'variable': k, 'base_level': v} for k, v in base_values.items()]

        current_app.logger.info("base_values")
        current_app.logger.info(base_values)
        return base_values
    
    def get_lift_data(self, request_json: dict):
    
        current_app.logger.info("Received a new request for lift chart data.")
        full_model_id = request_json["id"]
        nb_bins = request_json["nbBins"]
        train_test = request_json["trainTest"]
        dataset = 'train' if train_test else 'test'
        
        current_app.logger.info(f"Model ID received: {full_model_id}")
        
        model_retriever = VisualMLModelRetriver(full_model_id)
        
        lift_chart = LiftChartFormatter(
                    model_retriever,
                    self.data_handler
        )
        creation_args = {"data_handler": self.data_handler,
                            "model_cache": self.model_cache,
                            "full_model_id": full_model_id}
        train_set = self.model_cache.get_or_create_cached_item(full_model_id, 'train_set', get_model_train_set, **creation_args)
        test_set = self.model_cache.get_or_create_cached_item(full_model_id, 'test_set', get_model_test_set, **creation_args)

        lift_chart_data = lift_chart.get_lift_chart(nb_bins, train_set, test_set)
        
        lift_chart_data = lift_chart_data[lift_chart_data['dataset'] == dataset]
        current_app.logger.info(f"Successfully generated Lift chart data")
        
        return lift_chart_data.to_dict('records')
    
    def get_relativities(self, request_json: dict):
        full_model_id = request_json["id"]
        
        current_app.logger.info(f"Model ID received: {full_model_id}")
        creation_args = {"data_handler": self.data_handler,
                            "model_cache": self.model_cache,
                            "full_model_id": full_model_id}
        relativities = self.model_cache.get_or_create_cached_item(full_model_id, 'relativities', get_model_relativities, **creation_args)['relativities']
        
        relativities_df = relativities.copy()
        relativities_df.columns = ['variable', 'category', 'relativity']
        current_app.logger.info(f"relativites are {relativities_df.head()}")
        return relativities_df.to_dict('records')
    
    def get_variable_level_stats(self, request_json: dict):
        current_app.logger.info("Getting Variable Level Stats")
        full_model_id = request_json["id"]
        current_app.logger.info(f"for Model ID: {full_model_id}")

        creation_args = {"data_handler": self.data_handler,
                            "model_cache": self.model_cache,
                            "full_model_id": full_model_id}
        variable_stats = self.model_cache.get_or_create_cached_item(full_model_id, 'variable_level_stats', get_model_variable_level_stats, **creation_args)
        
        current_app.logger.info(variable_stats)
        current_app.logger.info(variable_stats.columns)
        return variable_stats.to_dict('records')
    
    def get_model_metrics(self, request_json: dict):
        
        model_retriever = VisualMLModelRetriver(request_json['id'])
        model_aic = model_retriever.predictor._clf.aic_value
        model_bic  = model_retriever.predictor._clf.bic_value
        model_deviance = model_retriever.predictor._clf.deviance_value

        metrics = {
            "AIC": model_aic,
            "BIC": model_bic,
            "Deviance": model_deviance
        }
        return metrics
    
    def export_model(self, request_json: dict):
        try:
            model = request_json.get("id")
            if not model:
                current_app.logger.error("error: Model ID not provided")

            creation_args = {"data_handler": self.data_handler,
                            "model_cache": self.model_cache,
                            "full_model_id": model}
            relativities_dict = self.model_cache.get_or_create_cached_item(model, 'relativities', get_model_relativities, **creation_args)['relativities_dict']
            if not relativities_dict:
                current_app.logger.error("error: Model Cache not found for {model} cache only has {model_cache.keys()}")
            
            current_app.logger.info(f"Relativities dict for model {model} is {relativities_dict}.")
            
            nb_col = (len(relativities_dict.keys()) - 1) * 3
            variables = [col for col in relativities_dict.keys() if col != "base"]
            variable_keys = {variable: list(relativities_dict[variable].keys()) for variable in variables}
            max_len = max(len(variable_keys[variable]) for variable in variable_keys.keys())

            csv_output = ",,\n"
            csv_output += "Base,,{}\n".format(relativities_dict['base']['base'])
            csv_output += ",,\n" * 2
            csv_output += ",,,".join(variables) + ",,\n" * 2

            for i in range(max_len):
                for variable in variables:
                    if i < len(variable_keys[variable]):
                        value = sorted(variable_keys[variable])[i]
                        csv_output += "{},{},,".format(value, relativities_dict[variable][value])
                    else:
                        csv_output += ",,,"
                csv_output += "\n"
            
            relativities_interaction = self.model_cache.get_or_create_cached_item(model, 'relativities_interaction', get_model_relativities_interaction, **creation_args)
            
            if len(relativities_interaction) > 0:
                unique_interactions = relativities_interaction.groupby(['feature_1', 'feature_2']).count().reset_index()
                for _, interaction in unique_interactions.iterrows():
                    feature_1 = interaction['feature_1']
                    feature_2 = interaction['feature_2']
                    these_relativities = relativities_interaction[(relativities_interaction['feature_1']==feature_1) & (relativities_interaction['feature_2']==feature_2)]
                    csv_output += "{} * {}\n\n".format(feature_1, feature_2)
                    csv_output += ",,{}\n".format(feature_1)
                    sorted_value_1 = sorted(list(set(these_relativities['value_1'])))
                    csv_output += ",,{}\n{}".format(",".join([str(v) for v in sorted_value_1]), feature_2)
                    sorted_value_2 = sorted(list(set(these_relativities['value_2'])))
                    for value_2 in sorted_value_2:
                        csv_output += ",{},{}\n".format(str(value_2), ",".join([str(these_relativities[(these_relativities['value_1']==value_1) & (these_relativities['value_2']==value_2)]['relativity'].iloc[0]/relativities_dict[feature_1][value_1]/relativities_dict[feature_2][value_2]) for value_1 in sorted_value_1]))
                    csv_output += "\n"                    
            
            csv_data = csv_output.encode('utf-8')

        except KeyError as e:
            current_app.logger.error(f"An error occurred: {str(e)}")
            raise KeyError(f"An error occurred: {str(e)}")

        return csv_data

    def export_variable_level_stats(self, request_json: dict):
        try:
            full_model_id = request_json["id"]
            
            current_app.logger.info(f"Model ID received: {full_model_id}")
            creation_args = {"data_handler": self.data_handler,
                            "model_cache": self.model_cache,
                            "full_model_id": full_model_id}
            df = self.model_cache.get_or_create_cached_item(full_model_id, 'variable_level_stats', get_model_variable_level_stats, **creation_args)
            current_app.logger.info(df.columns)
            df.columns = ['variable', 'value', 'relativity', 'coefficient', 'p_value', 'standard_error', 'standard_error_pct', 'weight', 'weight_pct']

            csv_data = df.to_csv(index=False).encode('utf-8')

        except KeyError as e:
            current_app.logger.error(f"An error occurred: {str(e)}")
            raise KeyError(f"An error occurred: {str(e)}")

        return csv_data
    
    def export_lift_chart(self, request_json: dict):
        try:
            full_model_id = request_json["id"]
            nb_bins = request_json["nbBins"]
            train_test = request_json["trainTest"]
            dataset = 'train' if train_test else 'test'

            current_app.logger.info(f"Model ID received: {full_model_id}")
            creation_args = {"data_handler": self.data_handler,
                            "model_cache": self.model_cache,
                            "full_model_id": full_model_id}
            
            model_retriever = VisualMLModelRetriver(full_model_id)
        
            lift_chart = LiftChartFormatter(
                        model_retriever,
                        self.data_handler
            )
            creation_args = {"data_handler": self.data_handler,
                                "model_cache": self.model_cache,
                                "full_model_id": full_model_id}
            train_set = self.model_cache.get_or_create_cached_item(full_model_id, 'train_set', get_model_train_set, **creation_args)
            test_set = self.model_cache.get_or_create_cached_item(full_model_id, 'test_set', get_model_test_set, **creation_args)

            lift_chart_data = lift_chart.get_lift_chart(nb_bins, train_set, test_set)
            
            lift_chart_data = lift_chart_data[lift_chart_data['dataset'] == dataset]
            csv_data = lift_chart_data.to_csv(index=False).encode('utf-8')

        except KeyError as e:
            current_app.logger.error(f"An error occurred: {str(e)}")
            raise KeyError(f"An error occurred: {str(e)}")

        return csv_data

    def export_one_way(self, request_json: dict):
        current_app.logger.info("Exporting one way graphs")
        try:
            full_model_id = request_json["id"]
            variable = request_json["variable"]
            train_test = request_json["trainTest"]
            rescale = request_json["rescale"]
            dataset = 'test' if train_test else 'train'

            current_app.logger.info(f"Model ID received: {full_model_id}")
            current_app.logger.info(f"Variable received: {variable}")
            current_app.logger.info(f"Train/Test received: {dataset}")
            current_app.logger.info(f"Rescale received: {rescale}")

            creation_args = {"data_handler": self.data_handler,
                            "model_cache": self.model_cache,
                            "full_model_id": full_model_id, 
                            "variable": variable}
            predicted_base = self.model_cache.get_or_create_cached_item(full_model_id, f'predicted_base_variable_{variable}', get_model_predicted_base, **creation_args)
            predicted_base = predicted_base[predicted_base['dataset']==dataset]

            if rescale:
                creation_args = {"data_handler": self.data_handler,
                            "model_cache": self.model_cache,
                            "full_model_id": full_model_id}
                base_values = self.model_cache.get_or_create_cached_item(full_model_id, 'base_values_modalities_types', get_model_base_values_modalities_types, **creation_args)['base_values']
                predicted_base_denominator = predicted_base[predicted_base['Category']==base_values[variable]].iloc[0]
                predicted_base['observedAverage'] = predicted_base['observedAverage'] / predicted_base_denominator['observedAverage']
                predicted_base['fittedAverage'] = predicted_base['fittedAverage'] / predicted_base_denominator['fittedAverage']
                predicted_base['baseLevelPrediction'] = predicted_base['baseLevelPrediction'] / predicted_base_denominator['baseLevelPrediction']

            csv_data = predicted_base.to_csv(index=False).encode('utf-8')

        except KeyError as e:
            current_app.logger.error(f"An error occurred: {str(e)}")
            raise KeyError(f"An error occurred: {str(e)}")

        return csv_data
    
    def get_excluded_columns(self):
        try:
            web_app_config = get_webapp_config()
            exposure_column = web_app_config.get("exposure_column")
            target_column = web_app_config.get("target_column")
        
            cols_json = {
                "target_column": target_column,
                "exposure_column": exposure_column
            }
            return cols_json
        
        except KeyError as e:
            current_app.logger.error(f"Error retrieving target and exposure {e}")
            raise KeyError(f'Error retrieving target and exposure : {e}')
    
    def get_dataset_columns(self):
        try:
            web_app_config = get_webapp_config()
            dataset_name = web_app_config.get("training_dataset_string")
            exposure_column = web_app_config.get("exposure_column")
            
            current_app.logger.info(f"Training Dataset name selected is: {dataset_name}")
            
            df = dataiku.Dataset(dataset_name).get_dataframe(limit=100000)
            cols_json = calculate_base_levels(df, exposure_column)

            current_app.logger.info(f"Successfully retrieved column for dataset '{dataset_name}': {[col['column'] for col in cols_json]}")

            return cols_json
        
        except KeyError as e:
            current_app.logger.error(f"Error retrieving target and exposure {e}")
            raise KeyError(f'Error retrieving target and exposure : {e}')

    def update_config(self, request_json):
        webapp_id = request_json['webAppId']
        self.visual_ml_deployer._set_webapp_id(webapp_id)
        if self.visual_ml_config.create_new_analysis:
            webapp = dataiku_api.default_project.get_webapp(webapp_id)
            settings = webapp.get_settings()
            settings.get_raw()['config']['analysis_id'] = self.visual_ml_trainer.visual_ml_config.analysis_id
            settings.save()
            return {'message': 'Settings updated.'}
        else:
            return {'message': 'No need to update settings'}