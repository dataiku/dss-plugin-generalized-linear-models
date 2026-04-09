from logging_assist.logging import logger
from logging_assist.logging import logger

class DKUVisualMLConfig:
    MAX_SPLINE_FEATURES = 3
    MAX_SPLINE_SEGMENTS_PER_FEATURE = 6
    
    def __init__(self):
        
        logger.debug("Initalising a dku visual ML config with the existing web app settings")
        
        self.prediction_type = "REGRESSION"
        self.target_column = None
        self.exposure_column = None
        self.sample_weight_column = None
        self.offset_columns = []
        self.variables = {}
        self.interaction_variables = []
        logger.debug("Successfully initalised a dku visual ML config with the existing web app settings")
        self.log_configuration()
    
    def get_variable_by_role(self, role_name):
        for variable in self.variables:
            role = self.variables[variable].get("role", "").lower()
            if role == role_name:
                logger.debug(f"Returning variable {variable}")
                return variable
        raise ValueError(f"{role_name.capitalize()} Variable is not set in the Visual ML configuration")
    
    def get_target_variable(self):
        logger.debug("Getting target variable")
        return self.target_column
    
    def get_exposure_variable(self):
        logger.debug("Getting exposure variable")
        return self.exposure_column

    def get_sample_weight_variable(self):
        logger.debug("Getting sample weight variable")
        return self.sample_weight_column

    def get_offset_variables(self):
        logger.debug("Getting offset variables")
        return self.offset_columns or []
    
    def get_interaction_variables(self):
        logger.debug("Getting interaction variables")
        return self.interaction_variables

    def get_offset_variable(self):
        logger.debug("Getting offset variables")
        return self.get_variable_by_role("offset")
    
    def get_variable_type(self, variable):
        logger.debug("Getting variable type")
        variable_type = self.variables[variable].get('type')
        if variable_type:
            return variable_type
        else: raise ValueError(f"Variable type not set in the Visual ML configuration for {variable}")

    @staticmethod
    def _normalize_spline_segments(segments):
        if not isinstance(segments, list):
            return []

        normalized = []
        for segment in segments:
            if not isinstance(segment, dict):
                continue
            if not {"min_value", "max_value", "degree"}.issubset(segment.keys()):
                continue
            try:
                min_value = float(segment["min_value"])
                max_value = float(segment["max_value"])
                degree = int(segment["degree"])
            except (TypeError, ValueError):
                continue
            if min_value >= max_value:
                continue
            normalized.append({
                "min_value": min_value,
                "max_value": max_value,
                "degree": degree,
            })
            if len(normalized) >= DKUVisualMLConfig.MAX_SPLINE_SEGMENTS_PER_FEATURE:
                break
        return normalized

    @classmethod
    def _normalize_spline_features(cls, spline_features):
        # Backward compatibility: previously a flat list of segment dicts was used.
        if isinstance(spline_features, list) and spline_features and all(isinstance(x, dict) for x in spline_features):
            normalized_segments = cls._normalize_spline_segments(spline_features)
            return [normalized_segments] if normalized_segments else []

        if not isinstance(spline_features, list):
            return []

        normalized_features = []
        for feature in spline_features[:cls.MAX_SPLINE_FEATURES]:
            normalized_segments = cls._normalize_spline_segments(feature)
            if normalized_segments:
                normalized_features.append(normalized_segments)
        return normalized_features

    def get_feature_spline_features(self, variable):
        feature_config = self.variables.get(variable, {})
        raw_spline_features = feature_config.get("spline_features")
        if raw_spline_features is None:
            raw_spline_features = feature_config.get("spline_definitions")
        return self._normalize_spline_features(raw_spline_features)

    @staticmethod
    def _normalize_categorical_groups(raw_groups):
        if not isinstance(raw_groups, list):
            return []

        normalized_groups = []
        seen_modalities = set()
        for raw_group in raw_groups[:5]:
            if not isinstance(raw_group, list):
                continue
            normalized_group = []
            for modality in raw_group:
                modality_str = str(modality)
                if modality_str in seen_modalities:
                    continue
                if modality_str in normalized_group:
                    continue
                normalized_group.append(modality_str)
            if len(normalized_group) < 2:
                continue
            normalized_groups.append(normalized_group)
            seen_modalities.update(normalized_group)

        return normalized_groups

    @staticmethod
    def _normalize_algorithm_identifier(value):
        if value is None:
            return None

        return str(value).strip().lower().replace("-", "_").replace(" ", "_")

    def get_feature_categorical_groups(self, variable):
        feature_config = self.variables.get(variable, {})
        raw_groups = feature_config.get("categorical_groups")
        if raw_groups is None:
            raw_groups = feature_config.get("categoricalGroups")
        return self._normalize_categorical_groups(raw_groups)

    @staticmethod
    def build_numeric_custom_handling_code(base_level, spline_features):
        custom_preamble = (
            'from dataiku.base.model_plugin import prepare_for_plugin\n'
            'prepare_for_plugin(\'generalized-linear-models\', \'generalized-linear-models_regression\')\n'
        )

        if spline_features:
            if base_level is None:
                raise ValueError("Spline features require a base_level for the variable")
            return (
                custom_preamble +
                'from processors.processors import continuous_spline\n'
                'processor = continuous_spline({"base_level": ' + repr(base_level) +
                ', "spline_features": ' + repr(spline_features) + '})\n'
            )

        return (
            custom_preamble +
            'from processors.processors import save_base\n'
            'processor = save_base({"base_level": ' + repr(base_level) + '})\n'
        )

    @staticmethod
    def build_categorical_custom_handling_code(base_level, categorical_groups):
        normalized_groups = DKUVisualMLConfig._normalize_categorical_groups(categorical_groups)
        return (
            'from dataiku.base.model_plugin import prepare_for_plugin\n'
            'prepare_for_plugin(\'generalized-linear-models\', \'generalized-linear-models_regression\')\n'
            'from processors.processors import rebase_mode\n'
            'processor = rebase_mode({"base_level": ' + repr(base_level) +
            ', "categorical_groups": ' + repr(normalized_groups) + '})\n'
        )
        
    def get_included_variables(self):
        included_variables = []
        for variable in self.variables:
            included = self.variables[variable].get('included')
            if included:
                included_variables.append(variable)
        if len(included_variables)>0:
            return included_variables
        else: 
            return []
        
    def get_excluded_features(self):
        protected_variables = {self.get_target_variable()}
        if self.exposure_column:
            protected_variables.add(self.exposure_column)
        if self.sample_weight_column:
            protected_variables.add(self.sample_weight_column)
        protected_variables.update(self.offset_columns or [])

        excluded_variables = []
        for variable in self.variables:
            included = self.variables[variable].get('included')
            if not included and variable not in protected_variables:
                excluded_variables.append(variable)
        return excluded_variables

        
    def get_model_features(self):
        
        target_variable = self.get_target_variable()
        included_variables = self.get_included_variables()
        protected_variables = {target_variable}
        if self.exposure_column:
            protected_variables.add(self.exposure_column)
        if self.sample_weight_column:
            protected_variables.add(self.sample_weight_column)
        protected_variables.update(self.offset_columns or [])
        
        model_features = [var for var in included_variables if var not in protected_variables]
        
        if len(model_features)>0:
            return model_features
        else: 
            return []

    def update_model_parameters(self, request_json):
        
        logger.debug("Initalising DKUVisualMLConfig ")
        self.target_column = request_json.get('targetColumn') or request_json.get('target_column')
        self.exposure_column = request_json.get('exposureColumn') or request_json.get('exposure_column')
        self.sample_weight_column = request_json.get('sampleWeightColumn') or request_json.get('sample_weight_column')
        self.offset_columns = request_json.get('offsetColumns')
        if self.offset_columns is None:
            self.offset_columns = request_json.get('offset_columns')
        if self.offset_columns is None:
            self.offset_columns = []
        self.offset_columns = list(dict.fromkeys(str(value) for value in self.offset_columns if value))

        if 'splitPolicy' in request_json: # when creating
            self.input_dataset = request_json.get('trainSet', "")
            self.analysis_name = request_json.get('analysisName', "")
            self.policy = request_json.get('splitPolicy', "")
            self.test_dataset_string = request_json.get('testSet', "")

        if 'model_parameters' in request_json.keys(): # when training
            self.distribution_function = self._normalize_algorithm_identifier(
                request_json.get('model_parameters', {}).get('distribution_function')
            )
            self.link_function = self._normalize_algorithm_identifier(
                request_json.get('model_parameters', {}).get('link_function')
            )
            self.elastic_net_penalty = float(request_json.get('model_parameters', {}).get('elastic_net_penalty'))
            self.l1_ratio = float(request_json.get('model_parameters', {}).get('l1_ratio'))
            self.model_name_string = request_json.get('model_parameters', {}).get('model_name', None)
            self.theta = request_json.get('model_parameters', {}).get('theta', None)
            self.power = request_json.get('model_parameters', {}).get('power', None)
            self.variance_power = request_json.get('model_parameters', {}).get('variance_power', None)

        self.variables = dict(request_json.get('variables', {}))
        self.variables_list = [{'name': key, **value} for key, value in self.variables.items()]
        self.interaction_variables =  request_json.get('interaction_variables', [])
        self.log_configuration()

    def validate_setup(self):
        
        required_parameters = {
            "distribution_function": self.distribution_function,
            "link_function": self.link_function,
            "elastic_net_penalty": self.elastic_net_penalty,
            "l1_ratio": self.l1_ratio,
            "model_name_string": self.model_name_string,
            "variables": self.variables,
        }
        
        missing_parameters = [param for param, value in required_parameters.items() if value is None]
        if missing_parameters:
            missing_params_str = ", ".join(missing_parameters)
            logger.error(f"Missing required parameters: {missing_params_str}")
            raise ValueError(f"Missing required parameters: {missing_params_str}")

        logger.debug("Successfully set up DKUVisualMLConfig with attributes:")
        return True
    
    
    def log_configuration(self):
        for attr, value in vars(self).items():
            logger.debug(f"Visual ML config set up with {attr}: {value}")
            
        
    
