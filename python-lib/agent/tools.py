
from typing import Any, Dict, List, Optional, Union
from backend.services import DataikuDataService

service = DataikuDataService()

def train_model(
	ml_task_id: str,
	analysis_id: str,
	targetColumn: str,
	exposureColumn: str,
	splitPolicy: str,
	trainSet: str,
	analysisName: str,
	model_parameters: Dict[str, Any],
	variables: Dict[str, Any],
	interaction_variables: Optional[List[Any]] = None,
	testSet: Optional[str] = None,
) -> Dict[str, Any]:
	"""
	Train a model.
	model_parameters and variables are mandatory. Find their formats below.
	Args:
		ml_task_id: The ML task ID.
		analysis_id: The analysis ID.
		targetColumn: Target column name.
		exposureColumn: Exposure column name.
		model_parameters: Dict of model parameters "distribution_function" ("Gamma", "Gaussian", "Inverse Gaussian", "Poisson", "Negative Binomial", "Tweedie"), "link_function" ("CLogLog", "Log", "Logit", "Cauchy", "Identity", "Power", "Inverse Power", "Inverse Squared"), "elastic_net_penalty", "l1_ratio", "model_name", "theta", "power" (when using the power link), "variance_power" (when using the Tweedie distribution).
		variables: Dict of variable objects using the format {<variable_name>: {"type" ("categorical", "numerical"), "role" ("REJECT", "INPUT", "Target", "Exposure"), included" (boolean), "base_level" ("Rural", 50, ...)}}.
		interaction_variables: (optional) List of interaction variables.
	Returns:
		Service response dict.
	"""
	try:
		request_json = dict(
			ml_task_id=ml_task_id,
			analysis_id=analysis_id,
		)
		if targetColumn is not None:
			request_json['targetColumn'] = targetColumn
		if exposureColumn is not None:
			request_json['exposureColumn'] = exposureColumn
		if splitPolicy is not None:
			request_json['splitPolicy'] = splitPolicy
		if trainSet is not None:
			request_json['trainSet'] = trainSet
		if analysisName is not None:
			request_json['analysisName'] = analysisName
		if testSet is not None:
			request_json['testSet'] = testSet
		if model_parameters is not None:
			request_json['model_parameters'] = model_parameters
		if variables is not None:
			request_json['variables'] = variables
		if interaction_variables is not None:
			request_json['interaction_variables'] = interaction_variables
		return service.train_model(request_json)
	except Exception as e:
		return {'error': str(e)}

def deploy_model(id: str, input_dataset: str, experiment_name: str) -> Dict[str, Any]:
	"""
	Deploy a model using the DataikuDataService.
	Args:
		id: Model ID.
		input_dataset: Input dataset name.
		experiment_name: Experiment name.
	Returns:
		Service response dict.
	"""
	try:
		request_json = dict(id=id, input_dataset=input_dataset, experiment_name=experiment_name)
		return service.deploy_model(request_json)
	except Exception as e:
		return {'error': str(e)}

def delete_model(id: str, input_dataset: str, experiment_name: str) -> Dict[str, Any]:
	"""
	Delete a model using the DataikuDataService.
	Args:
		id: Model ID.
		input_dataset: Input dataset name.
		experiment_name: Experiment name.
	Returns:
		Service response dict.
	"""
	try:
		request_json = dict(id=id, input_dataset=input_dataset, experiment_name=experiment_name)
		return service.delete_model(request_json)
	except Exception as e:
		return {'error': str(e)}

def get_latest_mltask_params(id: str) -> Dict[str, Any]:
	"""
	Get the latest ML task parameters for a model.
	Args:
		id: Model ID.
	Returns:
		Setup parameters dict.
	"""
	try:
		request_json = dict(id=id)
		return service.get_latest_mltask_params(request_json)
	except Exception as e:
		return {'error': str(e)}

def get_variables(id: str) -> List[Any]:
	"""
	Get variables used in a model.
	Args:
		id: Model ID.
	Returns:
		List of variables.
	"""
	try:
		request_json = dict(id=id)
		return service.get_variables(request_json)
	except Exception as e:
		return {'error': str(e)}

def get_models(mlTaskId: str, analysisId: str) -> List[Any]:
	"""
	Get all models for a given ML task and analysis.
	Args:
		mlTaskId: ML task ID.
		analysisId: Analysis ID.
	Returns:
		List of models.
	"""
	try:
		request_json = dict(mlTaskId=mlTaskId, analysisId=analysisId)
		return service.get_models(request_json)
	except Exception as e:
		return {'error': str(e)}

def get_univariate_analysis(id: str, trainTest: bool, variable: str) -> List[Any]:
	"""
	Get the univariate comparison between predicted and observed, bucketed for the selected variable
	Args:
		id: Model ID.
		trainTest: Boolean, True for train set, False for test set.
		variable: Variable name.
	Returns:
		List of prediction and observed for each bucket of variable.
	"""
	try:
		request_json = dict(id=id, trainTest=trainTest, variable=variable)
		return service.get_predicted_base(request_json)
	except Exception as e:
		return {'error': str(e)}

def get_base_values(id: str) -> List[Any]:
	"""
	Get base values for a model.
	Args:
		id: Model ID.
	Returns:
		List of base values.
	"""
	try:
		request_json = dict(id=id)
		return service.get_base_values(request_json)
	except Exception as e:
		return {'error': str(e)}

def get_lift_data(id: str, nbBins: int, trainTest: bool) -> List[Any]:
	"""
	Get lift chart data for a model.
	Args:
		id: Model ID.
		nbBins: Number of bins.
		trainTest: Boolean, True for train set, False for test set.
	Returns:
		List of lift chart data.
	"""
	try:
		request_json = dict(id=id, nbBins=nbBins, trainTest=trainTest)
		return service.get_lift_data(request_json)
	except Exception as e:
		return {'error': str(e)}

