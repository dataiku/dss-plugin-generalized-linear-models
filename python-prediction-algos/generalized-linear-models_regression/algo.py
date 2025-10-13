import sys
if sys.version_info[0] < 3:
    raise Exception(
        "Training environment must use Python 3, please update in Design > Advanced > Runtime "
        "environment")
from dataiku.doctor.plugins.custom_prediction_algorithm import BaseCustomPredictionAlgorithm
from generalized_linear_models.dku_glm import RegressionGLM
from commons import check_params


class CustomPredictionAlgorithm(BaseCustomPredictionAlgorithm):

    def __init__(self, prediction_type=None, params=None):
        print('backend change')
        print('params')
        print(params)
        self.params = check_params(params)
        print(self.params)
        self.clf = RegressionGLM(**params)
        super(CustomPredictionAlgorithm, self).__init__(prediction_type, self.params)

    def get_clf(self):
        return self.clf
