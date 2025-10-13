from logging_assist.logging import logger
from model_cache.model_conformity_checker import ModelConformityChecker

class ModelCache(ModelConformityChecker):
    def __init__(self):
        super().__init__()
        self.cache = {}

    def add_model_object(self, 
                        model_id: str,
                        model_object_key: str, 
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
    
    def get_or_create_cached_item(self, model_id: str, model_object_key: str, creation_func, *args, **kwargs):
        """
        Generic function to retrieve an item from the cache or create it if it doesn't exist.

        :param model_id: The ID of the model.
        :param item_key: The key for the object within the model's cache (e.g., 'train_set').
        :param creation_func: A function to call to create the item if not found.
        """

        if model_id not in self.list_models():
            logger.info(f"Cache miss for model '{model_id}'. Creating new entry.")
            model_object_value = creation_func(*args, **kwargs)
            self.add_model_object(model_id, model_object_key, model_object_value)

        model_data = self.get_model(model_id)
        if model_object_key not in model_data:
            logger.info(f"Cache miss for item '{model_object_key}' in model '{model_id}'. Creating.")
            model_object_value = creation_func(*args, **kwargs)
            self.add_model_object(model_id, model_object_key, model_object_value)
        
        logger.info(f"Cache hit for item '{model_object_key}' in model '{model_id}'.")
        return model_data.get(model_object_key)
    
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
    
