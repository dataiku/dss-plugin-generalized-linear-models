from flask import Blueprint, jsonify, request, send_file, current_app, abort
import pandas as pd
import random
import re
from logging_assist.logging import logger
from backend.local_config import *
from dku_visual_ml.dku_train_model_config import DKUVisualMLConfig
from io import BytesIO
from time import time
import traceback
import dataiku
import threading
import numpy as np
import time
from dataiku.customwebapp import get_webapp_config
from chart_formatters.lift_chart import LiftChartFormatter
from .api_utils import calculate_base_levels
from backend.dataiku_api import dataiku_api
from model_cache.model_cache import ModelCache
from chart_formatters.variable_level_stats import VariableLevelStatsFormatter

is_local = False

logger.debug(f"Starting web application with is_local: {is_local}")

if not is_local:
    from backend.api_utils import format_models
    from dku_visual_ml.dku_model_trainer import VisualMLModelTrainer
    from dku_visual_ml.dku_model_retrival import VisualMLModelRetriver
    from glm_handler.dku_relativites_calculator import RelativitiesCalculator
    from glm_handler.glm_data_handler import GlmDataHandler
    
    visual_ml_config = DKUVisualMLConfig()
    data_handler = GlmDataHandler()
    visual_ml_trainer = VisualMLModelTrainer(visual_ml_config)
    
    if visual_ml_config.create_new_analysis:
        visual_ml_trainer.create_initial_ml_task()
    else:
        visual_ml_trainer.setup_using_existing_ml_task(
            visual_ml_config.analysis_id
            )

model_cache = ModelCache()

fetch_api = Blueprint("fetch_api", __name__, url_prefix="/api")

@fetch_api.route("/send_webapp_id", methods=["POST"])
def update_config():
    webapp_id = request.get_json()['webAppId']
    if visual_ml_config.create_new_analysis:
        webapp = dataiku_api.default_project.get_webapp(webapp_id)
        settings = webapp.get_settings()
        settings.get_raw()['config']['analysis_id'] = visual_ml_trainer.visual_ml_config.analysis_id
        settings.save()
        return jsonify({'message': 'Settings updated.'}), 200
    else:
        return jsonify({'message': 'No need to update settings'}), 200
    
@fetch_api.route("/train_model", methods=["POST"])
def train_model():
    current_app.logger.info(f"Initalising Model Training with request {request.get_json()}")
    
    if is_local:
        logger.info("Local set up: No model training completed")
        time.sleep(2)
        return jsonify({'message': 'Model training initiated successfully.'}), 200
    
    global visual_ml_trainer, model_cache
    
    visual_ml_config.update_model_parameters(request.get_json())

    current_app.logger.debug("Creating Visual ML Trainer")
    visual_ml_trainer.update_visual_ml_config(visual_ml_config)

    model_details, error_message = visual_ml_trainer.train_model(
        code_env_string=dataiku_api.plugin_code_env,
        session_name=visual_ml_config.model_name_string
    )
    current_app.logger.debug(f"Model error message is {error_message}")
    print(f"Model error message is {error_message}")
    current_app.logger.debug(f"Model details are {model_details}")
    
    if not error_message:
        current_app.logger.info("Model trained and cache updated")
        return jsonify({'message': 'Model training completed successfully.'}), 200
    else: 
        current_app.logger.debug("Model training error: {error_message}")
        return jsonify({'error': str(error_message)}), 500

    
    
@fetch_api.route("/get_latest_mltask_params", methods=["POST"])
def get_latest_mltask_params():
    current_app.logger.info("Getting Latest ML task set up parameters")
    request_json = request.get_json()
    full_model_id = request_json["id"]
    
    if is_local:
        if full_model_id== "model_interaction":
            setup_params = interaction_setup_params
        else:
            setup_params = random.choice([dummy_setup_params, dummy_setup_params_2])
        current_app.logger.info(f"Returning Params {setup_params}")
        return jsonify(setup_params)
    
    current_app.logger.info(f"Recieved request for latest params for: {full_model_id}")
    
    model_retriver = VisualMLModelRetriver(full_model_id)
    setup_params = model_retriver.get_setup_params()
   
    current_app.logger.info(f"Returning setup params {setup_params}")
    return jsonify(setup_params)

