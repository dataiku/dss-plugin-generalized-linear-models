from backend.dataiku_api import dataiku_api
from logging.config import dictConfig
import os
import pandas as pd
import numpy as np
# Replace by your default project key that you are working on in dev
DEFAULT_PROJECT_KEY = "SOL_CLAIM_MODELING"

# TODO : Add dip_home to a .env file

CONFIG = {
    # put your webapp desired config
    "webapp_config": {
        "model_id": "aHJZVrBQ",
    },
    "default_project_key": DEFAULT_PROJECT_KEY,
    "training_dataset_string": "claim_train",
    "exposure_column":"exposure"
}


os.environ["DKU_CURRENT_PROJECT_KEY"] = CONFIG.get("default_project_key")


def get_setup_for_dataiku_client():
    return {
        "webapp_config": CONFIG.get("webapp_config"),
        "default_project_key": CONFIG.get("default_project_key"),
        "training_dataset_string": CONFIG.get("claim_train"),
        "exposure_column": CONFIG.get("exposure")
    }

DKU_CUSTOM_WEBAPP_CONFIG='{"saved_model_id": "U4TLlapA","training_dataset_string": "claim_train","code_env_string": "anotherValue"}'


dictConfig(
    {
        "version": 1,
        "formatters": {
            "default": {
                "format": "[%(asctime)s] %(levelname)s in %(module)s: %(message)s",
            }
        },
        "handlers": {
            "wsgi": {
                "class": "logging.StreamHandler",
                "stream": "ext://flask.logging.wsgi_errors_stream",
                "formatter": "default",
            }
        },
        "root": {"level": "INFO", "handlers": ["wsgi"]},
    }
)


def setup_dataiku_client():
    dataiku_setup = get_setup_for_dataiku_client()
    dataiku_api.setup(**dataiku_setup)

    
dummy_models = [{"id": "model_interaction", "name": "Interaction"}, {"id": "model_1", "name": "Generalized Linear Model Regression (GLM 1)"}, {"id": "model_2", "name": "Generalized Linear Model Regression (GLM 2)"}]

dummy_variables = [{'variable': 'Variable1', 'isInModel': True, 'variableType': 'categorical'},
                    {'variable': 'Variable2', 'isInModel': False, 'variableType': 'numeric'}]

dummy_df_data = pd.DataFrame({
            'definingVariable': ['Variable1','Variable1','Variable1','Variable1', 'Variable2','Variable2','Variable2','Variable2'],
            'Category': ['January', 'February', 'March', 'April', 10, 20, 30, 40],
            'Value': [0.2, 0.05, 0.3, 0.15, 0.4, 0.5, 0.6, 0.4],
            'observedAverage': [0.4, 0.5, 0.6, 0.4, 0.2, 0.05, 0.3, 0.15],
            'fittedAverage': [0.4, 0.7, 0.9, 0.8, 0.4, 0.5, 0.6, 0.4],
            'baseLevelPrediction': [0.5, 0.55, 0.6, 0.7, 0.5, 0.5, 0.4, 0.45]
        })


pre_dummy_base_values = {'Variable1': 'January', 
                     'Variable2': 20}
dummy_base_values = [{'variable': k, 'base_level': v} for k, v in pre_dummy_base_values.items()]

dummy_lift_data = pd.DataFrame({
            'Category': ['0.1', '0.15', '0.2', '0.3', '0.4', '0.6', '0.8', '1'],
            'Value': [100, 103, 101, 98, 100, 100, 101, 102],
            'observedAverage': [0.1, 0.15, 0.2, 0.3, 0.4, 0.6, 0.8, 1],
            'fittedAverage': [0.12, 0.16, 0.19, 0.32, 0.37, 0.55, 0.83, 1.02]
        })
dummy_lift_data['observedAverage'] = [float('%s' % float('%.3g' % x)) for x in dummy_lift_data['observedAverage']]
dummy_lift_data['fittedAverage'] = [float('%s' % float('%.3g' % x)) for x in dummy_lift_data['fittedAverage']]

