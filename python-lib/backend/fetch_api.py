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

visual_ml_trainer = model_cache = model_deployer =relativities_calculator = None
is_local = False

logger.debug(f"Starting web application with is_local: {is_local}")

if not is_local:
    from backend.api_utils import format_models
    from dku_visual_ml.dku_model_trainer import VisualMLModelTrainer
    from dku_visual_ml.dku_model_retrival import VisualMLModelRetriver
    from glm_handler.dku_relativites_calculator import RelativitiesCalculator
    from glm_handler.dku_model_deployer import ModelDeployer
    from glm_handler.glm_data_handler import GlmDataHandler
    from backend.model_cache import setup_model_cache, update_model_cache
    
    visual_ml_config = DKUVisualMLConfig()
    data_handler = GlmDataHandler()
    visual_ml_trainer = VisualMLModelTrainer(visual_ml_config)
    
    if visual_ml_config.create_new_analysis:
        visual_ml_trainer.create_initial_ml_task()
        web_app_config.get_raw()['analysis_id'] = ''
        logger.info(f"Created new analysis {visual_ml_config.experiment_name}")
        abort(500, description=f"Created new analysis {visual_ml_config.experiment_name}. Now select and restart backend")
    else:
        visual_ml_trainer.setup_using_existing_ml_task(
            visual_ml_config.existing_analysis_id
            )
        full_model_id = visual_ml_trainer.mltask.get_trained_models_ids()[0]
        model_retriever = VisualMLModelRetriver(full_model_id)
        relativities_calculator = RelativitiesCalculator(
            data_handler,
            model_retriever
        )
    
        
def setup_cache():
    global model_cache
    latest_ml_task = visual_ml_trainer.get_latest_ml_task()
    model_cache = setup_model_cache(latest_ml_task)

loading_thread = threading.Thread(target=setup_cache)
loading_thread.start()


fetch_api = Blueprint("fetch_api", __name__, url_prefix="/api")


    
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
    loading_thread.join()
    if not error_message:
        if not model_cache:
            current_app.logger.info("Creating Model cache For the first time")
            latest_ml_task = visual_ml_trainer.get_latest_ml_task()
            model_deployer = visual_ml_trainer.model_deployer
            model_cache = setup_model_cache(latest_ml_task, model_deployer)
        else:
            latest_ml_task = visual_ml_trainer.get_latest_ml_task()
            model_cache = update_model_cache(latest_ml_task, model_cache)

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
        loading_thread.join()
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
    
    loading_thread.join()
    latest_ml_task = visual_ml_trainer.get_latest_ml_task()
    
    if latest_ml_task is None:
        web_app_config = get_webapp_config()
        visual_ml_trainer.update_visual_ml_config(visual_ml_config)
        visual_ml_trainer.ml_task = visual_ml_trainer.create_inital_ml_task(web_app_config.get("target_column"))
        latest_ml_task = visual_ml_trainer.get_latest_ml_task()
    
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
        return jsonify(dummy_df_data.to_dict('records'))
    try:
        loading_thread.join()
        current_app.logger.info("Received a new request for data prediction.")
        request_json = request.get_json()
        full_model_id = request_json["id"]
        train_test = request_json['trainTest']
        dataset = 'test' if train_test else 'train'

        current_app.logger.info(f"Model ID received: {full_model_id}")
        predicted_base = model_cache.get_model(full_model_id).get('predicted_and_base')
        predicted_base = predicted_base[predicted_base['dataset']==dataset]

        current_app.logger.info(f"Successfully generated predictions. Sample is {predicted_base.head()}")
        
        return jsonify(predicted_base.to_dict('records'))
    
    except Exception as e:
        current_app.logger.error(f"An error occurred while processing the request: {e}", exc_info=True)
        return jsonify({"error": "An error occurred during data processing."}), 500

@fetch_api.route("/base_values", methods=["POST"])
def get_base_values():
    request_json = request.get_json()
    full_model_id = request_json["id"]
    current_app.logger.info(f"Request recieved for base_values for {full_model_id}")
        
    if is_local:
        current_app.logger.info("Running Locally")
        return jsonify(dummy_base_values)
    try:
        loading_thread.join()
        
        base_values = model_cache.get_model(full_model_id).get('base_values')
        
        base_values = [{'variable': k, 'base_level': v} for k, v in base_values.items()]

        current_app.logger.info("base_values")
        current_app.logger.info(base_values)
        return jsonify(base_values)
    
    except Exception as e:
        current_app.logger.error(f"An error occurred while processing the request: {e}", exc_info=True)
        return jsonify({"error": "An error occurred during data processing."}), 500


