from logging_assist.logging import logger
from logging_assist.logging import logger

class DKUVisualMLConfig:
    
    def __init__(self):
        
        logger.debug("Initalising a dku visual ML config with the existing web app settings")
        
        self.prediction_type = "REGRESSION"        
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
        excluded_variables = []
        for variable in self.variables:
            included = self.variables[variable].get('included')
            if not included:
                excluded_variables.append(variable)
        return excluded_variables

        
    def get_model_features(self):
        
        target_variable = self.get_target_variable()
        included_variables = self.get_included_variables()
        
        model_features= [var for var in included_variables if var not in {target_variable, self.exposure_column}]
        
        if len(model_features)>0:
            return model_features
        else: 
            return []

    def update_model_parameters(self, request_json):
        
        logger.debug("Initalising DKUVisualMLConfig ")
        self.target_column = request_json.get('targetColumn')
        self.exposure_column = request_json.get('exposureColumn')

        if 'splitPolicy' in request_json: # when creating
            self.input_dataset = request_json.get('trainSet', "")
            self.analysis_name = request_json.get('analysisName', "")
            self.policy = request_json.get('splitPolicy', "")
            self.test_dataset_string = request_json.get('testSet', "")

        if 'model_parameters' in request_json.keys(): # when training
            self.distribution_function = request_json.get('model_parameters', {}).get('distribution_function').lower()
            self.link_function = request_json.get('model_parameters', {}).get('link_function').lower()
            self.elastic_net_penalty = float(request_json.get('model_parameters', {}).get('elastic_net_penalty', 0.0))
            self.l1_ratio = float(request_json.get('model_parameters', {}).get('l1_ratio', 0.5))
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
            
        
    