dummy_get_updated_data  = pd.DataFrame({
            'definingVariable': ['Variable1','Variable1','Variable1','Variable1', 'Variable2','Variable2','Variable2','Variable2'],
            'Category': ['January', 'February', 'March', 'April','January', 'February', 'March', 'April'],
            'inModel': [True, True, True, True, False, False, False, False],
            'Value': [0.2, 0.05, 0.3, 0.15, 0.4, 0.5, 0.6, 0.4],
            'observedAverage': [0.4, 0.5, 0.6, 0.4, 0.2, 0.05, 0.3, 0.15],
            'fittedAverage': [0.4, 0.7, 0.9, 0.8, 0.4, 0.5, 0.6, 0.4],
            'baseLevelPrediction': [0.5, 0.55, 0.6, 0.7, 0.5, 0.5, 0.4, 0.45]
        })

dummy_relativites= pd.DataFrame({'variable': ['Variable1','Variable1','Variable1','Variable1', 'Variable1','Variable1','Variable1', 'Variable1', 'Variable1','Variable1','Variable1','Variable1', 'Variable2','Variable2','Variable2','Variable2'],
                        'category': ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'December', 'Other','January', 'February', 'March', 'April'],
                        'relativity': [1.0, 1.087324, 0.98091882, 0.7929717, 1.087324, 0.98091882, 0.7929717, 0.992374, 1.087324, 0.98091882, 0.7929717, 0.992374, 1.0, 0.992374, 1.19274, 1.052333]})

dummy_model_metrics_old ={
        "models": {
            "Model_1": {
            "AIC": 100,
            "BIC": 120,
            "Deviance": 5.5
            },
            "Model_2": {
            "AIC": 95,
            "BIC": 110,
            "Deviance": 5.0
            }
        }
        }

dummy_model_metrics ={
            "AIC": 100,
            "BIC": 120,
            "Deviance": 5.5
        }

dummy_model_metrics2 ={
            "AIC": 323,
            "BIC": 992,
            "Deviance": 18881
        }

interaction_setup_params = {
    "target_column": "ClaimAmount",
    "interactions": [{ "first": 'VehBrand', "second": 'VehPower' },
                     { "first": 'Area', "second": 'DrivAge' }],
    "exposure_column":"Exposure",
    "distribution_function":"Tweedie",
    "link_function":"Logit",
    'params': {'VehGas': {'role': 'REJECT','type': 'CATEGORY','handling': 'DUMMIFY'},
    'VehPower': {'role': 'REJECT', 'type': 'NUMERIC', 'handling': 'REGULAR'},
    'ClaimNb': {'role': 'REJECT', 'type': 'NUMERIC', 'handling': 'REGULAR'},
    'VehAge': {'role': 'REJECT', 'type': 'NUMERIC', 'handling': 'REGULAR'},
    'VehBrand': {'role': 'INPUT', 'type': 'CATEGORY', 'handling': 'DUMMIFY', 'chooseBaseLevel': True, 'baseLevel': 'B10'},
    'Exposure': {'role': 'INPUT', 'type': 'NUMERIC', 'handling': 'REGULAR'},
    'DrivAge': {'role': 'INPUT', 'type': 'NUMERIC', 'handling': 'REGULAR'},
    'BonusMalus': {'role': 'REJECT', 'type': 'NUMERIC', 'handling': 'REGULAR'},
    'Density': {'role': 'REJECT', 'type': 'NUMERIC', 'handling': 'REGULAR'},
    'Area': {'role': 'REJECT', 'type': 'CATEGORY', 'handling': 'DUMMIFY'},
    'ClaimAmount': {'role': 'Target', 'type': 'NUMERIC', 'handling': None},
    'IDpol': {'role': 'REJECT', 'type': 'NUMERIC', 'handling': None},
    'Region': {'role': 'REJECT', 'type': 'CATEGORY', 'handling': 'CUSTOM'}} 
}

