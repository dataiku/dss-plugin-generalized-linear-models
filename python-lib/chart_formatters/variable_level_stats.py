import logging
import pandas as pd
from glm_handler.dku_relativites_calculator import RelativitiesCalculator
from logging_assist.logging import logger

import logging
import numpy as np
import pandas as pd

class VariableLevelStatsFormatter:

    def __init__(self, model_retriever, data_handler, relativities, relativities_interaction, base_values, train_set=None, test_set=None):
        self.model_retriever = model_retriever
        self.data_handler = data_handler
        self.relativities = relativities
        self.relativities_interaction = relativities_interaction
        self.base_values = base_values
        self.relativities_calculator = RelativitiesCalculator(data_handler, model_retriever, train_set, test_set)

    def get_variable_level_stats(self):
        logger.info("Starting to get variable level stats.")
        try:
            coef_table = self._prepare_coef_table()
            features = self.model_retriever.get_features_used_in_modelling()
            
            variable_stats = self._process_intercept(coef_table, self.relativities)
            
            if categorical_features := self._get_categorical_features(features):
                variable_stats = self._process_categorical_features(
                    variable_stats, self.relativities, coef_table, categorical_features
                )

            if numeric_features := self._get_numeric_features(features):
                variable_stats = self._process_numeric_features(
                    variable_stats, coef_table, numeric_features
                )
            
            if interaction_features := self._get_interaction_features():
                variable_stats = self._process_interaction_features(
                    variable_stats, self.relativities_interaction, coef_table, interaction_features, categorical_features, numeric_features
                )
            
            variable_stats = self._finalize_stats(variable_stats)
            logger.info("Finished getting variable level stats.")
            return variable_stats

        except Exception as e:
            logger.error(f"An error occurred: {e}")
            raise

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
        variable_stats = coef_table_intercept[['feature', 'value', 'relativity', 'coef', 'p_value','se', 'se_pct', 'exposure', 'exposure_pct']]
        return variable_stats

    def _get_categorical_features(self, features):
        logger.debug("Retrieving categorical features.")
        return [feature['variable'] for feature in features if feature['variableType'] == 'categorical' and feature['isInModel']]

    def _transform_dataset(self, df):
        # Get all columns except 'weight'
        category_columns = df.columns[:-1]

        # Create empty lists to store the transformed data
        features = []
        values = []
        weights = []

        # Process each categorical column
        for column in category_columns:
            # Group by the current column and sum weights
            groups = df.groupby(column)['weight'].sum()

            # Add the results to our lists
            for value, weight in groups.items():
                features.append(column)
                values.append(value)
                weights.append(weight)

        # Create the new DataFrame
        new_df = pd.DataFrame({
            'feature': features,
            'value': values,
            'weight': weights
        })

        # Sort the DataFrame
        new_df = new_df.sort_values(['feature', 'value']).reset_index(drop=True)

        return new_df

    def _process_categorical_features(self, variable_stats, relativities, coef_table, categorical_features):
        logger.debug("Processing categorical features.")
        predicted_cat = self.relativities_calculator.train_set.groupby(categorical_features)['weight'].sum().reset_index()
        predicted_cat = self._transform_dataset(predicted_cat)
        predicted_cat.rename(columns={"weight": "exposure"}, inplace=True)
        relativities_cat = relativities[relativities['feature'].isin(categorical_features)]
        
        coef_table_cat = coef_table[((coef_table['index'] == 'intercept') | (coef_table['index'].str.contains(':'))) & (~coef_table['index'].str.startswith('interaction:')) & (~coef_table['index'].str.endswith(':_'))]

        coef_table_cat[['dummy', 'variable', 'value']] = coef_table_cat['index'].str.split(':', expand=True)
        variable_stats_cat = relativities_cat.merge(
            coef_table_cat[['variable', 'value', 'coef', 'p_value', 'se', 'se_pct']],
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
            on=['feature', 'value']
        )
        variable_stats_cat.drop(['exposure_sum'], axis=1, inplace=True)
        return variable_stats.append(variable_stats_cat)

    def _get_numeric_features(self, features):
        logger.debug("Retrieving numeric features.")
        return [feature['variable'] for feature in features if feature['variableType'] == 'numeric' and feature['isInModel']]

    def _process_numeric_features(self, variable_stats, coef_table, numeric_features):
        logger.debug("Processing numeric features.")
        coef_table_num = coef_table[(coef_table['index'].str.endswith(':_')) & (~coef_table['index'].str.startswith('interaction:'))].copy()
        coef_table_num['feature'] = [var.split(':')[1] for var in coef_table_num['index']]
        coef_table_num['value'] = [self.base_values[feature] for feature in coef_table_num['feature']]
        coef_table_num['exposure'] = self.relativities_calculator.train_set['weight'].sum()
        coef_table_num['exposure_pct'] = 100
        coef_table_num['relativity'] = 1
        
        variable_stats_num = coef_table_num[['feature', 'value', 'relativity', 'coef', 'p_value', 'se', 'se_pct', 'exposure', 'exposure_pct']]
        return variable_stats.append(variable_stats_num)

    def _get_interaction_features(self):
        return self.model_retriever.get_interactions()

    def _process_interaction_features(self, variable_stats, relativities_interaction, coef_table, interaction_features, categorical_features, numeric_features):
        interaction_cat_cat = [interaction for interaction in interaction_features if ((interaction[0] in categorical_features) & (interaction[1] in categorical_features))]
        interaction_num_num = [interaction for interaction in interaction_features if ((interaction[0] in numeric_features) & (interaction[1] in numeric_features))]
        interaction_cat_num = [interaction for interaction in interaction_features if ((interaction not in interaction_cat_cat) & (interaction not in interaction_num_num))]
        
        if interaction_cat_cat:
            variable_stats = self._process_interaction_features_cat_cat(variable_stats, relativities_interaction, coef_table, interaction_cat_cat)
        
        if interaction_num_num:
            variable_stats = self._process_interaction_features_num_num(variable_stats, relativities_interaction, coef_table, interaction_num_num)
        
        if interaction_cat_num:
            variable_stats = self._process_interaction_features_cat_num(variable_stats, relativities_interaction, coef_table, interaction_cat_num, numeric_features)
        
        return variable_stats

    def _process_interaction_features_cat_cat(self, variable_stats, relativities_interaction, coef_table, interaction_features):
        coef_table_interactions = coef_table[(coef_table['index'].str.startswith('interaction:'))]
        coef_table_interactions[['dummy', 'variable', 'value']] = coef_table_interactions['index'].str.split('::', expand=True)
        coef_table_interactions[['dummy', 'variable_1']] = coef_table_interactions['dummy'].str.split(':', expand=True)
        coef_table_interactions[['value_1', 'variable_2']] = coef_table_interactions['variable'].str.split(':', expand=True)
        coef_table_interactions['value_2'] = coef_table_interactions['value']
        coef_table_interactions['interaction'] = [(variable_1, variable_2) for variable_1, variable_2 in zip(coef_table_interactions['variable_1'], coef_table_interactions['variable_2'])]
        coef_table_interactions = coef_table_interactions[coef_table_interactions['interaction'].isin(interaction_features)]
        
        variable_stats_interaction = relativities_interaction.merge(
            coef_table_interactions[['variable_1', 'variable_2', 'value_1', 'value_2', 'coef', 'p_value', 'se', 'se_pct']],
            how='left',
            left_on=['feature_1', 'feature_2', 'value_1', 'value_2'],
            right_on=['variable_1', 'variable_2', 'value_1', 'value_2']
        )
        variable_stats_interaction = variable_stats_interaction[~variable_stats_interaction['coef'].isna()]
        
        # transform complete interaction into marginal interaction
        variable_stats_1 = variable_stats[['feature', 'value', 'relativity']]
        variable_stats_1.columns = ['feature_1', 'value_1', 'relativity_1']
        variable_stats_2 = variable_stats[['feature', 'value', 'relativity']]
        variable_stats_2.columns = ['feature_2', 'value_2', 'relativity_2']
        
        variable_stats_interaction = variable_stats_interaction.merge(variable_stats_1,
            how='left',
            on=['feature_1', 'value_1']
        )
        
        variable_stats_interaction = variable_stats_interaction.merge(variable_stats_2,
            how='left',
            on=['feature_2', 'value_2']
        )
        
        variable_stats_interaction['relativity'] = variable_stats_interaction['relativity'] / variable_stats_interaction['relativity_1'] / variable_stats_interaction['relativity_2']
        
        groupings = pd.DataFrame()
        for i, interaction in enumerate(interaction_features):
            interaction_grouped = self.relativities_calculator.train_set.groupby([interaction[0], interaction[1]])['weight'].sum().reset_index()
            interaction_grouped.columns = ['value_1', 'value_2', 'exposure']
            interaction_grouped['feature_1'] = interaction[0]
            interaction_grouped['feature_2'] = interaction[1]
            interaction_grouped['interaction'] = i
            groupings = groupings.append(interaction_grouped)
        
        groupings['exposure_sum'] = groupings['exposure'].groupby(groupings['interaction']).transform('sum')
        groupings['exposure_pct'] = groupings['exposure'] / groupings['exposure_sum'] * 100
        
        variable_stats_interaction = variable_stats_interaction.merge(
            groupings,
            how='left',
            on=['feature_1', 'feature_2', 'value_1', 'value_2']
        )
        
        variable_stats_interaction['feature'] = variable_stats_interaction['feature_1'] + '::' + variable_stats_interaction['feature_2']
        variable_stats_interaction['value'] = [str(v1) + '::' + str(v2) for v1, v2 in zip(variable_stats_interaction['value_1'], variable_stats_interaction['value_2'])]
        
        variable_stats_interaction.drop(['feature_1', 'feature_2', 'variable_1', 'variable_2', 'value_1', 'value_2', 'interaction', 'exposure_sum', 'relativity_1', 'relativity_2'], axis=1, inplace=True)
        
        variable_stats_interaction['relativity'] = [1 if np.isnan(coef) else rel for coef, rel in zip(variable_stats_interaction['coef'], variable_stats_interaction['relativity'])]
        
        return variable_stats.append(variable_stats_interaction)
    
    def _process_interaction_features_cat_num(self, variable_stats, relativities_interaction, coef_table, interactions_cat_num, numeric_features):
        coef_table_interactions = coef_table[(coef_table['index'].str.startswith('interaction:'))]
        coef_table_interactions[['dummy', 'variable', 'value']] = coef_table_interactions['index'].str.split('::', expand=True)
        coef_table_interactions[['dummy', 'variable_1']] = coef_table_interactions['dummy'].str.split(':', expand=True)
        coef_table_interactions[['value_1', 'variable_2']] = coef_table_interactions['variable'].str.split(':', expand=True)
        coef_table_interactions['value_2'] = coef_table_interactions['value']
        coef_table_interactions['value_1'] = [self.base_values[feature] if (feature in numeric_features) else value for feature, value in zip(coef_table_interactions['variable_1'], coef_table_interactions['value_1'])]
        coef_table_interactions['value_2'] = [self.base_values[feature] if (feature in numeric_features) else value for feature, value in zip(coef_table_interactions['variable_2'], coef_table_interactions['value_2'])]
        coef_table_interactions['interaction'] = [(variable_1, variable_2) for variable_1, variable_2 in zip(coef_table_interactions['variable_1'], coef_table_interactions['variable_2'])]
        
        coef_table_interactions = coef_table_interactions[coef_table_interactions['interaction'].isin(interactions_cat_num)]
        
        variable_stats_interaction = relativities_interaction.merge(
            coef_table_interactions[['variable_1', 'variable_2', 'value_1', 'value_2', 'coef', 'p_value', 'se', 'se_pct']],
            how='left',
            left_on=['feature_1', 'feature_2', 'value_1', 'value_2'],
            right_on=['variable_1', 'variable_2', 'value_1', 'value_2']
        )
        variable_stats_interaction = variable_stats_interaction[~variable_stats_interaction['coef'].isna()]
        
        # transform complete interaction into marginal interaction
        variable_stats_1 = variable_stats[['feature', 'value', 'relativity']]
        variable_stats_1.columns = ['feature_1', 'value_1', 'relativity_1']
        variable_stats_2 = variable_stats[['feature', 'value', 'relativity']]
        variable_stats_2.columns = ['feature_2', 'value_2', 'relativity_2']
        
        variable_stats_interaction = variable_stats_interaction.merge(variable_stats_1,
            how='left',
            on=['feature_1', 'value_1']
        )
        
        variable_stats_interaction = variable_stats_interaction.merge(variable_stats_2,
            how='left',
            on=['feature_2', 'value_2']
        )
        
        variable_stats_interaction['relativity'] = variable_stats_interaction['relativity'] / variable_stats_interaction['relativity_1'] / variable_stats_interaction['relativity_2']
        
        groupings = pd.DataFrame()
        for i, interaction in enumerate(interactions_cat_num):
            interaction_num = 0 if (interaction[0] in numeric_features) else 1
            interaction_cat = np.abs(interaction_num - 1)
            interaction_grouped = self.relativities_calculator.train_set.groupby([interaction[interaction_cat]])['weight'].sum().reset_index()
            interaction_grouped.columns = ['value_' + str(interaction_cat+1), 'exposure']
            interaction_grouped['value_' + str(interaction_num+1)] = self.base_values[interaction[interaction_num]]
            interaction_grouped['feature_' + str(interaction_cat+1)] = interaction[interaction_cat]
            interaction_grouped['feature_' + str(interaction_num+1)] = interaction[interaction_num]
            interaction_grouped['interaction'] = i
            groupings = groupings.append(interaction_grouped)
        
        groupings['exposure_sum'] = groupings['exposure'].groupby(groupings['interaction']).transform('sum')
        groupings['exposure_pct'] = groupings['exposure'] / groupings['exposure_sum'] * 100
        
        variable_stats_interaction = variable_stats_interaction.merge(
            groupings,
            how='left',
            on=['feature_1', 'feature_2', 'value_1', 'value_2']
        )
        
        variable_stats_interaction['feature'] = variable_stats_interaction['feature_1'] + '::' + variable_stats_interaction['feature_2']
        variable_stats_interaction['value'] = [str(v1) + '::' + str(v2) for v1, v2 in zip(variable_stats_interaction['value_1'], variable_stats_interaction['value_2'])]
        
        variable_stats_interaction.drop(['feature_1', 'feature_2', 'variable_1', 'variable_2', 'value_1', 'value_2', 'interaction', 'exposure_sum', 'relativity_1', 'relativity_2'], axis=1, inplace=True)
        
        variable_stats_interaction['relativity'] = [1 if np.isnan(coef) else rel for coef, rel in zip(variable_stats_interaction['coef'], variable_stats_interaction['relativity'])]
        
        return variable_stats.append(variable_stats_interaction)

    def _process_interaction_features_num_num(self, variable_stats, relativities_interaction, coef_table, interactions_num_num):
        coef_table_interactions = coef_table[(coef_table['index'].str.startswith('interaction:'))]
        coef_table_interactions[['dummy', 'variable', 'value']] = coef_table_interactions['index'].str.split('::', expand=True)
        coef_table_interactions[['dummy', 'variable_1']] = coef_table_interactions['dummy'].str.split(':', expand=True)
        coef_table_interactions[['value_1', 'variable_2']] = coef_table_interactions['variable'].str.split(':', expand=True)
        coef_table_interactions['value_2'] = coef_table_interactions['value']
        coef_table_interactions['value_1'] = [self.base_values[feature] for feature in coef_table_interactions['variable_1']]
        coef_table_interactions['value_2'] = [self.base_values[feature] for feature in coef_table_interactions['variable_2']]
        coef_table_interactions['interaction'] = [(variable_1, variable_2) for variable_1, variable_2 in zip(coef_table_interactions['variable_1'], coef_table_interactions['variable_2'])]
        coef_table_interactions = coef_table_interactions[coef_table_interactions['interaction'].isin(interactions_num_num)]
        
        variable_stats_interaction = relativities_interaction.merge(
            coef_table_interactions[['variable_1', 'variable_2', 'value_1', 'value_2', 'coef', 'p_value', 'se', 'se_pct']],
            how='left',
            left_on=['feature_1', 'feature_2', 'value_1', 'value_2'],
            right_on=['variable_1', 'variable_2', 'value_1', 'value_2']
        )
        variable_stats_interaction = variable_stats_interaction[~variable_stats_interaction['coef'].isna()]
        
        variable_stats_interaction['exposure'] = self.relativities_calculator.train_set['weight'].sum()
        variable_stats_interaction['exposure_pct'] = 100
        
        variable_stats_interaction['feature'] = variable_stats_interaction['feature_1'] + '::' + variable_stats_interaction['feature_2']
        variable_stats_interaction['value'] = [str(v1) + '::' + str(v2) for v1, v2 in zip(variable_stats_interaction['value_1'], variable_stats_interaction['value_2'])]
        
        variable_stats_interaction.drop(['feature_1', 'feature_2', 'variable_1', 'variable_2', 'value_1', 'value_2'], axis=1, inplace=True)
        
        variable_stats_interaction['relativity'] = [1 if np.isnan(coef) else rel for coef, rel in zip(variable_stats_interaction['coef'], variable_stats_interaction['relativity'])]
        
        return variable_stats.append(variable_stats_interaction)

    def _finalize_stats(self, variable_stats):
        logger.debug("Finalizing stats.")
        variable_stats.columns = ['variable', 'value', 'relativity', 'coefficient', 'p_value', 'standard_error', 'standard_error_pct', 'weight', 'weight_pct']
        variable_stats.fillna(0, inplace=True)
        variable_stats.replace([np.inf, -np.inf], 0, inplace=True)
        return variable_stats