def get_relativities(id: str) -> List[Any]:
	"""
	Get relativities for a model.
	Args:
		id: Model ID.
	Returns:
		List of relativities.
	"""
	try:
		request_json = dict(id=id)
		return service.get_relativities(request_json)
	except Exception as e:
		return {'error': str(e)}

def get_variable_level_stats(id: str) -> List[Any]:
	"""
	Get variable level statistics for a model.
	Args:
		id: Model ID.
	Returns:
		List of variable level stats.
	"""
	try:
		request_json = dict(id=id)
		return service.get_variable_level_stats(request_json)
	except Exception as e:
		return {'error': str(e)}

def get_model_metrics(id: str) -> Dict[str, Any]:
	"""
	Get model metrics (AIC, BIC, Deviance) for a model.
	Args:
		id: Model ID.
	Returns:
		Dict of metrics.
	"""
	try:
		request_json = dict(id=id)
		return service.get_model_metrics(request_json)
	except Exception as e:
		return {'error': str(e)}

def export_model(id: str) -> bytes:
	"""
	Export a model as CSV.
	Args:
		id: Model ID.
	Returns:
		CSV bytes.
	"""
	try:
		request_json = dict(id=id)
		return service.export_model(request_json)
	except Exception as e:
		return {'error': str(e)}

def export_variable_level_stats(id: str) -> bytes:
	"""
	Export variable level stats as CSV.
	Args:
		id: Model ID.
	Returns:
		CSV bytes.
	"""
	try:
		request_json = dict(id=id)
		return service.export_variable_level_stats(request_json)
	except Exception as e:
		return {'error': str(e)}

def export_lift_chart(id: str, nbBins: int, trainTest: bool) -> bytes:
	"""
	Export lift chart as CSV.
	Args:
		id: Model ID.
		nbBins: Number of bins.
		trainTest: Boolean, True for train set, False for test set.
	Returns:
		CSV bytes.
	"""
	try:
		request_json = dict(id=id, nbBins=nbBins, trainTest=trainTest)
		return service.export_lift_chart(request_json)
	except Exception as e:
		return {'error': str(e)}

def export_one_way(id: str, variable: str, trainTest: bool, rescale: str) -> bytes:
	"""
	Export one-way chart as CSV.
	Args:
		id: Model ID.
		variable: Variable name.
		trainTest: Boolean, True for train set, False for test set.
		rescale: Rescale option.
	Returns:
		CSV bytes.
	"""
	try:
		request_json = dict(id=id, variable=variable, trainTest=trainTest, rescale=rescale)
		return service.export_one_way(request_json)
	except Exception as e:
		return {'error': str(e)}

def get_dataset_columns(dataset: str, exposure: str) -> List[Any]:
	"""
	Get dataset columns and base levels.
	Args:
		dataset: Dataset name.
		exposure: Exposure column name.
	Returns:
		List of columns and base levels.
	"""
	try:
		request_json = dict(dataset=dataset, exposure=exposure)
		return service.get_dataset_columns(request_json)
	except Exception as e:
		return {'error': str(e)}

def get_project() -> Dict[str, Any]:
	"""
	Get the current project key.
	Returns:
		Dict with projectKey.
	"""
	try:
		return service.get_project()
	except Exception as e:
		return {'error': str(e)}

def get_ml_tasks() -> List[Any]:
	"""
	Get all ML tasks in the project.
	Returns:
		List of ML tasks.
	"""
	try:
		return service.get_ml_tasks()
	except Exception as e:
		return {'error': str(e)}

def get_datasets() -> List[Any]:
	"""
	Get all datasets in the project.
	Returns:
		List of datasets.
	"""
	try:
		return service.get_datasets()
	except Exception as e:
		return {'error': str(e)}


def create_ml_task(
	targetColumn: Optional[str] = None,
	exposureColumn: Optional[str] = None,
	splitPolicy: Optional[str] = None,
	trainSet: Optional[str] = None,
	analysisName: Optional[str] = None,
	testSet: Optional[str] = None,
	variables: Optional[Dict[str, Any]] = None,
	interaction_variables: Optional[List[Any]] = None
) -> Dict[str, Any]:
	"""
	Create a new ML task using splitPolicy-related parameters.
	Args:
		targetColumn: (optional) Target column name.
		exposureColumn: (optional) Exposure column name.
		splitPolicy: (optional) Split policy string.
		trainSet: (optional) Training set name.
		analysisName: (optional) Analysis name.
		testSet: (optional) Test set name.
		variables: (optional) Dict of variables.
		interaction_variables: (optional) List of interaction variables.
	Returns:
		Service response dict.
	"""
	try:
		request_json = {}
		if targetColumn is not None:
			request_json['targetColumn'] = targetColumn
		if exposureColumn is not None:
			request_json['exposureColumn'] = exposureColumn
		if splitPolicy is not None:
			request_json['splitPolicy'] = splitPolicy
		if trainSet is not None:
			request_json['trainSet'] = trainSet
		if analysisName is not None:
			request_json['analysisName'] = analysisName
		if testSet is not None:
			request_json['testSet'] = testSet
		if variables is not None:
			request_json['variables'] = variables
		if interaction_variables is not None:
			request_json['interaction_variables'] = interaction_variables
		return service.create_ml_task(request_json)
	except Exception as e:
		return {'error': str(e)}

def get_variables_for_dataset(name: str) -> List[Any]:
	"""
	Get variables for a given dataset.
	Args:
		name: Dataset name.
	Returns:
		List of variables.
	"""
	try:
		request_json = dict(name=name)
		return service.get_variables_for_dataset(request_json)
	except Exception as e:
		return {'error': str(e)}
