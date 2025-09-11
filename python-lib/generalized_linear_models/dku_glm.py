from glum import GeneralizedLinearRegressor
from glum import BinomialDistribution
from glum import GammaDistribution
from glum import NormalDistribution
from glum import InverseGaussianDistribution
from glum import TweedieDistribution
from glum import PoissonDistribution
from glum import NegativeBinomialDistribution

import numpy as np
from sklearn.base import BaseEstimator, ClassifierMixin
import generalized_linear_models.link as link
import pandas as pd
from generalized_linear_models.interactions import Interactions

class BaseGLM(BaseEstimator, ClassifierMixin):
    """
    Base class for GLM
    Binary and Regression GLM inherit from here
    """
    def __init__(self, family_name="gaussian", binomial_link="logit", gamma_link="inverse_power", gaussian_link="identity", inverse_gaussian_link="inverse_squared",
                 poisson_link="log", negative_binomial_link="log", tweedie_link="log", alpha=1, power=1, penalty=0.0, l1_ratio=0.5,
                 var_power=1, offset_mode="BASIC", training_dataset=None, offset_columns=None, exposure_columns=None,
                 interaction_columns_first=None, interaction_columns_second=None,
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
        self.family_glum_class = None
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
        if isinstance(l1_ratio, list):
            for l in l1_ratio:
                if l < 0 or l > 1:
                    raise ValueError('l1_ratio should be between 0 and 1')
        else:
            if l1_ratio < 0 or l1_ratio > 1:
                raise ValueError('l1_ratio should be between 0 and 1')
        self.l1_ratio = l1_ratio
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
        self.interaction_columns_first = interaction_columns_first
        self.interaction_columns_second = interaction_columns_second
        self.column_labels = column_labels
        self.training_dataset = training_dataset
        self.removed_indices = None
        self.assign_family()
        self.assign_family_glum_class()
        self.aic_value = None
        self.bic_value = None
        self.deviance_value = None

    def get_link_function(self):
        """
        gets the glum link function based on the
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
            return 'cloglog'
        elif user_link == 'log':
            return 'log'
        elif user_link == 'logit':
            return 'logit'
        elif user_link == 'identity':
            return 'identity'
        elif user_link == 'cauchy':
            return link.Cauchy()
        elif user_link == 'power':
            return link.Power(self.power)
        elif user_link == 'inverse_power':
            return link.InversePower(self.power)
        elif user_link == 'inverse_squared':
            return link.InverseSquared()
        else:
            raise ValueError("Unsupported link")

    def get_family(self):
        """
        takes in user defined family variable
        and returns the family
        """
        if self.family_name == 'binomial':
            return 'binomial'

        elif self.family_name == "gamma":
            return 'gamma'

        elif self.family_name == "gaussian":
            return 'gaussian'

        elif self.family_name == "inverse_gaussian":
            return 'inverse.gaussian'

        elif self.family_name == "negative_binomial":
            return 'negative.binomial (' + str(self.alpha) + ')'

        elif self.family_name == "poisson":
            return 'poisson'

        elif self.family_name == "tweedie":
            return 'tweedie (' + str(self.var_power) + ')'
        else:
            raise ValueError("Unsupported family")
        
    def get_family_glumn_class(self):
        if self.family_name == 'binomial':
            return BinomialDistribution()
        elif self.family_name == "gamma":
            return GammaDistribution()

        elif self.family_name == "gaussian":
            return NormalDistribution()

        elif self.family_name == "inverse_gaussian":
            return InverseGaussianDistribution()

        elif self.family_name == "negative_binomial":
            return NegativeBinomialDistribution(self.alpha)

        elif self.family_name == "poisson":
            return PoissonDistribution()

        elif self.family_name == "tweedie":
            return TweedieDistribution(self.var_power)
        else:
            raise ValueError("Unsupported family")
        
    def assign_family_glum_class(self):
        self.family_glum_class = self.get_family_glumn_class()

    def assign_family(self):
        """
        converts string inputs of family & link
        into glum family and makes it an attribute
        """
        self.link = self.get_link_function()
        self.family = self.get_family()

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

    def set_interactions(self):
        self.interactions = Interactions(self.interaction_columns_first, self.interaction_columns_second)

    def fit_model(self, X, y, sample_weight=None, prediction_is_classification=False):
        """
        fits a GLM model
        """
        self.classes_ = list(set(y))
        offsets, exposures = self.get_offsets_and_exposures(X)
        self.set_interactions()
        
        X = self.process_fixed_columns(X)
        
        X = self.interactions.transform(X, self.final_labels)
        
        offset_output = self.compute_aggregate_offset(offsets, exposures)
        
        #  fits and stores glum glm
        self.fitted_model = GeneralizedLinearRegressor(alpha=self.penalty, l1_ratio=self.l1_ratio, fit_intercept=True,
                                            family=self.family, link=self.link)
        X_df = pd.DataFrame(X, columns=self.final_labels)
        self.fitted_model.fit(X_df, y, sample_weight=sample_weight, offset=offset_output, store_covariance_matrix=True)
        
        self.aic_value = np.round(self.fitted_model.aic(X_df, y), 2)
        self.bic_value = np.round(self.fitted_model.bic(X_df, y), 2)
        
        predictions = self.fitted_model.predict(X_df)
        self.deviance_value = np.round(self.family_glum_class.deviance(y ,predictions), 2)
        
        self.coef_table = self.fitted_model.coef_table()
        
        self.compute_coefs(prediction_is_classification)
        
    def compute_coefs(self, prediction_is_classification):
        """
        adds attributes for explainability
        """
        # removes first value which is the intercept
        # other values correspond to fitted coefs (hence excludes offsets and exposures)
        self.coef_ = self.fitted_model.coef_#np.array(self.fitted_model.params[1:])
        if prediction_is_classification:
            self.intercept_ = [float(self.fitted_model.intercept_)]
        else:
            self.intercept_ = float(self.fitted_model.intercept_)
        # the column labels include offsets and exposures
        # so we need to insert 0 coefs for these columns to ensure consistency
        if self.removed_indices is not None:
            self.removed_indices = list(set(self.removed_indices))
            # 0 are inserted one by one in ascending order
            # because inserting a value at index = len + 1 fails
            for index in sorted(self.removed_indices):
                self.coef_ = np.insert(self.coef_, index, 0)
        if prediction_is_classification:
            self.coef_ = np.array([self.coef_])

    def set_column_labels(self, column_labels):
        # in order to preserve the attribute `column_labels` when cloning
        # the estimator, we have declared it as a keyword argument in the
        # `__init__` and set it there
        self.column_labels = column_labels
    
    def is_NA_column(self, label):
        """
        returns True if column is generated by DSS to represent potential NA values
        """
        return label.endswith('N/A')

    def process_fixed_columns(self, X):
        self.removed_indices = None
        self.final_labels = self.column_labels.copy()
        if self.offset_indices is not None:
            self.removed_indices = self.offset_indices
        if self.exposure_indices is not None:
            if self.removed_indices is not None:
                self.removed_indices.extend(self.exposure_indices)
            else:
                self.removed_indices = self.exposure_indices
        
        for label in self.column_labels:
            if self.is_NA_column(label):
                _, [column_index] = self.get_columns(X, [label])
                self.removed_indices.append(column_index)

        if self.removed_indices is not None:
            self.removed_indices = list(set(self.removed_indices))

            X = np.delete(X, self.removed_indices, axis=1)
            
            for ind in sorted(self.removed_indices, reverse=True):
                del self.final_labels[ind]

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
        self.set_interactions()
        X = self.process_fixed_columns(X)
        X = self.interactions.transform(X, self.final_labels)
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

        return y_pred > 0.5

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
    