dummy_setup_params = {
    "target_column": "ClaimAmount",
    "exposure_column":"Exposure",
    "distribution_function":"Tweedie",
    "link_function":"Logit",
    'params': {'VehGas': {'role': 'REJECT','type': 'CATEGORY','handling': 'DUMMIFY'},
    'VehPower': {'role': 'REJECT', 'type': 'NUMERIC', 'handling': 'REGULAR'},
    'ClaimNb': {'role': 'REJECT', 'type': 'NUMERIC', 'handling': 'REGULAR'},
    'VehAge': {'role': 'REJECT', 'type': 'NUMERIC', 'handling': 'REGULAR'},
    'VehBrand': {'role': 'INPUT', 'type': 'CATEGORY', 'handling': 'DUMMIFY', 'chooseBaseLevel': True, 'baseLevel': 'B10'},
    '5_Interaction': {'role': 'REJECT','type': 'CATEGORY','handling': 'DUMMIFY'},
    'Exposure': {'role': 'INPUT', 'type': 'NUMERIC', 'handling': 'REGULAR'},
    'DrivAge': {'role': 'INPUT', 'type': 'NUMERIC', 'handling': 'REGULAR'},
    'BonusMalus': {'role': 'REJECT', 'type': 'NUMERIC', 'handling': 'REGULAR'},
    'Density': {'role': 'REJECT', 'type': 'NUMERIC', 'handling': 'REGULAR'},
    '6_Interaction': {'role': 'REJECT','type': 'CATEGORY','handling': 'DUMMIFY'},
    'Area': {'role': 'REJECT', 'type': 'CATEGORY', 'handling': 'DUMMIFY'},
    'ClaimAmount': {'role': 'Target', 'type': 'NUMERIC', 'handling': None},
    'IDpol': {'role': 'REJECT', 'type': 'NUMERIC', 'handling': None},
    'DrivAgeBin': {'role': 'REJECT', 'type': 'CATEGORY', 'handling': 'DUMMIFY'},
    'Region': {'role': 'REJECT', 'type': 'CATEGORY', 'handling': 'CUSTOM'},
    '4_Interaction': {'role': 'REJECT','type': 'CATEGORY','handling': 'DUMMIFY'}}}

dummy_setup_params_2 = {
    "target_column": "ClaimNb",
    "exposure_column":"VehAge",
    "distribution_function":"Gaussian",
    "link_function":"Log",
    "elastic_net_penalty": 0.001,
    "l1_ratio": 0.5,
    'params': {'VehGas': {'role': 'REJECT',
    'type': 'CATEGORY',
    'handling': 'DUMMIFY'},
    'VehPower': {'role': 'REJECT', 'type': 'NUMERIC', 'handling': 'REGULAR'},
    'ClaimNb': {'role': 'TARGET', 'type': 'NUMERIC', 'handling': 'REGULAR'},
    'VehAge': {'role': 'Input', 'type': 'NUMERIC', 'handling': 'REGULAR'},
    'VehBrand': {'role': 'INPUT', 'type': 'CATEGORY', 'handling': 'DUMMIFY', 'chooseBaseLevel': True, 'baseLevel': 'B11'},
    '5_Interaction': {'role': 'REJECT',
    'type': 'CATEGORY',
    'handling': 'DUMMIFY'},
    'Exposure': {'role': 'INPUT', 'type': 'NUMERIC', 'handling': 'REGULAR'},
    'DrivAge': {'role': 'INPUT', 'type': 'NUMERIC', 'handling': 'REGULAR'},
    'BonusMalus': {'role': 'REJECT', 'type': 'NUMERIC', 'handling': 'REGULAR'},
    'Density': {'role': 'REJECT', 'type': 'NUMERIC', 'handling': 'REGULAR'},
    '6_Interaction': {'role': 'REJECT',
    'type': 'CATEGORY',
    'handling': 'DUMMIFY'},
    'Area': {'role': 'REJECT', 'type': 'CATEGORY', 'handling': 'DUMMIFY'},
    'ClaimAmount': {'role': 'Target', 'type': 'NUMERIC', 'handling': None},
    'IDpol': {'role': 'REJECT', 'type': 'NUMERIC', 'handling': None},
    'DrivAgeBin': {'role': 'REJECT', 'type': 'CATEGORY', 'handling': 'DUMMIFY'},
    'Region': {'role': 'REJECT', 'type': 'CATEGORY', 'handling': 'CUSTOM'},
    '4_Interaction': {'role': 'REJECT',
    'type': 'CATEGORY',
    'handling': 'DUMMIFY'}}}
