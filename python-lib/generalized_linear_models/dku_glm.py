import statsmodels.api as sm
from statsmodels.genmod.generalized_linear_model import GLMResults
import numpy as np
from sklearn.base import BaseEstimator, ClassifierMixin


class BaseGLM(BaseEstimator, ClassifierMixin):
    """
    Base class for GLM
    Binary and Regression GLM inherit from here
    """

    def __init__(self, family_name, binomial_link, gamma_link, gaussian_link, inverse_gaussian_link,
                 poisson_link, negative_binomial_link, tweedie_link, alpha, power, penalty,
                 var_power, offset_mode, training_dataset=None, offset_columns=None, exposure_columns=None,
                 column_labels=None):

        self.family_name = family_name
        self.binomial_link = binomial_link
        self.gamma_link = gamma_link
        self.gaussian_link = gaussian_link
        self.inverse_gaussian_link = inverse_gaussian_link
        self.poisson_link = poisson_link
        self.negative_binomial_link = negative_binomial_link
        self.tweedie_link = tweedie_link
        self.family = None
        if family_name == 'negative_binomial':
            if alpha < 0.01 or alpha > 2:
                raise ValueError('alpha should be between 0.01 and 2, current value of ' + str(alpha) + ' unsupported')
        self.alpha = alpha
        if (family_name == 'negative_binomial' and negative_binomial_link == 'power') or (
                family_name == 'tweedie' and tweedie_link == 'power'):
            if not isinstance(power, (int, float)):
                raise ValueError('power should be defined with a numeric value, current value of ' + str(
                    power) + ' unsupported, type: ' + str(type(power)))
        self.power = power
        if isinstance(penalty, list):
            for p in penalty:
                if p < 0:
                    raise ValueError('penalty should be positive')
        else:
            if penalty < 0:
                raise ValueError('penalty should be positive')
        self.penalty = penalty
        if family_name == 'tweedie':
            if not isinstance(var_power, (int, float)):
                raise ValueError('var_power should be defined with a numeric value, current value of ' + str(
                    var_power) + ' unsupported')
        self.var_power = var_power
        self.fit_intercept = True
        self.intercept_scaling = 1
        self.fitted_model = None
        self.coef_ = None
        self.intercept_ = None
        self.classes_ = None
        self.offset_mode = offset_mode
        self.offset_columns = offset_columns
        self.offset_indices = []
        self.exposure_columns = exposure_columns
        self.exposure_indices = []
        self.column_labels = column_labels
        self.training_dataset = training_dataset
        self.removed_indices = None
        self.assign_family()

    def get_link_function(self):
        """
        gets the statsmodel link function based on the
        user defined link on the model training screen
        """
        family_2_link_dict = {
            'binomial': self.binomial_link,
            'gamma': self.gamma_link,
            'gaussian': self.gaussian_link,
            'inverse_gaussian': self.inverse_gaussian_link,
            'poisson': self.poisson_link,
            'negative_binomial': self.negative_binomial_link,
            'tweedie': self.tweedie_link
        }

        user_link = family_2_link_dict[self.family_name]

        if user_link == 'cloglog':
            return sm.families.links.cloglog()
        elif user_link == 'log':
            return sm.families.links.log()
        elif user_link == 'logit':
            return sm.families.links.logit()
        elif user_link == 'negative_binomial':
            return sm.families.links.NegativeBinomial(self.alpha)
        elif user_link == 'power':
            return sm.families.links.Power(self.power)
        elif user_link == 'cauchy':
            return sm.families.links.cauchy()
        elif user_link == 'identity':
            return sm.families.links.identity()
        elif user_link == 'inverse_power':
            return sm.families.links.inverse_power()
        elif user_link == 'inverse_squared':
            return sm.families.links.inverse_squared()
        else:
            raise ValueError("Unsupported link")

    def get_family(self, link):
        """
        takes in user defined family variable
        and statsmodel link function
        returns the family
        """
        if self.family_name == 'binomial':
            return sm.families.Binomial(link=link)

        elif self.family_name == "gamma":
            return sm.families.Gamma(link=link)

        elif self.family_name == "gaussian":
            return sm.families.Gaussian(link=link)

        elif self.family_name == "inverse_gaussian":
            return sm.families.InverseGaussian(link=link)

        elif self.family_name == "negative_binomial":
            return sm.families.NegativeBinomial(link=link, alpha=self.alpha)

        elif self.family_name == "poisson":
            return sm.families.Poisson(link=link)

        elif self.family_name == "tweedie":
            return sm.families.Tweedie(link=link, var_power=self.var_power)
        else:
            raise ValueError("Unsupported family")

    def assign_family(self):
        """
        converts string inputs of family & link
        in to statsmodel family and makes it an attribute
        """
        link = self.get_link_function()
        self.family = self.get_family(link)

    def get_columns(self, X, important_columns):
        """
        returns an array of values specified by column names provided
        by the user
        """
        if important_columns is None:
            important_columns = []
        if len(important_columns) == 0:
            column_values = []
            column_indices = []

        else:
            for important_column in important_columns:
                if important_column not in self.column_labels:
                    raise ValueError(
                        f'The column names provided: [{important_column}], is not present in the list of columns from the dataset. Please check that the column is selected in feature handing.')

            column_indices = [self.column_labels.index(important_column) for important_column in important_columns]
            column_values = X[:, column_indices]

        return column_values, column_indices

    def compute_aggregate_offset(self, offsets, exposures):
        offset_output = None
        if len(offsets) > 0:
            offsets = offsets.sum(axis=1)
            offset_output = offsets

        if len(exposures) > 0:
            if (exposures <= 0).any():
                raise ValueError('Exposure columns contains some negative values. Please make sure that the exposure column is not rescaled in feature handling.')
            exposures = np.log(exposures)
            exposures = exposures.sum(axis=1)
            if offset_output is None:
                offset_output = exposures
            else:
                offset_output = offset_output + exposures

        return offset_output

    def fit_model(self, X, y, sample_weight=None, prediction_is_classification=False):
        """
        fits a GLM model
        """
        self.classes_ = list(set(y))
        offsets, exposures = self.get_offsets_and_exposures(X)

        X = self.process_fixed_columns(X)
        X = sm.add_constant(X)

        offset_output = self.compute_aggregate_offset(offsets, exposures)

        #  fits and stores statsmodel glm
        model = sm.GLM(y, X, family=self.family, offset=offset_output, var_weights=sample_weight)

        if self.penalty == 0.0:
            # fit is 10-100x faster than fit_regularized
            self.fitted_model = model.fit()
        else:
            regularized_model = model.fit_regularized(method='elastic_net', alpha=self.penalty)
            self.fitted_model = GLMResults(regularized_model.model, regularized_model.params,
                       np.linalg.pinv(np.dot(np.matrix(regularized_model.params).T, np.matrix(regularized_model.params))),
                       regularized_model.model.scale)

        self.compute_coefs(prediction_is_classification)
        if prediction_is_classification:
            self.intercept_ = [float(self.fitted_model.params[0])]
        else:
            self.intercept_ = float(self.fitted_model.params[0])

    def compute_coefs(self, prediction_is_classification):
        """
        adds attributes for explainability
        """
        # removes first value which is the intercept
        # other values correspond to fitted coefs (hence excludes offsets and exposures)
        self.coef_ = np.array(self.fitted_model.params[1:])
        # the column labels include offsets and exposures
        # so we need to insert 0 coefs for these columns to ensure consistency
        if self.removed_indices is not None:
            self.removed_indices = list(set(self.removed_indices))
            # 0 are inserted one by one in ascending order
            # because inserting a value at index = len + 1 fails
            for index in sorted(self.removed_indices):
                self.coef_ = np.insert(self.coef_, index, 0)
        # statsmodels 0 is 211 sets this to true 0
        if prediction_is_classification:
            self.coef_ = [[0 if x == 211.03485067364605 else x for x in self.coef_]]
        else:
            self.coef_ = [0 if x == 211.03485067364605 else x for x in self.coef_]

    def set_column_labels(self, column_labels):
        # in order to preserve the attribute `column_labels` when cloning
        # the estimator, we have declared it as a keyword argument in the
        # `__init__` and set it there
        self.column_labels = column_labels

    def process_fixed_columns(self, X):
        self.removed_indices = None
        if self.offset_indices is not None:
            self.removed_indices = self.offset_indices
        if self.exposure_indices is not None:
            if self.removed_indices is not None:
                self.removed_indices.extend(self.exposure_indices)
            else:
                self.removed_indices = self.exposure_indices
        if self.removed_indices is not None:
            self.removed_indices = list(set(self.removed_indices))
            X = np.delete(X, self.removed_indices, axis=1)
        return X

    def get_offsets_and_exposures(self, X):
        offsets = []
        exposures = []
        if self.offset_mode == 'OFFSETS':
            offsets, self.offset_indices = self.get_columns(X, self.offset_columns)
            if len(offsets) == 0:
                raise ValueError('OFFSETS mode is selected but no offset column is defined')
        elif self.offset_mode == 'OFFSETS/EXPOSURES':
            offsets, self.offset_indices = self.get_columns(X, self.offset_columns)
            exposures, self.exposure_indices = self.get_columns(X, self.exposure_columns)
            if len(offsets) == 0 and len(exposures) == 0:
                raise ValueError('OFFSETS/EXPOSURES mode is selected but neither offset nor exposure columns are '
                                 'defined')

        return offsets, exposures

    def predict_target(self, X):
        offsets, exposures = self.get_offsets_and_exposures(X)
        X = self.process_fixed_columns(X)

        X = sm.add_constant(X, has_constant='add')

        offset_output = self.compute_aggregate_offset(offsets, exposures)

        # makes predictions and converts to DSS accepted format
        y_pred = np.array(self.fitted_model.predict(X, offset=offset_output))
        return y_pred


class BinaryClassificationGLM(BaseGLM):

    def fit(self, X, y, sample_weight=None):
        """
        takes in training data and fits a model
        """
        self.fit_model(X, y, sample_weight, True)

    def predict(self, X):
        """
        Returns the binary target
        """
        y_pred = self.predict_target(X)
        y_pred_final = y_pred.reshape((len(y_pred), -1))

        return y_pred_final > 0.5

    def predict_proba(self, X):
        """
        Return the prediction proba
        """
        y_pred = self.predict_target(X)
        y_pred_final = y_pred.reshape((len(y_pred), -1))

        # returns p, 1-p prediction probabilities
        return np.append(1 - y_pred_final, y_pred_final, axis=1)


class RegressionGLM(BaseGLM):

    def fit(self, X, y, sample_weight=None):
        """
        takes in training data and fits a model
        """
        self.fit_model(X, y, sample_weight, False)

    def predict(self, X):
        """
        Returns the target as 1D array
        """
        return self.predict_target(X)
