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
        logger.info("Model Conformity Check: no offsets?")
        offsets = self.model_details.details['modeling']['plugin_python_grid']['params']['offset_columns']
        if len(offsets) > 0:
            logger.info("Failed: Model Conformity Check: no offsets?")
            return False
        logger.info("Passed: Model Conformity Check: no offsets?")
        return True

    def check_no_weighting(self):
        logger.info("Model Conformity Check: no weighting?")
        weight_method = self.model_details.details['coreParams']['weight']['weightMethod']
        if weight_method != 'NO_WEIGHTING':
            logger.info("FAILED: Model Conformity Check: no weighting?")
            return False
        logger.info("PASSED: Model Conformity Check: no weighting?")
        return True

    def check_train_test_split(self):
        logger.info("Model Conformity Check: train test split")
        tt_policy = self.model_details.details['splitDesc']['params']['ttPolicy']
        if tt_policy not in ['SPLIT_SINGLE_DATASET', 'EXPLICIT_FILTERING_TWO_DATASETS']:
            logger.info(f"Failed: Model Conformity Check: train test split with {tt_policy}")
            return False
        logger.info("PASSEd: Model Conformity Check: train test split")
        return True

    def check_feature_handling(self):
        logger.info("Model Conformity Check: no weighting?")
        feature_handlings = self.model_details.details['preprocessing']['per_feature']
        for feature, feature_handling in feature_handlings.items():
            if feature_handling['role'] == 'INPUT':
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