dummy_setup_params_3 = {
    'target_column': 'ClaimAmount',
      'exposure_column': 'Exposure', 
      'distribution_function': 'Gaussian', 
      'link_function': 'Log',
        'params': {'VehGas': {'role': 'INPUT', 'type': 'CATEGORY', 'handling': 'CUSTOM'},
                   'VehPower': {'role': 'REJECT', 'type': 'NUMERIC', 'handling': 'REGULAR'}, 
                   'ClaimNb': {'role': 'REJECT', 'type': 'NUMERIC', 'handling': 'REGULAR'},
                     'VehAge': {'role': 'REJECT', 'type': 'NUMERIC', 'handling': 'REGULAR'}, 
                     'VehBrand': {'role': 'REJECT', 'type': 'CATEGORY', 'handling': 'DUMMIFY'},
                       'Exposure': {'role': 'INPUT', 'type': 'NUMERIC', 'handling': 'REGULAR'}, 
                       'DrivAge': {'role': 'REJECT', 'type': 'NUMERIC', 'handling': 'REGULAR'}, 
                       'BonusMalus': {'role': 'REJECT', 'type': 'NUMERIC', 'handling': 'REGULAR'},
                         '2_interaction': {'role': 'REJECT', 'type': 'CATEGORY', 'handling': 'CUSTOM'},
                           'Density': {'role': 'REJECT', 'type': 'NUMERIC', 'handling': 'REGULAR'}, 
                           'Area': {'role': 'REJECT', 'type': 'CATEGORY', 'handling': 'DUMMIFY'},
                             'ClaimAmount': {'role': 'TARGET', 'type': 'NUMERIC', 'handling': None}, 
                             'IDpol': {'role': 'REJECT', 'type': 'NUMERIC', 'handling': None}, 
                             'DrivAgeBin': {'role': 'REJECT', 'type': 'CATEGORY', 'handling': 'DUMMIFY'},
                               'interaction': {'role': 'REJECT', 'type': 'CATEGORY', 'handling': 'DUMMIFY'},
                                 'Region': {'role': 'REJECT', 'type': 'CATEGORY', 'handling': 'DUMMIFY'}}}
def get_dummy_model_comparison_data():
    df = pd.DataFrame()
    # df['Category'] = ["B0","B1","B2","B3","B4","B5","B6","B7","B8","B9","B10"]
    # df['exposure'] = np.random.uniform(30, 120, size=11)
    # df['Model_1_fittedAverage'] =  np.random.uniform(0.3, .8, size=11)
    # df['Model_2_fittedAverage'] =  np.random.uniform(0.5, 1, size=11)
    # df['observedAverage'] =  np.random.uniform(0.6, 0.75, size=11)
    df['definingVariable'] =["VehPower","VehPower","VehPower","VehPower","VehPower","VehPower","VehPower","VehPower","VehPower","VehPower","VehPower"]
    df['Category']= ["B0","B1","B2","B3","B4","B5","B6","B7","B8","B9","B10"]
    df['model_1_observedAverage']= np.random.uniform(0.5, 1, size=11)
    df['model_1_fittedAverage'] = np.random.uniform(0.5, 1, size=11)
    df['Value']= np.random.uniform(0.5, 1, size=11)
    df['model1_baseLevelPrediction']= np.random.uniform(0.5, 1, size=11)
    df['model_2_observedAverage']= np.random.uniform(0.5, 1, size=11)
    df['model_2_fittedAverage']= np.random.uniform(0.5, 1, size=11)
    df['model2_baseLevelPrediction']= np.random.uniform(0.5, 1, size=11)
    choices = ["train", "test"]
    df['dataset']= [np.random.choice(choices) for _ in range(11)]
    return df

dummy_variable_level_stats = pd.DataFrame({'variable': ['VehBrand', 'VehBrand', 'VehBrand', 'VehPower', 'VehPower'], 
                       'value': ['B1', 'B10', 'B12', 'Diesel', 'Regular'], 
                       'coefficient': [0, 0.5, 0.32, 0, 0.0234],
                       'p_value': [0, 0.05, 0.302, 0.002, 0.0234],
                       'standard_error': [0, 1.23, 1.74, 0, 0.9],
                       'standard_error_pct': [0, 1.23, 1.74, 0, 0.9],
                        'weight': [234, 87, 73, 122, 90], 
                        'weight_pct': [60, 20, 20, 65, 35], 
                        'relativity': [1, 1.23, 1.077, 1, 0.98]}).to_dict('records')

data = {'Name': ['John', 'Alice', 'Bob'], 'Age': [30, 25, 35]}
variable_level_stats_df = pd.DataFrame(data)