from logging_assist.logging import logger
from model_cache.model_conformity_checker import ModelConformityChecker

class ModelCache(ModelConformityChecker):
    def __init__(self):
        super().__init__()
        self.cache = {}

    def add_model_object(self, 
                        model_id,
                        model_object_key, 
                        model_object_value
                        ):
        """
        Add a model object to the cache.

        Parameters:
        model_name (str): The name of the model.
        model_object_key: The model object key to be cached.
        model_object_value: The model object key to be cached.
        """
        
        is_conform = self.check_model_conformity(model_id)
        
        if is_conform:
            if model_id in self.cache.keys():
                self.cache[model_id][model_object_key] = model_object_value
            else:
                self.cache[model_id] = {model_object_key: model_object_value}
            logger.info(f"Model Object '{model_object_key}' for '{model_id}' added to cache.")
        else:
            logger.info(f"Model '{model_id}' does not conform, not added to cache")

    def add_model(self, 
                  model_id, 
                  relativities, 
                  relativities_interaction,
                  predicted_and_base, 
                  base_values,
                  relativities_dict,
                  lift_chart_data,
                  variable_stats
                 ):
        """
        Add a model to the cache.

        Parameters:
        model_name (str): The name of the model.
        model: The model object to be cached.
        """
        
        is_conform = self.check_model_conformity(model_id)
        
        if is_conform:
            self.cache[model_id] = {
                        'relativities': relativities,
                        'relativities_interaction': relativities_interaction,
                        'predicted_and_base': predicted_and_base,
                        'base_values': base_values,
                        'relativities_dict': relativities_dict,
                        'lift_chart_data':lift_chart_data,
                        'variable_stats':variable_stats,
                    }
            logger.info(f"Model '{model_id}' added to cache.")
        else:
            logger.info(f"Model '{model_id}' does not conform, not added to cache")

    def get_model(self, model_name):
        """
        Retrieve a model from the cache.

        Parameters:
        model_name (str): The name of the model to retrieve.

        Returns:
        The model object if found, None otherwise.
        """
        if model_name in self.cache:
            print(f"Model '{model_name}' retrieved from cache.")
            return self.cache[model_name]
        else:
            print(f"Model '{model_name}' not found in cache.")
            return None

    def model_exists(self, model_name):
        """
        Check if a model exists in the cache.

        Parameters:
        model_name (str): The name of the model to check.

        Returns:
        True if the model exists in the cache, False otherwise.
        """
        return model_name in self.cache

    def remove_model(self, model_name):
        """
        Remove a model from the cache.

        Parameters:
        model_name (str): The name of the model to remove.
        """
        if model_name in self.cache:
            del self.cache[model_name]
            print(f"Model '{model_name}' removed from cache.")
        else:
            print(f"Model '{model_name}' not found in cache.")

    def list_models(self):
        """
        List all models in the cache.

        Returns:
        A list of model names.
        """
        return list(self.cache.keys())