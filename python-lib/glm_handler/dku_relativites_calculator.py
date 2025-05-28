import dataiku
from dataiku.doctor.posttraining.model_information_handler import PredictionModelInformationHandler
import pandas as pd
import numpy as np
from dataiku import pandasutils as pdu
from glm_handler.dku_utils import extract_active_fullModelId
from logging_assist.logging import logger
from time import time
import re

class RelativitiesCalculator:
    """
    A class to handle interactions with a Dataiku model.

    Attributes:
        model_id (str): The ID of the model.
        model (dataiku.Model): The Dataiku model object.
        full_model_id (str): The full model ID of the active model version.
        model_info_handler (PredictionModelInformationHandler): Handler for model information.
    """

    def __init__(self,data_handler, model_retriever, prepared_train_set=None, prepared_test_set=None, base_values=None, modalities=None, variable_types=None):
        """
        Initializes the ModelHandler with a specific model ID.

        Args:
            model_id (str): The ID of the model to handle.
        """
        self.data_handler = data_handler
        self.model_retriever = model_retriever
        try:
            if prepared_train_set is not None:
                self.train_set = prepared_train_set
            else:
                self.train_set = self.prepare_dataset('train')
            if prepared_test_set is not None:
                self.test_set = prepared_test_set
            else:
                self.test_set = self.prepare_dataset('test')
            if base_values is None:
                self.base_values = {}
                self.modalities = {}
                self.variable_types = {}
                self.compute_base_values()
            else:
                self.base_values = base_values
                self.modalities = modalities
                self.variable_types = variable_types
            logger.info("Relativities ModelHandler initialized.")
            logger.info(f"length of train set is {len(self.train_set)}")
        except Exception as e:
            logger.error(f"Error initializing RelativitiesCalculator: {e}")
            self.train_set = None
            self.test_set = None
        
    def compute_base_values(self):
        logger.info("Computing base values on initiation.")
        params = self.model_retriever.predictor.params
        preprocessing_features = params.preprocessing_params['per_feature']

        for feature, config in preprocessing_features.items():
            self.base_values[feature] = self.extract_base_level(config['customHandlingCode'])
            self.modalities[feature] = self.train_set[feature].unique()
            self.variable_types[feature] = config['type']

        logger.info("Base values computed and modalities extracted.")

    def get_base_values(self):
        logger.info(f"Getting base values")
        return self.base_values

    def extract_base_level(self, custom_code):
        """
        Extracts Base Level from preprocessing custom code
        """
        base_level = None
        pattern = r'self\.mode_column\s*=\s*["\']([^"\']+)["\']'
        # Search for the pattern in the code string
        match = re.search(pattern, custom_code)
        if match:
            base_level = match.group(1)
        else:
            pattern = r'self\.mode_column\s*=\s*(\d+)'
            match = re.search(pattern, custom_code)
            if match:
                base_level = int(match.group(1))
        logger.debug(f"returning base_level {base_level}")
        return base_level

    def initialize_baseline(self):
        logger.info("Starting initialize_baseline method")
        train_row = self.train_set.head(1).copy()
        used_features = self.model_retriever.get_used_features()
        logger.info(f"Used features: {used_features}")
        
        for feature in used_features:
            base_value = self.base_values[feature]
            train_row[feature] = base_value

        if self.model_retriever.exposure_columns is not None:
            train_row[self.model_retriever.exposure_columns] = 1
            logger.debug(f"Exposure column(s) set to 1")
        else:
            logger.info("No exposure columns to set")

        logger.info("Successfully completed initialize_baseline method")
        return train_row

    def calculate_baseline_prediction(self, sample_train_row):
        logger.info("Calculating baseline prediction")
        return self.model_retriever.predictor.predict(sample_train_row).iloc[0][0]

    def construct_relativities_df(self):
        logger.info("constructing relativites DF")
        rel_df = pd.DataFrame(columns=['feature', 'value', 'relativity'])
        for feature, values in self.relativities.items():
            for value, relativity in values.items():
                rel_df = rel_df.append({'feature': feature, 'value': value, 'relativity': relativity}, ignore_index=True)
        return rel_df
    
    def construct_relativities_interaction_df(self):
        logger.info("constructing relativites DF")
        rel_df = pd.DataFrame(columns=['feature_1', 'feature_2', 'value_1', 'value_2', 'relativity'])
        for feature_1, features in self.relativities_interaction.items():
            for feature_2, values in features.items():
                for value_1, relativities in values.items():
                    for value_2, relativity in relativities.items():
                        rel_df = rel_df.append({'feature_1': feature_1, 
                        'feature_2': feature_2,
                        'value_1': value_1,
                        'value_2': value_2, 
                        'relativity': relativity}, ignore_index=True)
        return rel_df
    
    def get_relativities_df(self):
        """
        Computes and returns the relativities DataFrame for the model.
        Returns:
            pd.DataFrame: The relativities DataFrame.
        """
        logger.info("Computing relativities DataFrame.")
        sample_train_row = self.initialize_baseline()
        baseline_prediction = self.calculate_baseline_prediction(sample_train_row)

        self.relativities = {'base': {'base': baseline_prediction}}
        used_features = self.model_retriever.get_used_features()

        for feature in used_features:
            feature_type = self.model_retriever.features[feature]['type']
            base_value = self.base_values[feature]
            self.relativities[feature] = {base_value: 1.0}
            train_row_copy = sample_train_row.copy()

            values_to_process = self.modalities[feature]

            for value in values_to_process:
                train_row_copy[feature] = value
                prediction = self.model_retriever.predictor.predict(train_row_copy).iloc[0][0]
                relativity = prediction / baseline_prediction
                self.relativities[feature][value] = relativity

        relativities_df = self.construct_relativities_df()
        logger.info("Relativities DataFrame computed")
        return relativities_df

    def get_relativities_interactions_df(self):
        """
        Computes and returns the relativities DataFrame for the model.
        Returns:
            pd.DataFrame: The relativities DataFrame.
        """
        logger.info("Computing relativities DataFrame.")
        sample_train_row = self.initialize_baseline()
        baseline_prediction = self.calculate_baseline_prediction(sample_train_row)

        self.relativities_interaction = {}
        interactions = self.model_retriever.get_interactions()

        for interaction in interactions:
            interaction_first = interaction[0]
            interaction_second = interaction[1]
            
            base_value_first = self.base_values[interaction_first]
            base_value_second = self.base_values[interaction_second]
            try:
                self.relativities_interaction[interaction_first][interaction_second] = {base_value_first: {base_value_second: 1.0}}
            except KeyError:
                self.relativities_interaction[interaction_first] = {interaction_second:  {base_value_first: {base_value_second: 1.0}}}
            train_row_copy = sample_train_row.copy()
            
            values_to_process_first = self.modalities[interaction_first]
            values_to_process_second = self.modalities[interaction_second]
            
            for value_first in values_to_process_first:
                for value_second in values_to_process_second:
                    train_row_copy[interaction_first] = value_first
                    train_row_copy[interaction_second] = value_second
                    prediction = self.model_retriever.predictor.predict(train_row_copy).iloc[0][0]
                    relativity = prediction / baseline_prediction
                    try:
                        self.relativities_interaction[interaction_first][interaction_second][value_first][value_second] = relativity
                    except KeyError:
                        self.relativities_interaction[interaction_first][interaction_second][value_first] = {value_second: relativity}

        relativities_interaction_df = self.construct_relativities_interaction_df()
        logger.info("Relativities DataFrame computed")
        return relativities_interaction_df

    def apply_weights_to_data(self, test_set):
        used_features = self.model_retriever.get_used_features()
        print(f"Using feature list of {used_features}")
        if self.model_retriever.exposure_columns is None:
            test_set['weight'] = 1
        else:
            test_set['weight'] = test_set[self.model_retriever.exposure]
        test_set['weighted_target'] = test_set[self.model_retriever.target_columns] * test_set['weight']
        test_set['weighted_predicted'] = test_set['predicted'] * test_set['weight']

    def prepare_dataset(self, dataset_type='train'):
        """
        Prepares and returns either the training or test dataset.

        Args:
            dataset_type (str): Either 'train' or 'test'. Defaults to 'train'.

        Returns:
            pd.DataFrame: The prepared dataset.
        """
        logger.info(f"Preparing {dataset_type} dataset.")

        if dataset_type == 'train':
            dataset = self.model_retriever.model_info_handler.get_train_df()[0].copy()
        elif dataset_type == 'test':
            dataset = self.model_retriever.model_info_handler.get_test_df()[0].copy()
        else:
            raise ValueError("dataset_type must be either 'train' or 'test'")

        predicted = self.model_retriever.predictor.predict(dataset)
        dataset['predicted'] = predicted
        dataset['weight'] = 1 if self.model_retriever.exposure_columns is None else dataset[self.model_retriever.exposure_columns]

        dataset['weighted_target'] = dataset[self.model_retriever.target_column]
        dataset['weighted_predicted'] = dataset['predicted']
                  
        logger.info(f"{dataset_type.capitalize()} dataset prepared: {dataset.shape}")
        return dataset
    
    def compute_base_predictions_new(self, test_set, used_features):
        logger.info(f"Starting compute_base_predictions_new for {used_features}")
        base_data = {}
        copy_test_df = test_set.copy()
        copy_test_df[self.model_retriever.exposure_columns] = 1

        for feature in used_features:
            feature_df = copy_test_df.groupby(feature, as_index=False).first()

            for other_feature in used_features:
                if other_feature != feature:
                    feature_df[other_feature] = self.base_values[other_feature]

            predictions = self.model_retriever.predictor.predict(feature_df)
            base_data[feature] = pd.DataFrame({
                f'base_{feature}': predictions['prediction'],
                feature: feature_df[feature]
            })

        logger.info("Finished compute_base_predictions_new")
        return base_data
    
    def compute_base_predictions_variable(self, test_set, used_features, feature):
        logger.info(f"Starting compute_base_predictions for {feature}")
        base_data = {}
        copy_test_df = test_set.copy()
        copy_test_df[self.model_retriever.exposure_columns] = 1

        feature_df = copy_test_df.groupby(feature, as_index=False).first()

        for other_feature in used_features:
            if other_feature != feature:
                feature_df[other_feature] = self.base_values[other_feature]

        predictions = self.model_retriever.predictor.predict(feature_df)
        base_data[feature] = pd.DataFrame({
            f'base_{feature}': predictions['prediction'],
            feature: feature_df[feature]
        })

        logger.info("Finished compute_base_predictions")
        return base_data

    def get_formated_predicted_base(self):
        logger.info("Getting formatted and predicted base")
        self.get_predicted_and_base()
        df = self.predicted_base_df.copy()
        df.columns = ['definingVariable', 
                     'Category', 
                     'observedAverage', 
                     'fittedAverage', 'Value', 'baseLevelPrediction', 'dataset']
        logger.info("Successfully got formatted and predicted base")
        return df
    
    def get_formated_predicted_base_variable(self, variable):
        logger.info("Getting formatted and predicted base")
        self.get_predicted_and_base_variable(variable)
        df = self.predicted_base_df.copy()
        df.columns = ['definingVariable', 
                     'Category', 
                     'observedAverage', 
                     'fittedAverage', 'Value', 'baseLevelPrediction', 'dataset']
        logger.info("Successfully got formatted and predicted base")
        return df

    def merge_predictions(self, test_set, base_data):
        logger.info("Merging Base predictions")
        for feature in base_data.keys():
            test_set = test_set.set_index(feature).join(base_data[feature].set_index(feature), how='left')
        logger.info("Successfully Merged Base predictions")
        return test_set
    
    def process_dataset_variable(self, dataset, dataset_name, variable):
        logger.info(f"Processing dataset {dataset_name}")
        used_features = self.model_retriever.get_used_features()
        base_data = self.compute_base_predictions_variable(dataset, used_features, variable)
        dataset = self.merge_predictions(dataset, base_data)
        predicted_base = self.data_handler.calculate_weighted_aggregations(dataset, [variable], ([variable] if variable in used_features else []))
        predicted_base_df = self.data_handler.construct_final_dataframe(predicted_base)
        predicted_base_df['dataset'] = dataset_name
        logger.info(f"Processed dataset {dataset_name}")
        return predicted_base_df
    
    def get_predicted_and_base(self, nb_bins_numerical=100000):
        logger.info("Getting Predicted and base")
        
        test_predictions = self.process_dataset(self.test_set, 'test')
        train_predictions = self.process_dataset(self.train_set, 'train')
        
        self.predicted_base_df = train_predictions.append(test_predictions)
        categorical_variables = [variable for variable in self.variable_types.keys() if self.variable_types[variable] == 'CATEGORY']
        self.predicted_base_df['category'] = [str(category) if variable in categorical_variables else category for category, variable in zip(self.predicted_base_df['category'], self.predicted_base_df['feature'])]
        logger.info("Successfully got Predicted and base")
        return self.predicted_base_df.copy()
    
    def get_predicted_and_base_variable(self, variable, nb_bins_numerical=100000):
        logger.info(f"Getting Predicted and base for variable {variable}")
        
        test_predictions = self.process_dataset_variable(self.test_set, 'test', variable)
        train_predictions = self.process_dataset_variable(self.train_set, 'train', variable)
        
        self.predicted_base_df = train_predictions.append(test_predictions)
        categorical_variables = [variable for variable in self.variable_types.keys() if self.variable_types[variable] == 'CATEGORY']
        self.predicted_base_df['category'] = [str(category) if variable in categorical_variables else category for category, variable in zip(self.predicted_base_df['category'], self.predicted_base_df['feature'])]
        logger.info("Successfully got Predicted and base")
        return self.predicted_base_df.copy()
    


