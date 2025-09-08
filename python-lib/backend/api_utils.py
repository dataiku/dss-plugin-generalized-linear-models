import re
from logging_assist.logging import logger
from model_cache.model_conformity_checker import ModelConformityChecker
from .dataiku_api import dataiku_api
import pandas as pd
from dku_visual_ml.dku_model_retrival import VisualMLModelRetriver
from glm_handler.dku_relativites_calculator import RelativitiesCalculator
from chart_formatters.variable_level_stats import VariableLevelStatsFormatter

def format_models(global_dku_mltask):
    logger.info("Formatting Models")
    model_id_pattern = r'\((.*?)\)'
    mcc = ModelConformityChecker()

    list_ml_id = global_dku_mltask.get_trained_models_ids()
    project_key = dataiku_api.default_project.project_key
    ml_task_id = global_dku_mltask.mltask_id
    analysis_id = global_dku_mltask.analysis_id
    models = []
    for ml_id in list_ml_id:
        model_details = global_dku_mltask.get_trained_model_details(ml_id)
        is_conform = mcc.check_model_conformity(ml_id)
        if is_conform:
            model_name = model_details.get_user_meta()['name']
            matches = re.findall(model_id_pattern, model_name)
            date = [v['value'] for v in model_details.get_user_meta()['labels'] if v['key'] == 'model:date'][0]
            models.append({"id": ml_id, "name": matches[0], "date": date, "project_key": project_key, "ml_task_id": ml_task_id, "analysis_id": analysis_id})
        else:
            logger.info(f"model {ml_id} is not conform")
    return models

def natural_sort_key(s):
    import re
    return [int(c) if c.isdigit() else c.lower() for c in re.split(r'(\d+)', str(s))]

def calculate_base_levels(df, exposure_column=None):
    cols_json = []
    # Sort the columns using natural sorting
    sorted_columns = sorted(df.columns, key=natural_sort_key)
    
    for col in sorted_columns:
        if col == exposure_column:
            continue
        
        # Determine if the column contains numeric or non-numeric data
        is_numeric = pd.api.types.is_numeric_dtype(df[col])
        
        if is_numeric:
            options = sorted([str(val) for val in df[col].unique()], key=float)
        else:
            options = sorted([str(val) for val in df[col].unique()], key=natural_sort_key)
        
        if exposure_column and exposure_column in df.columns:
            # Exposure-based calculation
            weighted_counts = df.groupby(col)[exposure_column].sum()
            base_level = str(weighted_counts.idxmax())
        else:
            # Original mode-based calculation
            base_level = str(df[col].mode().iloc[0])
        
        cols_json.append({
            'column': col,
            'options': options,
            'baseLevel': base_level,
            'type': ('numerical' if is_numeric else 'categorical')
        })
    
    return cols_json

def get_model_train_set(full_model_id, model_cache, data_handler):
    model_retriever = VisualMLModelRetriver(full_model_id)
    relativities_calculator = RelativitiesCalculator(data_handler, model_retriever)
    train_set = relativities_calculator.train_set
    return train_set

def get_model_test_set(full_model_id, model_cache, data_handler):
    model_retriever = VisualMLModelRetriver(full_model_id)
    relativities_calculator = RelativitiesCalculator(data_handler, model_retriever)
    test_set = relativities_calculator.test_set
    return test_set

def get_model_base_values_modalities_types(full_model_id, model_cache, data_handler):
    creation_args = {"data_handler": data_handler,
                     "model_cache": model_cache,
                    "full_model_id": full_model_id}
    train_set = model_cache.get_or_create_cached_item(full_model_id, 'train_set', get_model_train_set, **creation_args)
    test_set = model_cache.get_or_create_cached_item(full_model_id, 'test_set', get_model_test_set, **creation_args)
    model_retriever = VisualMLModelRetriver(full_model_id)
    relativities_calculator = RelativitiesCalculator(data_handler, model_retriever, train_set, test_set)
    base_values = relativities_calculator.get_base_values()
    return {'base_values': base_values, 
            'modalities': relativities_calculator.modalities, 
            'types': relativities_calculator.variable_types}

