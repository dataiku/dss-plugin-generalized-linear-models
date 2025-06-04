from glm_handler.dku_relativites_calculator import RelativitiesCalculator
from glm_handler.dku_model_deployer import ModelDeployer
from glm_handler.glm_data_handler import GlmDataHandler
from time import time
from logging_assist.logging import logger
from dku_visual_ml.dku_model_retrival import VisualMLModelRetriver
from chart_formatters.lift_chart import LiftChartFormatter
from chart_formatters.variable_level_stats import VariableLevelStatsFormatter
data_handler = GlmDataHandler()
from model_cache.model_cache import ModelCache

model_cache = ModelCache()

def setup_model_cache(global_dku_mltask, model_deployer):
    if global_dku_mltask is None:
        logger.warning("global_dku_mltask is None. Exiting setup_model_cache.")
        return

    elif model_deployer is None:
        logger.warning("model_deployer is None. Exiting setup_model_cache.")
        return
    
    else:
        logger.info("Updating Model cache")
        model_cache_setup_time = time()
        model_id_list = global_dku_mltask.get_trained_models_ids()
        logger.debug(f"Model ID list obtained for the cache is: {model_id_list}")

        for model_id in model_id_list:

            loop_start_time = time()
            model_deployer.set_new_active_version(model_id)
            model_retriever = VisualMLModelRetriver(
                model_id
            )
        return model_cache

def update_model_cache(global_dku_mltask, model_cache):
    logger.info("Updating model cache")
    
    model_id_list = global_dku_mltask.get_trained_models_ids()
    logger.debug(f"Model ID list obtained: {model_id_list}")
    
    for model_id in model_id_list:
        if not model_cache.model_exists(model_id):
            logger.debug(f"Model ID {model_id} not found in cache. Updating cache.")

            model_retriever = VisualMLModelRetriver(
                model_id
            )
            relativities_calculator = RelativitiesCalculator(
                data_handler,
                model_retriever
            )
            model1_predicted_base = relativities_calculator.get_formated_predicted_base()
            base_values = relativities_calculator.get_base_values()
            
            relativities = relativities_calculator.get_relativities_df()
            relativities_interaction = relativities_calculator.get_relativities_interactions_df()
            
            relativities_dict = relativities_calculator.relativities
            variable_level_stats = VariableLevelStatsFormatter(
                model_retriever, data_handler, relativities_calculator
            )
            variable_stats=variable_level_stats.get_variable_level_stats()
            
            lift_chart = LiftChartFormatter(
                     model_retriever,
                     data_handler
            ) 
            train_set = relativities_calculator.train_set
            test_set = relativities_calculator.test_set

            if train_set is None:
                raise ValueError("Train set is not defined in relativities_calculator")
            if test_set is None:
                raise ValueError("Test set is not defined in relativities_calculator")

            lift_chart_data = lift_chart.get_lift_chart(8, train_set, test_set)
            

            model_cache.add_model(model_id, 
                                 relativities, 
                                 relativities_interaction,
                                 model1_predicted_base,
                                 base_values,
                                 relativities_dict,
                                 lift_chart_data,
                                 variable_stats)

            logger.debug(f"Model ID {model_id} cache updated.")
    
    logger.info("Model cache update complete.")
    return model_cache