@fetch_api.route("/variables", methods=["POST"])
def get_variables():
    if is_local:
        return jsonify(dummy_variables)
    
    request_json = request.get_json()
    full_model_id = request_json["id"]
    try:
        model_retriever = VisualMLModelRetriver(full_model_id)
        variables = model_retriever.get_features_used_in_modelling()

    except ValueError as e:
        current_app.logger.error(f"Validation Error: {e}")
        return jsonify({"error": e})        
    except Exception as e:
        current_app.logger.error(f"An error occurred: {e}")
        return jsonify({"error": e})    
        
    if variables is None:
            raise ValueError("No variables returned.")
    else: return jsonify(variables)

@fetch_api.route("/models", methods=["GET"])
def get_models():
    if is_local:
        return jsonify(dummy_models)
    
    latest_ml_task = visual_ml_trainer.get_latest_ml_task()
    
    if latest_ml_task is None:
        return jsonify({'error': 'ML task not initialized'}), 500
    try:
        current_app.logger.info(f"Mltask has : {len(visual_ml_trainer.mltask.get_trained_models_ids())} Models")
        
        models = format_models(latest_ml_task)
        current_app.logger.info(f"models from global ML task is {models}")
        return jsonify(models)
    except Exception as e:
        current_app.logger.exception("An error occurred while retrieving models")
        return jsonify({'error': str(e)}), 500



@fetch_api.route("/data", methods=["POST"])
def get_data():
    if is_local:
        import time
        time.sleep(1)
        request_json = request.get_json()
        variable = request_json['variable']
        dummy_df_variable = dummy_df_data[dummy_df_data['definingVariable'] == variable]
        return jsonify(dummy_df_variable.to_dict('records'))
    try:
        current_app.logger.info("Received a new request for data prediction.")
        request_json = request.get_json()
        current_app.logger.info(request_json)
        full_model_id = request_json["id"]
        train_test = request_json['trainTest']
        dataset = 'test' if train_test else 'train'
        variable = request_json['variable']

        current_app.logger.info(f"Model ID received: {full_model_id}")
        predicted_base_variable = get_model_predicted_base(full_model_id, variable)
        predicted_base_variable = predicted_base_variable[predicted_base_variable['dataset']==dataset]
        
        current_app.logger.info(f"Successfully generated predictions. Sample is {predicted_base_variable}")
        
        return jsonify(predicted_base_variable.to_dict('records'))
        
    except Exception as e:
        current_app.logger.error(f"An error occurred while processing the request: {e}", exc_info=True)
        return jsonify({"error": "An error occurred during data processing."}), 500


def get_model_predicted_base(full_model_id, variable):
    
    train_set = get_model_train_set(full_model_id)
    test_set = get_model_test_set(full_model_id)
    base_values = get_model_base_values(full_model_id)
    modalities = get_model_modalities(full_model_id)
    variable_types = get_model_variable_types(full_model_id)
    if full_model_id in model_cache.list_models():
        model = model_cache.get_model(full_model_id)
        if 'predicted_and_base' in model.keys():
            predicted_base = model.get('predicted_and_base')
            if variable in predicted_base.keys():
                predicted_base_variable = predicted_base.get(variable)
            else:
                model_retriever = VisualMLModelRetriver(full_model_id)
                relativities_calculator = RelativitiesCalculator(data_handler, model_retriever, train_set, test_set, base_values, modalities, variable_types)
                predicted_base_variable = relativities_calculator.get_formated_predicted_base_variable(variable)
                predicted_base[variable] = predicted_base_variable
        else:
            model_retriever = VisualMLModelRetriver(full_model_id)
            relativities_calculator = RelativitiesCalculator(data_handler, model_retriever, train_set, test_set, base_values, modalities, variable_types)
            predicted_base_variable = relativities_calculator.get_formated_predicted_base_variable(variable)
            model_cache.add_model_object(full_model_id, 'predicted_and_base', {variable: predicted_base_variable})
    else:
        model_retriever = VisualMLModelRetriver(full_model_id)
        relativities_calculator = RelativitiesCalculator(data_handler, model_retriever, train_set, test_set, base_values, modalities, variable_types)
        predicted_base_variable = relativities_calculator.get_formated_predicted_base(variable)
        model_cache.add_model_object(full_model_id, 'predicted_and_base', {variable: predicted_base_variable})
    
    return predicted_base_variable