def get_model_relativities(full_model_id, model_cache, data_handler):
    creation_args = {"data_handler": data_handler,
                     "model_cache": model_cache,
                    "full_model_id": full_model_id}
    train_set = model_cache.get_or_create_cached_item(full_model_id, 'train_set', get_model_train_set, **creation_args)
    test_set = model_cache.get_or_create_cached_item(full_model_id, 'test_set', get_model_test_set, **creation_args)
    base_values_modalities_types = model_cache.get_or_create_cached_item(full_model_id, 'base_values_modalities_types', get_model_base_values_modalities_types, **creation_args)
    base_values = base_values_modalities_types['base_values']
    modalities = base_values_modalities_types['modalities']
    variable_types = base_values_modalities_types['types']
    model_retriever = VisualMLModelRetriver(full_model_id)
    relativities_calculator = RelativitiesCalculator(data_handler, model_retriever, train_set, test_set, base_values=base_values, modalities=modalities, variable_types=variable_types)
    relativities = relativities_calculator.get_relativities_df()
    relativities_dict = relativities_calculator.relativities
    return {'relativities': relativities, 'relativities_dict': relativities_dict}

def get_model_relativities_interaction(full_model_id, model_cache, data_handler):
    creation_args = {"data_handler": data_handler,
                     "model_cache": model_cache,
                    "full_model_id": full_model_id}
    train_set = model_cache.get_or_create_cached_item(full_model_id, 'train_set', get_model_train_set, **creation_args)
    test_set = model_cache.get_or_create_cached_item(full_model_id, 'test_set', get_model_test_set, **creation_args)
    base_values_modalities_types = model_cache.get_or_create_cached_item(full_model_id, 'base_values_modalities_types', get_model_base_values_modalities_types, **creation_args)
    base_values = base_values_modalities_types['base_values']
    modalities = base_values_modalities_types['modalities']
    variable_types = base_values_modalities_types['types']
    model_retriever = VisualMLModelRetriver(full_model_id)
    relativities_calculator = RelativitiesCalculator(data_handler, model_retriever, train_set, test_set, base_values=base_values, modalities=modalities, variable_types=variable_types)
    relativities_interaction = relativities_calculator.get_relativities_interactions_df()
    return relativities_interaction

def get_model_variable_level_stats(full_model_id, model_cache, data_handler):
    creation_args = {"data_handler": data_handler,
                     "model_cache": model_cache,
                    "full_model_id": full_model_id}
    train_set = model_cache.get_or_create_cached_item(full_model_id, 'train_set', get_model_train_set, **creation_args)
    test_set = model_cache.get_or_create_cached_item(full_model_id, 'test_set', get_model_test_set, **creation_args)
    relativities = model_cache.get_or_create_cached_item(full_model_id, 'relativities', get_model_relativities, **creation_args)['relativities']
    relativities_interaction = model_cache.get_or_create_cached_item(full_model_id, 'relativities_interaction', get_model_relativities_interaction, **creation_args)
    base_values_modalities_types = model_cache.get_or_create_cached_item(full_model_id, 'base_values_modalities_types', get_model_base_values_modalities_types, **creation_args)
    base_values = base_values_modalities_types['base_values']
    model_retriever = VisualMLModelRetriver(full_model_id)
    variable_level_stats = VariableLevelStatsFormatter(model_retriever, data_handler, relativities, relativities_interaction, base_values, train_set, test_set)
    variable_stats = variable_level_stats.get_variable_level_stats()
    return variable_stats

def get_model_predicted_base(full_model_id, model_cache, data_handler, variable):
    creation_args = {"data_handler": data_handler,
                     "model_cache": model_cache,
                    "full_model_id": full_model_id}
    train_set = model_cache.get_or_create_cached_item(full_model_id, 'train_set', get_model_train_set, **creation_args)
    test_set = model_cache.get_or_create_cached_item(full_model_id, 'test_set', get_model_test_set, **creation_args)
    base_values_modalities_types = model_cache.get_or_create_cached_item(full_model_id, 'base_values_modalities_types', get_model_base_values_modalities_types, **creation_args)
    base_values = base_values_modalities_types['base_values']
    modalities = base_values_modalities_types['modalities']
    variable_types = base_values_modalities_types['types']
    model_retriever = VisualMLModelRetriver(full_model_id)
    relativities_calculator = RelativitiesCalculator(data_handler, model_retriever, train_set, test_set, base_values, modalities, variable_types)
    predicted_base_variable = relativities_calculator.get_formated_predicted_base_variable(variable)
    return predicted_base_variable