import dataiku
from dataiku.doctor.posttraining.model_information_handler import PredictionModelInformationHandler
import pandas as pd
import numpy as np
from dataiku import pandasutils as pdu
from glm_handler.dku_utils import extract_active_fullModelId
import logging
from backend.logging_settings import logger

class ModelHandler:
    """
    A class to handle interactions with a Dataiku model.

    Attributes:
        model_id (str): The ID of the model.
        model (dataiku.Model): The Dataiku model object.
        predictor (Predictor): The predictor object of the model.
        full_model_id (str): The full model ID of the active model version.
        model_info_handler (PredictionModelInformationHandler): Handler for model information.
    """

    def __init__(self, model_id, data_handler):
        """
        Initializes the ModelHandler with a specific model ID.

        Args:
            model_id (str): The ID of the model to handle.
        """
        self.model_id = model_id
        self.model = dataiku.Model(model_id)
        self.data_handler = data_handler
        

    def get_coefficients(self):
        """
        Retrieves the coefficients of the model predictor.

        Returns:
            dict: A dictionary mapping variable names to their coefficients.
        """
        coefficients = self.predictor._model.clf.coef_
        variable_names = self.predictor._model.clf.column_labels
        return dict(zip(variable_names, coefficients))

    
    def update_active_version(self):
        self.full_model_id = extract_active_fullModelId(self.model.list_versions())
        self.model_info_handler = PredictionModelInformationHandler.from_full_model_id(self.full_model_id)
        self.predictor = self.model_info_handler.get_predictor()
        self.target = self.model_info_handler.get_target_variable()
        self.compute_features()
        
    def get_model_versions(self):
        versions = self.model.list_versions()
        fmi_name = {version['snippet']['fullModelId']: version['snippet']['userMeta']['name'] for version in versions}
        return fmi_name
    
    def get_features(self):
        return [{'variable': feature, 
          'isInModel': self.features[feature]['role']=='INPUT', 
          'variableType': 'categorical' if self.features[feature]['type'] == 'CATEGORY' else 'numeric'} for feature in self.non_excluded_features]

    
    def compute_features(self):
        """ Main method to compute feature configurations. """
        self.initialize_feature_variables()
        self.compute_column_roles()
        self.filter_features()

    def initialize_feature_variables(self):
        """ Initializes basic variables related to features. """
        self.exposure = None
        self.features = self.model_info_handler.get_per_feature()

    def compute_column_roles(self):
        """ Computes special columns like exposure and offset columns from modeling params. """
        modeling_params = self.model_info_handler.get_modeling_params()
        self.offset_columns = modeling_params['plugin_python_grid']['params']['offset_columns']
        self.exposure_columns = modeling_params['plugin_python_grid']['params']['exposure_columns']
        if len(self.exposure_columns) > 0:
            self.exposure = self.exposure_columns[0]  # assumes there is only one exposure column

    def filter_features(self):
        """ Filters features based on their importance and role in the model. """
        important_columns = self.offset_columns + self.exposure_columns + [self.target]
        self.non_excluded_features = [feature for feature in self.features.keys() if feature not in important_columns]
        self.used_features = [feature for feature in self.non_excluded_features if self.features[feature]['role'] == 'INPUT']
        self.candidate_features = [feature for feature in self.non_excluded_features if self.features[feature]['role'] == 'REJECT']

    def compute_base_values(self):
        """ Main method to initialize and compute base values. """
        self.initialize_base_values()
        self.handle_preprocessing()
        self.compute_numerical_features()

    def initialize_base_values(self):
        """ Initializes dictionaries for base values and modalities. """
        self.base_values = {}
        self.modalities = {}

    def handle_preprocessing(self):
        """ Processes each step in the preprocessing pipeline. """
        preprocessing = self.predictor.get_preprocessing()
        for step in preprocessing.pipeline.steps:
            self.process_preprocessing_step(step)

    def process_preprocessing_step(self, step):
        """ Processes a single preprocessing step to extract base values and modalities. """
        try:
            self.base_values[step.input_col] = step.processor.mode_column
            self.modalities[step.input_col] = step.processor.modalities
        except AttributeError:
            pass

    def compute_numerical_features(self):
        """ Computes base values for numerical features not handled in preprocessing. """
        train_set = self.model_info_handler.get_train_df()[0].copy()
        for feature in self.used_features:
            if feature not in self.base_values:
                self.compute_base_for_feature(feature, train_set)

    def compute_base_for_feature(self, feature, train_set):
        """ Computes base value for a single feature based on its type and rescaling. """
        if self.features[feature]['type'] == 'NUMERIC' and self.features[feature]['rescaling'] == 'NONE':
            self.compute_base_for_numeric_feature(feature, train_set)
        else:
            raise Exception("feature should be handled numerically without rescaling or categorically with the custom preprocessor")

    def compute_base_for_numeric_feature(self, feature, train_set):
        """ Computes base values for numeric features without rescaling. """
        if self.exposure is not None:
            self.base_values[feature] = (train_set[feature] * train_set[self.exposure]).sum() / train_set[self.exposure].sum()
        else:
            self.base_values[feature] = train_set[feature].mean()
        self.modalities[feature] = {'min': train_set[feature].min(), 'max': train_set[feature].max()}

    def get_relativities_df(self):
        sample_train_row = self.initialize_baseline()
        baseline_prediction = self.calculate_baseline_prediction(sample_train_row)
        self.calculate_relative_predictions(sample_train_row, baseline_prediction)
        return self.construct_relativities_df()

    def initialize_baseline(self):
        train_row = self.model_info_handler.get_train_df()[0].head(1).copy()
        for feature in self.base_values.keys():
            train_row[feature] = self.base_values[feature]
        if self.exposure is not None:
            train_row[self.exposure] = 1
        return train_row

    def calculate_baseline_prediction(self, sample_train_row):
        return self.predictor.predict(sample_train_row).iloc[0][0]

    def calculate_relative_predictions(self, sample_train_row, baseline_prediction):
        self.relativities = {'base': {'base': baseline_prediction}}
        for feature in self.base_values.keys():
            self.relativities[feature] = {self.base_values[feature]: 1.0}
            if self.features[feature]['type'] == 'CATEGORY':    
                for modality in self.modalities[feature]:
                    train_row_copy = sample_train_row.copy()
                    train_row_copy[feature] = modality
                    prediction = self.predictor.predict(train_row_copy).iloc[0][0]
                    self.relativities[feature][modality] = prediction / baseline_prediction
            else:
                train_row_copy = sample_train_row.copy()
                min_value, max_value = self.modalities[feature]['min'], self.modalities[feature]['max']
                for value in np.linspace(min_value, max_value, 10):
                    train_row_copy[feature] = value
                    prediction = self.predictor.predict(train_row_copy).iloc[0][0]
                    self.relativities[feature][value] = prediction / baseline_prediction

    def construct_relativities_df(self):
        rel_df = pd.DataFrame(columns=['feature', 'value', 'relativity'])
        for feature, values in self.relativities.items():
            for value, relativity in values.items():
                rel_df = rel_df.append({'feature': feature, 'value': value, 'relativity': relativity}, ignore_index=True)
        rel_df = rel_df.append({'feature': 'base', 'value': 'base', 'relativity': self.relativities['base']['base']}, ignore_index=True)
        return rel_df

    def get_predicted_and_base(self, nb_bins_numerical=100000, class_map=None):
        self.compute_base_values()
        test_set = self.prepare_test_dataset()
        self.predict_test_data(test_set)
        base_predictions = self.compute_base_predictions(test_set, class_map)
        self.bin_numeric_features(test_set, nb_bins_numerical)
        return self.aggregate_predictions(test_set, base_predictions)
    
    def prepare_test_dataset(self):
        test_set = self.model_info_handler.get_test_df()[0].copy()
        if self.exposure is None:
            test_set['weight'] = 1
        else:
            test_set['weight'] = test_set[self.exposure]
        return test_set

    def predict_test_data(self, test_set):
        # Predict the outcomes on the test set and assign them to the 'predicted' column
        predicted = self.predictor.predict(test_set)
        test_set['predicted'] = predicted
        test_set['weighted_target'] = test_set[self.target] * test_set['weight']
        test_set['weighted_predicted'] = test_set['predicted'] * test_set['weight']

    def compute_base_predictions(self, test_set, class_map):
        base_data = {}
        for feature in self.non_excluded_features:
            copy_test_df = test_set.copy()
            for other_feature in [col for col in self.used_features if col != feature]:
                copy_test_df[other_feature] = self.base_values[other_feature]
            predictions = self.predictor.predict(copy_test_df)
            if class_map is not None:  # classification
                base_data[feature] = pd.Series([class_map[pred] for pred in predictions['prediction']])
            else:
                base_data[feature] = predictions
        return pd.concat([base_data[f] for f in base_data], axis=1, keys=['base_' + f for f in base_data])

    def bin_numeric_features(self, test_set, nb_bins_numerical):
        for feature in self.non_excluded_features:
            if self.features[feature]['type'] == 'NUMERIC' and len(test_set[feature].unique()) > nb_bins_numerical:
                test_set[feature] = pd.cut(test_set[feature], bins=nb_bins_numerical, labels=[(x.left + x.right) / 2 for x in pd.cut(test_set[feature], bins=nb_bins_numerical).categories])

    def aggregate_predictions(self, test_set, base_predictions):
        test_set = pd.concat([test_set, base_predictions], axis=1)
        for feature in self.non_excluded_features:
            test_set['base_' + feature] *= test_set['weight']
        result_df = pd.DataFrame()
        for feature in self.non_excluded_features:
            grouped = test_set.groupby(feature).agg({
                'weighted_target': 'sum',
                'weighted_predicted': 'sum',
                'weight': 'sum',
                'base_' + feature: 'sum'
            }).reset_index()
            grouped['weighted_target'] /= grouped['weight']
            grouped['weighted_predicted'] /= grouped['weight']
            grouped['base_' + feature] /= grouped['weight']
            grouped.rename(columns={feature: 'category', 'base_' + feature: 'base'}, inplace=True)
            grouped['feature'] = feature
            result_df = pd.concat([result_df, grouped], ignore_index=True)
        return result_df


   

    def get_model_predictions_on_train(self):
        """
        Generates model predictions on the training dataset.

        Returns:
            pd.DataFrame: A DataFrame of the training dataset with an additional column for predictions.
        """
        train_set = self.model_info_handler.get_train_df()[0].copy()
        predicted = self.predictor.predict(train_set)
        train_set['prediction'] = predicted
        
        return train_set
    
    def get_lift_chart(self, nb_bins):
        """
        Calculates and returns the lift chart data for the model on the training set,
        divided into the specified number of bins.

        Args:
            nb_bins (int): The number of bins to divide the data into for the lift chart.

        Returns:
            pd.DataFrame: The aggregated lift chart data with observed and predicted metrics.
        """
        train_set = self.get_model_predictions_on_train()
        train_set_df = pd.DataFrame(train_set)
        print(train_set_df.head())
        
        tempdata = self.data_handler.sort_and_cumsum_exposure(train_set_df, self.exposure)
        binned_data = self.data_handler.bin_data(tempdata, nb_bins)
        
        new_data = train_set.join(binned_data[['bin']], how='inner')
        lift_chart_data = self.data_handler.aggregate_metrics_by_bin(new_data, self.exposure, self.target)
        return lift_chart_data


    def get_link_function(self):
        """
        Retrieves the link function of the original model as a statsmodel object
        """
        return self.predictor._model.clf.get_link_function()
    
    def get_dataframe(self, dataset_type='test'):
        """
        Retrieves the specified dataset as a DataFrame.

        Args:
            dataset_type (str, optional): The type of dataset to retrieve ('test', 'train', or 'full'). Defaults to 'test'.

        Returns:
            pd.DataFrame: The requested dataset.

        Raises:
            ValueError: If an invalid dataset type is provided.
        """
        if dataset_type == 'test':
            return self.model_info_handler.get_test_df()[0]
        elif dataset_type == 'train':
            return self.model_info_handler.get_train_df()[0]
        elif dataset_type == 'full':
            return self.model_info_handler.get_full_df()[0]
        else:
            raise ValueError("Invalid dataset type")

    def preprocess_dataframe(self, df):
        """
        Preprocesses a DataFrame using the model's preprocessing steps.

        Args:
            df (pd.DataFrame): The DataFrame to preprocess.

        Returns:
            pd.DataFrame: The preprocessed DataFrame.
        """
        column_names = self.predictor.get_features()
        preprocessed_values = self.predictor.preprocess(df)[0]
        return pd.DataFrame(preprocessed_values, columns=column_names)

