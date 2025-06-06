import dataiku
import dataikuapi
from logging_assist.logging import logger
import re
from dku_visual_ml.dku_base import DataikuClientProject
from dataiku.doctor.posttraining.model_information_handler import PredictionModelInformationHandler
from typing import List, Dict, Any, Optional

# need to come up with a structure way of storing features as its being done twice

class VisualMLModelRetriver(DataikuClientProject):
    """
    An class to retrieve the modelling parameter from a DKU visual ML model
    based on a full model Id, and format them for the front end
    """

    def __init__(self, full_model_id):
        super().__init__()

        logger.info(f"Initialising a model retriever for model ID {full_model_id}")
        
        self.full_model_id = full_model_id
        self.task = dataikuapi.dss.ml.DSSMLTask.from_full_model_id(
            self.client, 
            full_model_id, 
            self.project.project_key
        )
        self.model_details = self.task.get_trained_model_details(full_model_id) 
        self.algo_settings = self.model_details.get_modeling_settings().get('plugin_python_grid')
        self.model_info_handler = PredictionModelInformationHandler.from_full_model_id(self.full_model_id)
        self.offset_columns = self.get_offset_columns()
        self.features = self.model_info_handler.get_per_feature()
        self.exposure_columns = self.get_exposure_columns()
        self.target_column = self.get_target_column() 
        self.predictor = self.get_predictor()
        self.get_used_features()
        logger.info(f"Model retriever intialised for model ID {full_model_id}")
              
    def get_offset_columns(self):
        return self.algo_settings['params']['offset_columns']
    
    def get_features(self):
        logger.info(f"Getting features for model ID {self.full_model_id}")
        return self.features
    
    def get_feature_type(self, feature):
        logger.debug(f"Getting feature type for {feature}")
        feature_type = self.features.get(feature).get('type')
        logger.debug(f"Feature type is {feature_type}")
        return feature_type
    
    def get_rescaling_type(self, feature):
        logger.debug(f"Getting Rescaling type for {feature}")
        rescaling_type = self.features.get(feature).get('rescaling')
        logger.debug(f"Rescaling type is {rescaling_type}")
        return rescaling_type
    
    def get_full_model_id(self):
        return self.full_model_id
    
    def get_target_column(self):
        print(f"Getting the target column for model id {self.full_model_id}")
        self.target_column = self.model_details.details.get('coreParams').get('target_variable')
        if not self.target_column:
            print("Unable to find a target column")
            return
        else:
            print(f"returning the target column for model id {self.target_column }")
            return self.target_column 

    
    def _get_excluded_features(self):
        logger.debug(f"Excluding features exposure {self.exposure_columns}")
        logger.debug(f"Excluding features target {self.target_column}")
        important_columns = []
        important_columns += [self.offset_columns, self.exposure_columns, self.target_column]
        
        return important_columns
    
    def _get_included_features(self):
        logger.debug(f"Getting Included features")
        excluded_features = self._get_excluded_features()
        logger.debug(f"Searching in features")
        logger.debug(f"excluded_features: {excluded_features}")
        self.non_excluded_features = [feature for feature in self.features.keys() if feature not in excluded_features]
        logger.debug(f"Found Included features as {self.non_excluded_features }")
        return self.non_excluded_features

    
    def get_used_features(self):
        """
        Filters features based on their importance and role in the model.
        """

        self.non_excluded_features = self._get_included_features()
        self.used_features = [feature for feature in self.non_excluded_features if self.features[feature]['role'] == 'INPUT']
        self.candidate_features = [feature for feature in self.non_excluded_features if self.features[feature]['role'] == 'REJECT']
        logger.info(f"Features filtered: non_excluded_features={self.non_excluded_features}, used_features={self.used_features}, candidate_features={self.candidate_features}")
        return self.used_features
    
    def get_interactions(self):
        """
        Extracts the interaction variables from the model
        """
        coef_table = self.predictor._clf.coef_table.reset_index()
        coef_variable_names = list(coef_table['index'])
        interaction_variables = [variable for variable in coef_variable_names if variable.split(':')[0] == 'interaction']
        final_interactions = set()

        for interaction in interaction_variables:
            split_interaction = interaction.split('::')
            first = split_interaction[0].split(':')[1]
            second = split_interaction[1].split(':')[1]
            final_interactions.add((first, second))
        
        final_interactions = list(final_interactions)
        return final_interactions

    def get_features_used_in_modelling(self):
        """
        Retrieves the features used in the model.

        Returns:
            list: A list of dictionaries with feature details.
        """
        logger.info("Retrieving model features.")
        self._get_included_features()
        features_list = [
            {'variable': feature, 
             'isInModel': self.features[feature]['role'] == 'INPUT', 
             'variableType': 'categorical' if self.features[feature]['type'] == 'CATEGORY' else 'numeric'} 
            for feature in self.non_excluded_features
        ]

        logger.info(f"Features retrieved: {features_list}")
        return features_list
    
    
    def get_rejected_features(self):
        logger.debug(f"Getting Rejected Features")
        self.candidate_features = [feature for feature in self.non_excluded_features if self.features[feature]['role'] == 'REJECT']
        logger.debug(f"Rejected Features are {self.candidate_features}")
        return self.candidate_features
    
        
    def get_features_and_type(self):
        
        logger.info(f"Getting Features for {self.full_model_id }")
        self._get_included_features()
        
        formatted_features = [
            {'variable': feature, 
              'isInModel': self.features[feature]['role']=='INPUT', 
              'variableType': 'categorical' if self.features[feature]['type'] == 'CATEGORY' else 'numeric'
            } for feature in self.non_excluded_features]
        return formatted_features
    
    def get_predictor(self):
        """
        Retrieves a model predictor.

        """
        logger.debug(f"Getting predictor for the model {self.full_model_id}")
        predictor = self.model_info_handler.get_predictor()
        logger.debug(f"Successfully retrieved predictor for the model {self.full_model_id}")
        return predictor
    
    
    def _get_basic_feature_info(self, feature_settings: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "role": feature_settings.get('role'),
            'type': feature_settings.get('type'),
            "handling": feature_settings.get('numerical_handling') or feature_settings.get('category_handling'),
        }

    def _extract_base_level(self, feature_settings: Dict[str, Any]) -> Optional[str]:
        custom_handling_code = feature_settings.get('customHandlingCode', '')
        pattern = r'["\']base_level["\']\s*:\s*(["\'])(.*?)\1'
        match = re.search(pattern, custom_handling_code)
        # If a match is found, the value is in the second captured group.
        return match.group(2) if match else None
    
    def _process_feature(self, feature: str, preprocessing: Dict[str, Any], 
                         exposure_columns: str, target_column: str) -> Dict[str, Any]:
        
        feature_settings = preprocessing.get(feature, {})
        feature_dict = self._get_basic_feature_info(feature_settings)
        feature_dict["baseLevel"] = self._extract_base_level(feature_settings)
        
        if feature == exposure_columns:
            feature_dict["role"] = "Exposure"
        elif feature == target_column:
            feature_dict["role"] = "Target"
        
        return feature_dict
    
    
    def get_features_dict(self) -> Dict[str, Dict[str, Any]]:
        
        logger.info("Getting model feature dict")
        exposure_columns = self.get_exposure_columns()
        target_column = self.get_target_column()
        
        preprocessing = self.model_details.get_preprocessing_settings().get('per_feature')
        features = preprocessing.keys()
        
        features_dict = {}
        for feature in features:
            feature_dict = self._process_feature(feature, preprocessing, exposure_columns, target_column)
            features_dict[feature] = feature_dict
                    
                
        logger.info("Model retriever succesfully got features")    
        logger.debug(f"Features are:{features_dict}")
        return features_dict
    
    def get_exposure_columns(self):
        try:
            if self.exposure_columns:
                return self.exposure_columns
            else:
                self.exposure_columns = self.algo_settings.get('params').get('exposure_columns')[0]
                return self.exposure_columns
        except:
            self.exposure_columns = self.algo_settings.get('params').get('exposure_columns')[0]
            return self.exposure_columns

    def get_elastic_net_penalty(self):
        return self.algo_settings.get('params').get('penalty')[0]
    
    def get_l1_ratio(self):
        logger.debug("Getting the L1 Ratio")
        return self.algo_settings.get('params').get('l1_ratio')[0]
    
    def get_distribution_function(self):
        logger.debug("Getting the distribution Function")
        distribution_function = self.algo_settings.get('params').get('family_name')
        return distribution_function.title()
    
    def get_link_function(self):
        logger.debug("Getting the Link Function")
        distribution_function = self.get_distribution_function()
        link_function = self.algo_settings.get('params').get(distribution_function.lower()+"_link").title()
        logger.debug(f"Returning the link_function as {link_function}")
        return link_function
    
    def get_setup_params(self):   

        logger.debug(f"Retrieving setup parameters for model id {self.full_model_id}")
        logger.debug("Model Parameters")
        features_dict = self.get_features_dict()
        interaction_columns_first = self.predictor._clf.interaction_columns_first
        interaction_columns_second = self.predictor._clf.interaction_columns_second
        
        setup_params = {
            "target_column": self.get_target_column(),
            "exposure_column":self.get_exposure_columns(),
            "distribution_function": self.get_distribution_function(),
            "link_function":self.get_link_function(),
            "elastic_net_penalty": self.get_elastic_net_penalty(),
            "l1_ratio": self.get_l1_ratio(),
            "params": features_dict,
            "interactions":[
                {'first': first, 'second': second}
                for first, second in zip(interaction_columns_first, interaction_columns_second)
            ]
            
        }
        logger.info(f"Retrieved setup parameters for model id {self.full_model_id}")
        logger.info(f"Setup params are {setup_params}")
        return setup_params


        
    