@fetch_api.route("/lift_data", methods=["POST"])
def get_lift_data():
    
    if is_local:
        return jsonify(dummy_lift_data.to_dict('records'))
    
    current_app.logger.info("Received a new request for lift chart data.")
    
    loading_thread.join()
    request_json = request.get_json()
    full_model_id = request_json["id"]
    nb_bins = request_json["nbBins"]
    train_test = request_json["trainTest"]
    dataset = 'test' if train_test else 'train'
    
    current_app.logger.info(f"Model ID received: {full_model_id}")
    
    lift_chart_data = model_cache.get_model(full_model_id).get('lift_chart_data')
    
    current_nb_bins = len(lift_chart_data[lift_chart_data['dataset'] == dataset])
    
    if current_nb_bins != nb_bins:
        model_retriever = VisualMLModelRetriver(full_model_id)
        
        lift_relativites_calculator = RelativitiesCalculator(
            data_handler,
            model_retriever)
        
        current_app.logger.info(f"Relativies calculator is: {lift_relativites_calculator}")
        current_app.logger.info(f"Relativies calculator train is : {len(lift_relativites_calculator.train_set)}")
        
        lift_chart = LiftChartFormatter(
                 model_retriever,
                 data_handler
        ) 
        train_set = lift_relativites_calculator.train_set
        test_set = lift_relativites_calculator.test_set

        if train_set is None:
            raise ValueError("Train set is not defined in relativities_calculator")
        if test_set is None:
            raise ValueError("Test set is not defined in relativities_calculator")

        lift_chart_data = lift_chart.get_lift_chart(nb_bins, train_set, test_set)
        
#          model_cache.add_model(full_model_id).get('lift_chart_data') = lift_chart_data
    
    lift_chart_data = lift_chart_data[lift_chart_data['dataset'] == dataset]
    current_app.logger.info(f"Successfully generated Lift chart data")
    
    return jsonify(lift_chart_data.to_dict('records'))



@fetch_api.route("/update_bins", methods=["POST"])
def get_updated_data(): 
    if is_local:
        return jsonify(dummy_get_updated_data.to_dict('records'))
    request_json = request.get_json()

    feature = request_json["feature"]
    nb_bins = request_json["nbBin"]
    predicted_base = relativities_calculator.get_predicted_and_base_feature(feature, nb_bins)
    df = predicted_base.copy()
    df.columns = ['definingVariable', 'Category', 'observedAverage', 'fittedAverage', 'Value', 'baseLevelPrediction']
    
    
    return jsonify(df.to_dict('records'))
#     local dev
    return jsonify(dummy_get_updated_data.to_dict('records'))


@fetch_api.route("/relativities", methods=["POST"])
def get_relativities():
    if is_local:
        return jsonify(dummy_relativites.to_dict('records'))
    loading_thread.join()
    request_json = request.get_json()
    full_model_id = request_json["id"]
    
    current_app.logger.info(f"Model ID received: {full_model_id}")
    df = model_cache.get_model(full_model_id).get('relativities')
    df.columns = ['variable', 'category', 'relativity']
    current_app.logger.info(f"relativites are {df.head()}")
    return jsonify(df.to_dict('records'))


@fetch_api.route("/get_variable_level_stats", methods=["POST"])
def get_variable_level_stats():
    current_app.logger.info("Getting Variable Level Stats")
    if is_local:
        return jsonify(dummy_variable_level_stats)
    
    loading_thread.join()
    request_json = request.get_json()
    full_model_id = request_json["id"]
    current_app.logger.info(f"for Model ID: {full_model_id}")


    df = model_cache.get_model(full_model_id).get('variable_stats')
    return jsonify(df.to_dict('records'))



@fetch_api.route("/get_model_comparison_data", methods=["POST"])
def get_model_comparison_data():
    request_json = request.get_json()
    current_app.logger.info(f"Model Comparison Data recieved the following json {request_json}")
    if is_local:
        df = get_dummy_model_comparison_data()
        current_app.logger.info(f"Returning Merged Model stats as {df.head().to_string()}") 
        return jsonify(df.to_dict('records'))

    try:
        model1, model2, selectedVariable = request_json["model1"], request_json["model2"], request_json["selectedVariable"]
        train_test = request_json["trainTest"]
        dataset = 'test' if train_test else 'train'

        loading_thread.join()
        current_app.logger.info(f"Retrieving {model1} from the cache")
        model_1_predicted_base = model_cache.get_model(model1).get('predicted_and_base')
        model_1_predicted_base = model_1_predicted_base[model_1_predicted_base['dataset']==dataset]
        current_app.logger.info(f"Successfully retrieved {model1} from the cache")
        
        current_app.logger.info(f"Retrieving {model2} from the cache")
        model_2_predicted_base = model_cache.get_model(model2).get('predicted_and_base')
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
    
    loading_thread.join()
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
            loading_thread.join()
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
            
            variable_stats = model_cache.get_model(model).get('variable_stats')
            relativities_interaction = model_cache.get_model(model).get('relativities_interaction')
            
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
            loading_thread.join()
            request_json = request.get_json()
            full_model_id = request_json["id"]
            
            current_app.logger.info(f"Model ID received: {full_model_id}")

            df = model_cache.get_model(full_model_id).get('variable_stats')
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
            loading_thread.join()
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

            predicted_base = model_cache.get_model(full_model_id).get('predicted_and_base')
            predicted_base = predicted_base[predicted_base['dataset']==dataset]
            predicted_base = predicted_base[predicted_base['definingVariable']==variable]

            if rescale:
                base_values = model_cache.get_model(full_model_id).get('base_values')
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
        
        df = dataiku.Dataset(dataset_name).get_dataframe()
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