@fetch_api.route("/base_values", methods=["POST"])
def get_base_values():
    request_json = request.get_json()
    full_model_id = request_json["id"]
    current_app.logger.info(f"Request recieved for base_values for {full_model_id}")
        
    if is_local:
        current_app.logger.info("Running Locally")
        return jsonify(dummy_base_values)
    try:
        
        base_values = get_model_base_values(full_model_id)
        
        base_values = [{'variable': k, 'base_level': v} for k, v in base_values.items()]

        current_app.logger.info("base_values")
        current_app.logger.info(base_values)
        return jsonify(base_values)
    
    except Exception as e:
        current_app.logger.error(f"An error occurred while processing the request: {e}", exc_info=True)
        return jsonify({"error": "An error occurred during data processing."}), 500

def get_model_base_values(full_model_id):
    logger.info("get model base values")
    if full_model_id in model_cache.list_models():
        model = model_cache.get_model(full_model_id)
        if 'base_values' in model.keys():
            base_values = model_cache.get_model(full_model_id).get('base_values')
        else:
            train_set = get_model_train_set(full_model_id)
            test_set = get_model_test_set(full_model_id)
            model_retriever = VisualMLModelRetriver(full_model_id)
            relativities_calculator = RelativitiesCalculator(data_handler, model_retriever, train_set, test_set)
            base_values = relativities_calculator.get_base_values()        
            model_cache.add_model_object(full_model_id, 'base_values', base_values)
            model_cache.add_model_object(full_model_id, 'modalities', relativities_calculator.modalities)
            model_cache.add_model_object(full_model_id, 'variable_types', relativities_calculator.variable_types)
    else:
        train_set = get_model_train_set(full_model_id)
        test_set = get_model_test_set(full_model_id)
        model_retriever = VisualMLModelRetriver(full_model_id)
        relativities_calculator = RelativitiesCalculator(data_handler, model_retriever, train_set, test_set)
        base_values = relativities_calculator.get_base_values()        
        model_cache.add_model_object(full_model_id, 'base_values', base_values)
        model_cache.add_model_object(full_model_id, 'modalities', relativities_calculator.modalities)
        model_cache.add_model_object(full_model_id, 'variable_types', relativities_calculator.variable_types)
    
    return base_values


def get_model_modalities(full_model_id):
    logger.info("get model modalities")
    model = model_cache.get_model(full_model_id)
    modalities = model.get('modalities')
    return modalities

def get_model_variable_types(full_model_id):
    logger.info("get model variable types")
    model = model_cache.get_model(full_model_id)
    variable_types = model.get('variable_types')
    return variable_types


@fetch_api.route("/lift_data", methods=["POST"])
def get_lift_data():
    
    if is_local:
        return jsonify(dummy_lift_data.to_dict('records'))
    
    current_app.logger.info("Received a new request for lift chart data.")
    
    request_json = request.get_json()
    full_model_id = request_json["id"]
    nb_bins = request_json["nbBins"]
    train_test = request_json["trainTest"]
    dataset = 'test' if train_test else 'train'
    
    current_app.logger.info(f"Model ID received: {full_model_id}")
    
    model_retriever = VisualMLModelRetriver(full_model_id)
    
    lift_chart = LiftChartFormatter(
                model_retriever,
                data_handler
    ) 
    train_set = get_model_train_set(full_model_id)
    test_set = get_model_test_set(full_model_id)

    lift_chart_data = lift_chart.get_lift_chart(nb_bins, train_set, test_set)
    
    lift_chart_data = lift_chart_data[lift_chart_data['dataset'] == dataset]
    current_app.logger.info(f"Successfully generated Lift chart data")
    
    return jsonify(lift_chart_data.to_dict('records'))

