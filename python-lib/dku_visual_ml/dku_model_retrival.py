import dataikuapi
from logging_assist.logging import logger
import re
import ast
from dku_visual_ml.dku_base import DataikuClientProject
from dataiku.doctor.posttraining.model_information_handler import PredictionModelInformationHandler
from typing import List, Dict, Any, Optional

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
        spline_config = self._extract_continuous_spline_config(feature_settings)
        if spline_config is not None and "base_level" in spline_config:
            return spline_config.get("base_level")

        custom_handling_code = feature_settings.get('customHandlingCode', '')
       # Match either a quoted string or a signed integer/float
        pattern = r'"base_level":\s*(?:"([^"]+)"|([+-]?\d+(?:\.\d+)?))'
        match = re.search(pattern, custom_handling_code)
        base_level = None
        if match:
            if match.group(1) is not None:
                base_level = match.group(1)
            elif match.group(2) is not None:
                # Convert numeric string to float to support decimals
                num_str = match.group(2)
                try:
                    base_level = float(num_str)
                except ValueError:
                    base_level = None
        logger.debug(f"returning base_level {base_level}")
        return base_level

    def _extract_continuous_spline_config(self, feature_settings: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        custom_handling_code = feature_settings.get('customHandlingCode', '')
        if "continuous_spline" not in custom_handling_code:
            return None

        try:
            parsed = ast.parse(custom_handling_code)
        except SyntaxError:
            return None

        for node in ast.walk(parsed):
            if not isinstance(node, ast.Assign):
                continue
            value = node.value
            if not isinstance(value, ast.Call):
                continue
            if not isinstance(value.func, ast.Name) or value.func.id != "continuous_spline":
                continue
            if not value.args:
                continue
            try:
                config_dict = ast.literal_eval(value.args[0])
            except (ValueError, SyntaxError):
                continue
            if isinstance(config_dict, dict):
                return config_dict
        return None

    def _extract_spline_features(self, feature_settings: Dict[str, Any]) -> List[List[Dict[str, Any]]]:
        spline_config = self._extract_continuous_spline_config(feature_settings)
        if not spline_config:
            return []

        raw_spline_features = spline_config.get("spline_features")
        if raw_spline_features is None and spline_config.get("definitions") is not None:
            # Backward compatibility with flat shape.
            raw_spline_features = [spline_config.get("definitions")]

        if not isinstance(raw_spline_features, list):
            return []

        spline_features = []
        for feature in raw_spline_features:
            if not isinstance(feature, list):
                continue
            segments = []
            for segment in feature:
                if not isinstance(segment, dict):
                    continue
                if not {"min_value", "max_value", "degree"}.issubset(segment.keys()):
                    continue
                try:
                    segments.append({
                        "min_value": float(segment["min_value"]),
                        "max_value": float(segment["max_value"]),
                        "degree": int(segment["degree"]),
                    })
                except (TypeError, ValueError):
                    continue
            if segments:
                spline_features.append(segments)
        return spline_features

    def _extract_categorical_groups(self, feature_settings: Dict[str, Any]) -> List[List[str]]:
        custom_handling_code = feature_settings.get('customHandlingCode', '')
        if "rebase_mode" not in custom_handling_code:
            return []

        try:
            parsed = ast.parse(custom_handling_code)
        except SyntaxError:
            return []

        for node in ast.walk(parsed):
            if not isinstance(node, ast.Assign):
                continue
            value = node.value
            if not isinstance(value, ast.Call):
                continue
            if not isinstance(value.func, ast.Name) or value.func.id != "rebase_mode":
                continue
            if not value.args:
                continue
            try:
                config_dict = ast.literal_eval(value.args[0])
            except (ValueError, SyntaxError):
                continue
            if not isinstance(config_dict, dict):
                continue
            raw_groups = config_dict.get("categorical_groups")
            if not isinstance(raw_groups, list):
                return []
            normalized_groups = []
            seen_modalities = set()
            for raw_group in raw_groups:
                if not isinstance(raw_group, list):
                    continue
                group = []
                for modality in raw_group:
                    modality_str = str(modality)
                    if modality_str in seen_modalities or modality_str in group:
                        continue
                    group.append(modality_str)
                if len(group) < 2:
                    continue
                normalized_groups.append(group)
                seen_modalities.update(group)
            return normalized_groups

        return []
    
    def _process_feature(self, feature: str, preprocessing: Dict[str, Any], 
                         exposure_columns: str, target_column: str) -> Dict[str, Any]:
        
        feature_settings = preprocessing.get(feature, {})
        feature_dict = self._get_basic_feature_info(feature_settings)
        feature_dict["baseLevel"] = self._extract_base_level(feature_settings)
        feature_dict["splineFeatures"] = self._extract_spline_features(feature_settings)
        feature_dict["categoricalGroups"] = self._extract_categorical_groups(feature_settings)
        
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
    
    def get_theta(self):
        logger.debug("Getting the Theta")
        return self.algo_settings.get('params').get('alpha')
    
    def get_power(self):
        logger.debug("Getting the Power")
        return self.algo_settings.get('params').get('power')
    
    def get_var_power(self):
        logger.debug("Getting the Variance Power")
        return self.algo_settings.get('params').get('var_power')
    
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
            "theta": self.get_theta(),
            "power": self.get_power(),
            "var_power": self.get_var_power(),
            "params": features_dict,
            "interactions":[
                {'first': first, 'second': second}
                for first, second in zip(interaction_columns_first, interaction_columns_second)
            ]
            
        }
        logger.info(f"Retrieved setup parameters for model id {self.full_model_id}")
        logger.info(f"Setup params are {setup_params}")
        return setup_params

    def delete_model(self, model_id):
        
        self.task.delete_trained_model(model_id=model_id)        

        
    
