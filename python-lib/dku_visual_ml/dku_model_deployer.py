import dataikuapi
from logging_assist.logging import logger
from dku_visual_ml.dku_base import DataikuClientProject

class VisualMLModelDeployer(DataikuClientProject):
    """
    A class to deploy GLMs in the flow.
    """
    
    def __init__(self):
        super().__init__()
        logger.info("Initializing a Visual ML deployer")

    def deploy_model(self, model_id, input_dataset, experiment_name):
        """
        Deploys the model model_id to the flow.

        """
        logger.info(f"Attempting to deploy the model {model_id} to the flow.")

        mltask = dataikuapi.dss.ml.DSSMLTask.from_full_model_id(
                    self.client, 
                    model_id, 
                    self.project.project_key
                )
        
        saved_model = self.get_saved_model(experiment_name)

        if saved_model:
            logger.debug(f"Using existing saved Model ID to deploy {saved_model.id}")
            try:
                model_details = mltask.redeploy_to_flow(model_id, saved_model_id=saved_model.id)
                logger.info(f"Successfully used a saved Model ID to deploy {saved_model.id}")
                return model_details
            except Exception as e:
                raise Exception(e)
        else:
            logger.debug("Saved model not present - Creating new Model ID to deploy")
            model_name = experiment_name + "_Model"
            model_details = mltask.deploy_to_flow(model_id, model_name=model_name, train_dataset=input_dataset)
            logger.info(f"Successfully Deployed Model")
            return model_details
    
    def get_saved_model(self, experiment_name):
        
        model_name = experiment_name + "_Model"
        saved_models = self.project.list_saved_models()
        matching_sm = [sm['id'] for sm in saved_models if sm['name']==model_name]
        if len(matching_sm) == 1:
            saved_model_id = matching_sm[0]
            return self.project.get_saved_model(saved_model_id)
        else:
            return None

    def get_deployed_models(self, saved_model):

        version_mapping = {}

        if (saved_model == None) or saved_model == "None" :
            logger.debug("Saved Model Not initalised, deployed models not retrieved")
            return version_mapping
        
        versions = saved_model.list_versions()
        for version in versions:
            version_details = saved_model.get_version_details(version['id'])

            full_model_id = version_details.details['smOrigin']['fullModelId']

            version_mapping[full_model_id] = version['id']
        
        return version_mapping

    def get_analysis_name(self, analysis_id):
        analysis = self.project.get_analysis(analysis_id)
        definition = analysis.get_definition()
        name = definition.get_raw()['name']
        

    def set_new_active_version(self, model_id, input_dataset, experiment_name):
        
        len_prefix = len(input_dataset)
        analysis_name = experiment_name[(len_prefix+1):]

        saved_model = self.get_saved_model(analysis_name)
        deployed_models = self.get_deployed_models(saved_model)
        
        if model_id in deployed_models.keys():
            saved_model.set_active_version(deployed_models[model_id])
            logger.info(f"Model {model_id} activated successfully.")
        else:
            self.deploy_model(model_id, input_dataset, analysis_name)
            logger.info(f"Model {model_id} deployed successfully and set to active version.")

    def delete_model(self, model_id, input_dataset, experiment_name):

        len_prefix = len(input_dataset)
        analysis_name = experiment_name[(len_prefix+1):]

        saved_model = self.get_saved_model(analysis_name)
        deployed_models = self.get_deployed_models(saved_model)

        if model_id in deployed_models.keys():
            saved_model.delete_versions([deployed_models[model_id]])