@fetch_api.route("/relativities", methods=["POST"])
def get_relativities():
    if is_local:
        return jsonify(dummy_relativites.to_dict('records'))
    request_json = request.get_json()
    full_model_id = request_json["id"]
    
    current_app.logger.info(f"Model ID received: {full_model_id}")
    relativities = get_model_relativities(full_model_id)
    
    relativities_df = relativities.copy()
    relativities_df.columns = ['variable', 'category', 'relativity']
    current_app.logger.info(f"relativites are {relativities_df.head()}")
    return jsonify(relativities_df.to_dict('records'))

def get_model_train_set(full_model_id):
    logger.info("get model train set")
    if full_model_id in model_cache.list_models():
        model = model_cache.get_model(full_model_id)
        logger.info(model.keys())
        if 'train_set' in model.keys():
            train_set = model_cache.get_model(full_model_id).get('train_set')
        else:
            model_retriever = VisualMLModelRetriver(full_model_id)
            relativities_calculator = RelativitiesCalculator(data_handler, model_retriever)
            train_set = relativities_calculator.train_set
            model_cache.add_model_object(full_model_id, 'train_set', train_set)
    else:
        model_retriever = VisualMLModelRetriver(full_model_id)
        relativities_calculator = RelativitiesCalculator(data_handler, model_retriever)
        train_set = relativities_calculator.train_set
        model_cache.add_model_object(full_model_id, 'train_set', train_set)
    
    return train_set


def get_model_test_set(full_model_id):
    logger.info("get model test set")
    if full_model_id in model_cache.list_models():
        model = model_cache.get_model(full_model_id)
        if 'test_set' in model.keys():
            test_set = model_cache.get_model(full_model_id).get('test_set')
        else:
            model_retriever = VisualMLModelRetriver(full_model_id)
            relativities_calculator = RelativitiesCalculator(data_handler, model_retriever)
            test_set = relativities_calculator.test_set
            model_cache.add_model_object(full_model_id, 'test_set', test_set)
    else:
        model_retriever = VisualMLModelRetriver(full_model_id)
        relativities_calculator = RelativitiesCalculator(data_handler, model_retriever)
        test_set = relativities_calculator.test_set
        model_cache.add_model_object(full_model_id, 'test_set', test_set)
    
    return test_set

def get_model_relativities(full_model_id):
    logger.info("get model relativities")
    if full_model_id in model_cache.list_models():
        model = model_cache.get_model(full_model_id)
        if 'relativities' in model.keys():
            relativities = model_cache.get_model(full_model_id).get('relativities')
        else:
            train_set = get_model_train_set(full_model_id)
            test_set = get_model_test_set(full_model_id)
            base_values = get_model_base_values(full_model_id)
            modalities = get_model_modalities(full_model_id)
            variable_types = get_model_variable_types(full_model_id)
            model_retriever = VisualMLModelRetriver(full_model_id)
            relativities_calculator = RelativitiesCalculator(data_handler, model_retriever, train_set, test_set, base_values=base_values, modalities=modalities, variable_types=variable_types)
            relativities = relativities_calculator.get_relativities_df()
            relativities_dict = relativities_calculator.relativities
            model_cache.add_model_object(full_model_id, 'relativities', relativities)
            model_cache.add_model_object(full_model_id, 'relativities_dict', relativities_dict)
    else:
        train_set = get_model_train_set(full_model_id)
        test_set = get_model_test_set(full_model_id)
        base_values = get_model_base_values(full_model_id)
        modalities = get_model_modalities(full_model_id)
        variable_types = get_model_variable_types(full_model_id)
        model_retriever = VisualMLModelRetriver(full_model_id)
        relativities_calculator = RelativitiesCalculator(data_handler, model_retriever, train_set, test_set, base_values=base_values, modalities=modalities, variable_types=variable_types)
        relativities = relativities_calculator.get_relativities_df()
        model_cache.add_model_object(full_model_id, 'relativities', relativities)
        relativities_dict = relativities_calculator.relativities
        model_cache.add_model_object(full_model_id, 'relativities_dict', relativities_dict)
    
    return relativities


