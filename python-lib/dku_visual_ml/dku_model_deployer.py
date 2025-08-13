import logging
from logging_assist.logging import logger
from dku_visual_ml.custom_configurations import dku_dataset_selection_params
from dku_visual_ml.dku_base import DataikuClientProject
from typing import List, Any

class VisualMLModelDeployer(DataikuClientProject):
    """
    A class to deploy GLMs in the flow.
    """
    
    def __init__(self, mltask, saved_model_id=None):
        super().__init__()
        logger.info("Initializing a Visual ML deployer")
        self.saved_model_id = saved_model_id
        if saved_model_id:
            if saved_model_id in [k['id'] for k in self.project.list_saved_models()]:
                self.saved_model = self.project.get_saved_model(saved_model_id)
            else:
                self.saved_model_id = None
                self.saved_model = None
        else:
            self.saved_model = None
        self.mltask = mltask
        self.webapp_id = None
    
    def _set_webapp_id(self, webapp_id):
        self.webapp_id = webapp_id

    def _set_saved_model_attribute(self, saved_model_id):
        self.saved_model_id = saved_model_id
        self.saved_model = self.project.get_saved_model(saved_model_id)
        webapp = self.project.get_webapp(self.webapp_id)
        settings = webapp.get_settings()
        settings.get_raw()['config']['saved_model_id'] = self.saved_model_id
        settings.save()

    def deploy_model(self, model_id, input_dataset, experiment_name):
        """
        Deploys the model model_id to the flow.

        """
        logger.info(f"Attempting to deploy the model {model_id} to the flow.")

        if self.saved_model:
            logger.debug(f"Using existing saved Model ID to deploy {self.saved_model_id}")
            try:
                model_details = self.mltask.redeploy_to_flow(model_id, saved_model_id=self.saved_model_id)
                logger.info(f"Successfully used a saved Model ID to deploy {self.saved_model_id}")
                return model_details
            except Exception as e:
                raise Exception(e)
        else:
            logger.debug("Saved model not present - Creating new Model ID to deploy")
            model_name = experiment_name + "_Model"
            model_details = self.mltask.deploy_to_flow(model_id, model_name=model_name, train_dataset=input_dataset)
            saved_model_id = model_details.get("savedModelId")
            self._set_saved_model_attribute(saved_model_id)
            logger.info(f"Successfully Deployed Model")
            return model_details
    
    def get_deployed_models(self):
        
        version_mapping = {}

        if (self.saved_model == None) or self.saved_model == "None" :
            logger.debug("Saved Model Not initalised, deployed models not retrieved")
            return version_mapping
        
        versions = self.saved_model.list_versions()
        for version in versions:
            version_details = self.saved_model.get_version_details(version['id'])

            full_model_id = version_details.details['smOrigin']['fullModelId']

            version_mapping[full_model_id] = version['id']
        
        return version_mapping

    def set_new_active_version(self, model_id, input_dataset, experiment_name):
        
        self.deployed_models = self.get_deployed_models()
        
        if model_id in self.deployed_models.keys():
            self.saved_model.set_active_version(self.deployed_models[model_id])
            logger.info(f"Model {model_id} activated successfully.")
        else:
            self.deploy_model(model_id, input_dataset, experiment_name)
            self.deployed_models = self.get_deployed_models()
            logger.info(f"Model {model_id} deployed successfully and set to active version.")

    def delete_model(self, model_id):

        self.deployed_models = self.get_deployed_models()
                
        if model_id in self.deployed_models.keys():
            self.saved_model.delete_versions([self.deployed_models[model_id]])