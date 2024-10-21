import logging
import pandas as pd
from logging_assist.logging import logger

import logging
import numpy as np
import pandas as pd

class VariableLevelStatsFormatter:

    def __init__(self, model_retriever, data_handler, relativities_calculator):
        self.model_retriever = model_retriever
        self.data_handler = data_handler
        self.relativities_calculator = relativities_calculator

    def get_variable_level_stats(self):
        logger.info("Starting to get variable level stats.")
        try:
            predicted_base = self._get_predicted_base()
            relativities = self._get_relativities()
            coef_table = self._prepare_coef_table()
            features = self.model_retriever.get_features_used_in_modelling()
            
            variable_stats = self._process_intercept(coef_table, relativities)

            if categorical_features := self._get_categorical_features(features):
                variable_stats = self._process_categorical_features(
                    variable_stats, predicted_base, relativities, coef_table, categorical_features
                )

            if numeric_features := self._get_numeric_features(features):
                variable_stats = self._process_numeric_features(
                    variable_stats, coef_table, numeric_features
                )

            variable_stats = self._finalize_stats(variable_stats)
            logger.info("Finished getting variable level stats.")
            return variable_stats

        except Exception as e:
            logger.error(f"An error occurred: {e}")
            raise

    def _get_predicted_base(self):
        logger.debug("Retrieving predicted base DataFrame.")
        predicted_base = self.relativities_calculator.predicted_base_df
        return predicted_base[predicted_base['dataset'] == 'train'][['feature', 'category', 'exposure']]

    def _get_relativities(self):
        logger.debug("Retrieving relativities DataFrame.")
        return self.relativities_calculator.get_relativities_df()

    def _prepare_coef_table(self):
        logger.debug("Preparing coefficient table.")
        coef_table = self.model_retriever.predictor._clf.coef_table.reset_index()
        coef_table['se_pct'] = coef_table['se'] / abs(coef_table['coef']) * 100
        return coef_table

    def _process_intercept(self, coef_table, relativities):
        logger.debug("Processing intercept.")
        coef_table_intercept = coef_table[coef_table['index'] == 'intercept'].copy()
        coef_table_intercept['feature'] = 'base'
        coef_table_intercept['value'] = 'base'
        coef_table_intercept['exposure'] = 0
        coef_table_intercept['exposure_pct'] = 0
        coef_table_intercept['relativity'] = relativities[relativities['feature'] == 'base']['relativity'].iloc[0]
        variable_stats = coef_table_intercept[['feature', 'value', 'relativity', 'coef', 'se', 'se_pct', 'exposure', 'exposure_pct']]
        return variable_stats

    def _get_categorical_features(self, features):
        logger.debug("Retrieving categorical features.")
        return [feature['variable'] for feature in features if feature['variableType'] == 'categorical' and feature['isInModel']]

    def _process_categorical_features(self, variable_stats, predicted_base, relativities, coef_table, categorical_features):
        logger.debug("Processing categorical features.")
        predicted_cat = predicted_base[predicted_base['feature'].isin(categorical_features)]
        relativities_cat = relativities[relativities['feature'].isin(categorical_features)]
        coef_table_cat = coef_table[(coef_table['index'] == 'intercept') | (coef_table['index'].str.contains(':'))]

        coef_table_cat[['dummy', 'variable', 'value']] = coef_table_cat['index'].str.split(':', expand=True)
        variable_stats_cat = relativities_cat.merge(
            coef_table_cat[['variable', 'value', 'coef', 'se', 'se_pct']],
            how='left',
            left_on=['feature', 'value'],
            right_on=['variable', 'value']
        )

        variable_stats_cat.drop('variable', axis=1, inplace=True)
        predicted_cat['exposure_sum'] = predicted_cat['exposure'].groupby(predicted_cat['feature']).transform('sum')
        predicted_cat['exposure_pct'] = predicted_cat['exposure'] / predicted_cat['exposure_sum'] * 100

        variable_stats_cat = variable_stats_cat.merge(
            predicted_cat,
            how='left',
            left_on=['feature', 'value'],
            right_on=['feature', 'category']
        )
        variable_stats_cat.drop(['category', 'exposure_sum'], axis=1, inplace=True)
        return variable_stats.append(variable_stats_cat)

    def _get_numeric_features(self, features):
        logger.debug("Retrieving numeric features.")
        return [feature['variable'] for feature in features if feature['variableType'] == 'numeric' and feature['isInModel']]

    def _process_numeric_features(self, variable_stats, coef_table, numeric_features):
        logger.debug("Processing numeric features.")
        coef_table_num = coef_table[(coef_table['index'].str.endswith(':_')) & (~coef_table['index'].str.startswith('interaction:'))].copy()
        coef_table_num['feature'] = [var.split(':')[1] for var in coef_table_num['index']]
        coef_table_num['value'] = [self.relativities_calculator.base_values[feature] for feature in coef_table_num['feature']]
        coef_table_num['exposure'] = self.relativities_calculator.train_set['weight'].sum()
        coef_table_num['exposure_pct'] = 100
        coef_table_num['relativity'] = 1
        
        variable_stats_num = coef_table_num[['feature', 'value', 'relativity', 'coef', 'se', 'se_pct', 'exposure', 'exposure_pct']]
        return variable_stats.append(variable_stats_num)

    def _finalize_stats(self, variable_stats):
        logger.debug("Finalizing stats.")
        variable_stats.columns = ['variable', 'value', 'relativity', 'coefficient', 'standard_error', 'standard_error_pct', 'weight', 'weight_pct']
        variable_stats.fillna(0, inplace=True)
        variable_stats.replace([np.inf, -np.inf], 0, inplace=True)
        return variable_stats