def get_model_relativities_interaction(full_model_id):
    if full_model_id in model_cache.list_models():
        model = model_cache.get_model(full_model_id)
        if 'relativities_interaction' in model.keys():
            relativities_interaction = model_cache.get_model(full_model_id).get('relativities_interaction')
        else:
            train_set = get_model_train_set(full_model_id)
            test_set = get_model_test_set(full_model_id)
            base_values = get_model_base_values(full_model_id)
            modalities = get_model_modalities(full_model_id)
            variable_types = get_model_variable_types(full_model_id)
            model_retriever = VisualMLModelRetriver(full_model_id)
            relativities_calculator = RelativitiesCalculator(data_handler, model_retriever, train_set, test_set, base_values=base_values, modalities=modalities, variable_types=variable_types)
            relativities_interaction = relativities_calculator.get_relativities_interactions_df()
            model_cache.add_model_object(full_model_id, 'relativities_interaction', relativities_interaction)
    else:
        train_set = get_model_train_set(full_model_id)
        test_set = get_model_test_set(full_model_id)
        base_values = get_model_base_values(full_model_id)
        modalities = get_model_modalities(full_model_id)
        variable_types = get_model_variable_types(full_model_id)
        model_retriever = VisualMLModelRetriver(full_model_id)
        relativities_calculator = RelativitiesCalculator(data_handler, model_retriever, train_set, test_set, base_values=base_values, modalities=modalities, variable_types=variable_types)
        relativities_interaction = relativities_calculator.get_relativities_interactions_df()
        model_cache.add_model_object(full_model_id, 'relativities_interaction', relativities_interaction)
    
    return relativities_interaction


@fetch_api.route("/get_variable_level_stats", methods=["POST"])
def get_variable_level_stats():
    current_app.logger.info("Getting Variable Level Stats")
    if is_local:
        return jsonify(dummy_variable_level_stats)
    
    request_json = request.get_json()
    full_model_id = request_json["id"]
    current_app.logger.info(f"for Model ID: {full_model_id}")

    variable_stats = get_model_variable_stats(full_model_id)
    
    return jsonify(variable_stats.to_dict('records'))

def get_model_variable_stats(full_model_id):
    
    if full_model_id in model_cache.list_models():
        model = model_cache.get_model(full_model_id)
        if 'variable_stats' in model.keys():
            variable_stats = model_cache.get_model(full_model_id).get('variable_stats')
        else:
            train_set = get_model_train_set(full_model_id)
            test_set = get_model_test_set(full_model_id)
            model_retriever = VisualMLModelRetriver(full_model_id)
            relativities = get_model_relativities(full_model_id)
            relativities_interaction = get_model_relativities_interaction(full_model_id)
            base_values = get_model_base_values(full_model_id)
            variable_level_stats = VariableLevelStatsFormatter(model_retriever, data_handler, relativities, relativities_interaction, base_values, train_set, test_set)
            variable_stats = variable_level_stats.get_variable_level_stats()
            model_cache.add_model_object(full_model_id, 'variable_stats', variable_stats)
    else:
        train_set = get_model_train_set(full_model_id)
        test_set = get_model_test_set(full_model_id)
        model_retriever = VisualMLModelRetriver(full_model_id)
        relativities = get_model_relativities(full_model_id)
        relativities_interaction = get_model_relativities_interaction(full_model_id)
        base_values = get_model_base_values(full_model_id)
        variable_level_stats = VariableLevelStatsFormatter(model_retriever, data_handler, relativities, relativities_interaction, base_values, train_set, test_set)
        variable_stats = variable_level_stats.get_variable_level_stats()
        model_cache.add_model_object(full_model_id, 'variable_stats', variable_stats)
        
    return variable_stats




