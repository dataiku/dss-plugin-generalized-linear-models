import dataiku

from dataiku.doctor.posttraining.model_information_handler import PredictionModelInformationHandler

import pandas as pd
import numpy as np
from dataiku import pandasutils as pdu
from glm_handler.dku_utils import extract_active_fullModelId

from logging_assist.logging import logger


class GlmDataHandler():
    def __init__(self):
        logger.info("Initalising the GLM Data Handler")
    
    def bin_data(self, data, nb_bins):
        """
        Bins the data into specified number of bins based on the cumulative sum of exposure.

        Args:
            data (pd.DataFrame): The DataFrame containing cumulative sum of exposures.
            nb_bins (int): The number of bins to divide the data into.

        Returns:
            pd.DataFrame: The input DataFrame with a new column indicating the bin for each row.
        """
        bins = [round(x / nb_bins, 8) for x in range(nb_bins + 1)][:-1] + [float("inf")]
        data['bin'] = pd.cut(data['exposure_cumsum'].round(16), bins=bins, labels=[x + 1 for x in range(nb_bins)])
        data['bin'] = data['bin'].astype(int)
        return data

    def sort_and_cumsum_exposure(self, data):
        """
        Sorts the data by prediction values in ascending order and calculates
        the cumulative sum of exposure, normalized by the total exposure.

        Args:
            data (pd.DataFrame): The DataFrame containing model predictions and exposures.

        Returns:
            pd.DataFrame: The input DataFrame with additional columns for the cumulative sum
                          and binning information based on exposure.
        """
        print(f"Pandas version is {pd.__version__}")
        print(f"data is type {type(data)}")
        tempdata = data.sort_values(by='predicted', ascending=True).copy()
        tempdata['exposure_cumsum'] = tempdata['weight'].cumsum() / tempdata['weight'].sum()
        return tempdata
    
    def aggregate_metrics_by_bin(self, data):
        """
        Aggregates and calculates metrics within each bin, including sum of exposures,
        weighted predictions, and targets, and calculates observed and predicted data metrics.

        Args:
            data (pd.DataFrame): The DataFrame with predictions, targets, and bin information.

        Returns:
            pd.DataFrame: A summarized DataFrame with metrics calculated for each bin.
        """
        grouped = data.groupby(["bin"]).aggregate({
            'weight': 'sum',
            'weighted_target': 'sum',
            'weighted_predicted': 'sum', 
            'predicted': ['min', 'max']
        })
        grouped.columns = grouped.columns.map('_'.join)
        grouped = grouped.reset_index()
        grouped['observedData'] = grouped['weighted_target_sum'] / grouped['weight_sum']
        grouped['predictedData'] = grouped['weighted_predicted_sum'] / grouped['weight_sum']
        grouped['binInterval'] = [('%s' % float('%.3g' % value_min)) + '-' + ('%s' % float('%.3g' % value_max)) for value_min, value_max in zip(grouped['predicted_min'], grouped['predicted_max'])]
        grouped.reset_index(inplace=True)
        grouped.drop(['index', 'weighted_target_sum', 'weighted_predicted_sum', 'predicted_min', 'predicted_max', 'bin'], axis=1, inplace=True)
        return grouped
    
    def calculate_weighted_aggregations(self, test_set, non_excluded_features, used_feature):
        logger.info(f"caclulating weighted aggregation on {used_feature}")
        predicted_base = {feature: test_set.rename(columns={'base_' + feature: 'weighted_base'}).groupby([feature]).agg(
            {'weighted_target': 'sum',
             'weighted_predicted': 'sum',
             'weight': 'sum',
             'weighted_base': 'mean'}).reset_index()
             if feature in used_feature else test_set.groupby([feature]).agg(
            {'weighted_target': 'sum',
             'weighted_predicted': 'sum',
             'weight': 'sum'}).reset_index()
            for feature in non_excluded_features}
        for feature in predicted_base:
            predicted_base[feature]['weighted_target'] /= predicted_base[feature]['weight']
            predicted_base[feature]['weighted_predicted'] /= predicted_base[feature]['weight']
            if feature not in used_feature:
                predicted_base[feature]['weighted_base'] = predicted_base[feature]['weighted_predicted']
                #predicted_base[feature]['weighted_base'] /= predicted_base[feature]['weight']
                #else:
        logger.info(f"Successfully calculated weighted aggregation on {used_feature}")
        return predicted_base
    
    def construct_final_dataframe(self, predicted_base):
        logger.info("Constructing final dataframe")
        predicted_base_df = pd.DataFrame(columns=['feature', 'category', 'target', 'predicted', 'exposure', 'base'])
        for feature, df in predicted_base.items():
            df.columns = ['category', 'target', 'predicted', 'exposure', 'base']
            df['feature'] = feature
            predicted_base_df = predicted_base_df.append(df)
        logger.info("Successfully constructed final dataframe")
        return predicted_base_df
    
    def bin_numeric_columns(self, test_set, nb_bins_numerical, features, non_excluded_features):
        for feature in non_excluded_features:
            if features[feature]['type'] == 'NUMERIC' and len(test_set[feature].unique()) > nb_bins_numerical:
                test_set[feature] = [(x.left + x.right) / 2 if isinstance(x, pd.Interval) else x for x in pd.cut(test_set[feature], bins=nb_bins_numerical)]
        return test_set
    
    def preprocess_dataframe(self, df, predictor):
        """
        Preprocesses a DataFrame using the model's preprocessing steps.

        Args:
            df (pd.DataFrame): The DataFrame to preprocess.

        Returns:
            pd.DataFrame: The preprocessed DataFrame.
        """
        column_names = predictor.get_features()
        preprocessed_values = predictor.preprocess(df)[0]
        return pd.DataFrame(preprocessed_values, columns=column_names)