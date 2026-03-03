from logging_assist.logging import logger
from dku_visual_ml.dku_base import DataikuClientProject
import dataikuapi

class ModelConformityChecker(DataikuClientProject):
    def __init__(self):
        super().__init__()


    def check_model_conformity(self, model_id):
        
        self.mltask = dataikuapi.dss.ml.DSSMLTask.from_full_model_id(
            self.client,
            model_id, 
            self.project.project_key)
        
        logger.info("Check for Model Conformity")
        model_details = self.mltask.get_trained_model_details(model_id)
        self.model_details = model_details
        
        is_glm = self.check_is_glm()
        no_offset = self.check_no_offset()
        no_weighting = self.check_no_weighting()
        train_test_split = self.check_train_test_split()
        feature_handling = self.check_feature_handling()
        
        return all([is_glm, no_offset, no_weighting, train_test_split, feature_handling])

    def check_is_glm(self):
        logger.info("Model Conformity Check: is GLM?")
        modeling = self.model_details.details['modeling']
        if modeling['algorithm'] != 'CUSTOM_PLUGIN':
            logger.info("Failed: Model Conformity Check: is GLM?")
            return False
        if modeling['plugin_python_grid']['pluginId'] != 'generalized-linear-models':
            logger.info("Failed: Model Conformity Check: is GLM?")
            return False
        logger.info("Passed: Model Conformity Check: is GLM?")
        return True

    def check_no_regularization(self):
        penalty = self.model_details.details['modeling']['plugin_python_grid']['params']['penalty']
        if penalty != [0.0]:
            return False
        return True

    def check_no_offset(self):
        logger.info("Model Conformity Check: offsets/exposure support")
        offsets = self.model_details.details['modeling']['plugin_python_grid']['params']['offset_columns']
        if len(offsets) > 0:
            logger.info(f"Passed: Model Conformity Check: offsets enabled ({len(offsets)})")
            return True
        logger.info("Passed: Model Conformity Check: no offsets")
        return True

    def check_no_weighting(self):
        logger.info("Model Conformity Check: supported weighting?")
        weight_details = self.model_details.details.get('coreParams', {}).get('weight', {})
        if not isinstance(weight_details, dict):
            logger.info("PASSED: Model Conformity Check: missing weight details treated as NO_WEIGHTING")
            return True
        weight_method = weight_details.get('weightMethod')
        if not weight_method or weight_method == 'NO_WEIGHTING':
            logger.info("PASSED: Model Conformity Check: NO_WEIGHTING")
            return True
        if weight_method == 'SAMPLE_WEIGHT':
            sample_weight_variable = weight_details.get('sampleWeightVariable')
            if sample_weight_variable:
                logger.info("PASSED: Model Conformity Check: SAMPLE_WEIGHT")
                return True
            logger.info("FAILED: SAMPLE_WEIGHT without sampleWeightVariable")
            return False
        logger.info(f"FAILED: Unsupported weighting method ({weight_method})")
        return False

    def check_train_test_split(self):
        logger.info("Model Conformity Check: train test split")
        tt_policy = self.model_details.details['splitDesc']['params']['ttPolicy']
        if tt_policy not in ['SPLIT_SINGLE_DATASET', 'EXPLICIT_FILTERING_TWO_DATASETS']:
            logger.info(f"Failed: Model Conformity Check: train test split with {tt_policy}")
            return False
        logger.info("PASSEd: Model Conformity Check: train test split")
        return True

    def check_feature_handling(self):
        logger.info("Model Conformity Check: feature handling and role validity")
        feature_handlings = self.model_details.details['preprocessing']['per_feature']
        allowed_roles = {'INPUT', 'REJECT', 'TARGET', 'WEIGHT'}
        for feature, feature_handling in feature_handlings.items():
            role = feature_handling.get('role')
            if role not in allowed_roles:
                logger.info(f"FAILED: Model Conformity Check: unsupported role '{role}' for feature '{feature}'")
                return False
            if role == 'INPUT':
                if feature_handling['type'] == 'CATEGORY':
                    if feature_handling['category_handling'] != 'CUSTOM':
                        logger.info("FAILED: Model Conformity Check: feature handling")
                        return False
                elif feature_handling['type'] == 'NUMERIC':
                    if feature_handling['rescaling'] != 'NONE':
                        logger.info("FAILED: Model Conformity Check: feature handling")
                        return False
        logger.info("PASSED: Model Conformity Check: feature handling")
        return True