@fetch_api.route("/get_model_comparison_data", methods=["POST"])
def get_model_comparison_data():
    request_json = request.get_json()
    current_app.logger.info(f"Model Comparison Data recieved the following json {request_json}")
    if is_local:
        df = get_dummy_model_comparison_data()
        current_app.logger.info(f"Returning Merged Model stats as {df.head().to_string()}") 
        return jsonify(df.to_dict('records'))

    try:
        model1, model2, selectedVariable = request_json["model1"], request_json["model2"]
        variable = request_json["selectedVariable"]
        train_test = request_json["trainTest"]
        dataset = 'test' if train_test else 'train'

        current_app.logger.info(f"Retrieving {model1} from the cache")
        model_1_predicted_base = get_model_predicted_base(model1, variable)
        model_1_predicted_base = model_1_predicted_base[model_1_predicted_base['dataset']==dataset]
        current_app.logger.info(f"Successfully retrieved {model1} from the cache")
        
        current_app.logger.info(f"Retrieving {model2} from the cache")
        model_2_predicted_base = get_model_predicted_base(model2, variable)
        model_2_predicted_base = model_2_predicted_base[model_2_predicted_base['dataset']==dataset]
        current_app.logger.info(f"Successfully retrieved {model2} from the cache")
        model_1_predicted_base = model_1_predicted_base.rename(columns={
            'observedAverage': 'model_1_observedAverage',
            'fittedAverage': 'model_1_fittedAverage',
            'baseLevelPrediction': 'model1_baseLevelPrediction'
        })

        model_2_predicted_base = model_2_predicted_base.rename(columns={
            'observedAverage': 'model_2_observedAverage',
            'fittedAverage': 'model_2_fittedAverage',
            'baseLevelPrediction': 'model2_baseLevelPrediction'
        })
        merged_model_stats = pd.merge(model_1_predicted_base, model_2_predicted_base, 
                                      on=['definingVariable', 'Category', 'Value'], 
                                      how='outer')
        
        
        merged_model_stats = merged_model_stats[merged_model_stats.definingVariable == selectedVariable]
        current_app.logger.info(f"Returning Merged Model stats as {merged_model_stats.head()}")
        return jsonify(merged_model_stats.to_dict('records'))
    
    except Exception as e:
        current_app.logger.error(f"An error occurred: {str(e)}")
        return jsonify({"error": str(e)}), 500

@fetch_api.route("/get_model_metrics", methods=["POST"])
def get_model_metrics():
    if is_local:
        return jsonify(dummy_model_metrics)
    
    request_json = request.get_json()
    
    model_retriever = VisualMLModelRetriver(request_json['id'])
    model_aic = model_retriever.predictor._clf.aic_value
    model_bic  = model_retriever.predictor._clf.bic_value
    model_deviance = model_retriever.predictor._clf.deviance_value

    metrics = {
        "AIC": model_aic,
        "BIC": model_bic,
        "Deviance": model_deviance
    }
    return jsonify(metrics)



@fetch_api.route('/export_model', methods=['POST'])
def export_model():

    if is_local:
        data = {'Name': ['John', 'Alice', 'Bob'], 'Age': [30, 25, 35]}
        df = pd.DataFrame(data)

        # Convert DataFrame to CSV format
        csv_data = df.to_csv(index=False).encode('utf-8')
    else:
        try:
            request_json = request.get_json()
            model = request_json.get("id")
            if not model:
                current_app.logger.error("error: Model ID not provided")

            relativities_dict = model_cache.get_model(model).get('relativities_dict')
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
            
            variable_stats = get_model_variable_stats(model)
            relativities_interaction = get_model_relativities_interaction(model)
            
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

    csv_io = BytesIO(csv_data)

    # Serve the CSV file for download
    return send_file(
        csv_io,
        mimetype='text/csv',
        as_attachment=True,
        download_name='model.csv'
    )


@fetch_api.route('/export_variable_level_stats', methods=['POST'])
def export_variable_level_stats():

    if is_local:


        # Convert DataFrame to CSV format
        csv_data = df.to_csv(index=False).encode('utf-8')
    else:
        try:
            request_json = request.get_json()
            full_model_id = request_json["id"]
            
            current_app.logger.info(f"Model ID received: {full_model_id}")

            df = get_model_variable_stats(full_model_id)
            df.columns = ['variable', 'value', 'relativity', 'coefficient', 'standard_error', 'standard_error_pct', 'weight', 'weight_pct']

            csv_data = df.to_csv(index=False).encode('utf-8')

        except KeyError as e:
            current_app.logger.error(f"An error occurred: {str(e)}")

    csv_io = BytesIO(csv_data)

    # Serve the CSV file for download
    return send_file(
        csv_io,
        mimetype='text/csv',
        as_attachment=True,
        download_name='variable_level_stats.csv'
    )


@fetch_api.route('/export_one_way', methods=['POST'])
def export_one_way():
    current_app.logger.info("Exporting one way graphs")
    if is_local:
        csv_data = variable_level_stats_df.to_csv(index=False).encode('utf-8')
    else:
        try:
            request_json = request.get_json()
            full_model_id = request_json["id"]
            variable = request_json["variable"]
            train_test = request_json["trainTest"]
            rescale = request_json["rescale"]
            dataset = 'test' if train_test else 'train'

            current_app.logger.info(f"Model ID received: {full_model_id}")
            current_app.logger.info(f"Variable received: {variable}")
            current_app.logger.info(f"Train/Test received: {dataset}")
            current_app.logger.info(f"Rescale received: {rescale}")

            predicted_base = get_model_predicted_base(full_model_id, variable)
            predicted_base = predicted_base[predicted_base['dataset']==dataset]

            if rescale:
                base_values = get_model_base_values(full_model_id)
                predicted_base_denominator = predicted_base[predicted_base['Category']==base_values[variable]].iloc[0]
                predicted_base['observedAverage'] = predicted_base['observedAverage'] / predicted_base_denominator['observedAverage']
                predicted_base['fittedAverage'] = predicted_base['fittedAverage'] / predicted_base_denominator['fittedAverage']
                predicted_base['baseLevelPrediction'] = predicted_base['baseLevelPrediction'] / predicted_base_denominator['baseLevelPrediction']

            csv_data = predicted_base.to_csv(index=False).encode('utf-8')

        except KeyError as e:
            current_app.logger.error(f"An error occurred: {str(e)}")

    csv_io = BytesIO(csv_data)

    # Serve the CSV file for download
    return send_file(
        csv_io,
        mimetype='text/csv',
        as_attachment=True,
        download_name='variable_level_stats.csv'
    )

@fetch_api.route("/get_excluded_columns", methods=["GET"])
def get_excluded_columns():
    try:
        if is_local:
            exposure_column = "Exposure"
            target_column = "ClaimAmount"
        else:
            web_app_config = get_webapp_config()
            exposure_column = web_app_config.get("exposure_column")
            target_column = web_app_config.get("target_column")
        
        cols_json = {
            "target_column": target_column,
            "exposure_column": exposure_column
        }
        return jsonify(cols_json)
    
    except KeyError as e:
        current_app.logger.error(f"Error retrieving target and exposure {e}")
        return jsonify({'error': f'Error retrieving target and exposure : {e}'}), 400
    
    

@fetch_api.route("/get_dataset_columns", methods=["GET"])
def get_dataset_columns():
    try:
        if is_local:
            dataset_name = "claim_train"
            exposure_column = "exposure"
        else:
            web_app_config = get_webapp_config()
            dataset_name = web_app_config.get("training_dataset_string")
            exposure_column = web_app_config.get("exposure_column")
            
        current_app.logger.info(f"Training Dataset name selected is: {dataset_name}")
        
        df = dataiku.Dataset(dataset_name).get_dataframe(limit=100000)
        cols_json = calculate_base_levels(df, exposure_column)

        current_app.logger.info(f"Successfully retrieved column for dataset '{dataset_name}': {[col['column'] for col in cols_json]}")

        return jsonify(cols_json)
    
    except KeyError as e:
        current_app.logger.error(f"Missing key in request: {e}")
        return jsonify({'error': f'Missing key in request: {e}'}), 400
    
    except Exception as e:
        current_app.logger.exception(f"Error retrieving columns for dataset '{dataset_name}': {e}")
        return jsonify({'error': str(e)}), 500
    
@fetch_api.route("/get_train_dataset_column_names", methods=["GET"])
def get_train_dataset_column_names():
    try:
        if is_local:
            dataset_name = "claim_train"
        else:
            dataset_name = visual_ml_config.input_dataset

        current_app.logger.debug(f"Training Dataset name for colum retrival is: {dataset_name}")
        cols_dict = dataiku.Dataset(dataset_name).get_config().get('schema').get('columns')
        column_names = [column['name'] for column in cols_dict]

        current_app.logger.info(f"Successfully retrieved column names for dataset '{dataset_name}': {column_names}")

        return jsonify(column_names)

    except Exception as e:
        current_app.logger.exception(f"Error retrieving columns for dataset '{dataset_name}': {e}")
        return jsonify({'error': str(e)}), 500
