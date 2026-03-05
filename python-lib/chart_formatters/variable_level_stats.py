import logging
import pandas as pd
from glm_handler.dku_relativites_calculator import RelativitiesCalculator
from logging_assist.logging import logger

import logging
import numpy as np
import pandas as pd
import re

class VariableLevelStatsFormatter:

    def __init__(self, model_retriever, data_handler, relativities, relativities_interaction, base_values, train_set=None, test_set=None):
        self.model_retriever = model_retriever
        self.data_handler = data_handler
        self.relativities = relativities
        self.relativities_interaction = relativities_interaction
        self.base_values = base_values
        self.relativities_calculator = RelativitiesCalculator(data_handler, model_retriever, train_set, test_set)
        self._group_mapping_cache = {}

    def get_variable_level_stats(self):
        logger.info("Starting to get variable level stats.")
        try:
            coef_table = self._prepare_coef_table()
            features = self.model_retriever.get_features_used_in_modelling()
            
            variable_stats = self._process_intercept(coef_table, self.relativities)

            categorical_features = self._get_categorical_features(features)
            numeric_features = self._get_numeric_features(features)

            if categorical_features:
                variable_stats = self._process_categorical_features(
                    variable_stats, self.relativities, coef_table, categorical_features
                )

            if numeric_features:
                variable_stats = self._process_numeric_features(
                    variable_stats, coef_table, numeric_features
                )
            
            interaction_features = self._get_interaction_features()
            if interaction_features:
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

    def _get_group_mapping(self, feature):
        if feature not in self._group_mapping_cache:
            self._group_mapping_cache[feature] = self.relativities_calculator.get_categorical_group_mapping(feature)
        return self._group_mapping_cache[feature]

    @staticmethod
    def _parse_main_effects(coef_table):
        parsed_rows = []
        pattern = re.compile(r'^[^:]+:(?P<variable>[^:]+):(?P<value>.+)$')
        for _, row in coef_table.iterrows():
            index_value = str(row.get("index", ""))
            if index_value == "intercept":
                continue
            if index_value.startswith("interaction:"):
                continue
            matched = pattern.match(index_value)
            if not matched:
                continue
            parsed_rows.append({
                "variable": matched.group("variable"),
                "value": matched.group("value"),
                "coef": row.get("coef"),
                "p_value": row.get("p_value"),
                "se": row.get("se"),
                "se_pct": row.get("se_pct"),
            })
        if not parsed_rows:
            return pd.DataFrame(columns=["variable", "value", "coef", "p_value", "se", "se_pct"])
        return pd.DataFrame(parsed_rows)

    @staticmethod
    def _parse_spline_term(term_name):
        pattern = r'^spline_f(?P<feature_idx>\d+)_s(?P<segment_idx>\d+)_(?P<min>[-+0-9.eE]+)_(?P<max>[-+0-9.eE]+)_d(?P<degree>\d+)$'
        match = re.match(pattern, str(term_name))
        if not match:
            return None
        try:
            return {
                "feature_idx": int(match.group("feature_idx")),
                "segment_idx": int(match.group("segment_idx")),
                "min_value": float(match.group("min")),
                "max_value": float(match.group("max")),
                "degree": int(match.group("degree")),
            }
        except ValueError:
            return None

    @staticmethod
    def _format_segment_term(parsed_term):
        min_value = parsed_term["min_value"]
        max_value = parsed_term["max_value"]
        return f"f{parsed_term['feature_idx']}:s{parsed_term['segment_idx']}:[{min_value}, {max_value}]:d{parsed_term['degree']}"

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
        main_effects = self._parse_main_effects(coef_table)
        variable_stats_frames = []

        for feature in categorical_features:
            mapping = self._get_group_mapping(feature)
            train_df = self.relativities_calculator.train_set.copy()
            mapped_values = self.relativities_calculator._map_categorical_series(feature, train_df[feature])
            exposure_df = (
                train_df.assign(_mapped_value=mapped_values)
                .dropna(subset=["_mapped_value"])
                .groupby("_mapped_value", as_index=False)["weight"]
                .sum()
                .rename(columns={"_mapped_value": "value", "weight": "exposure"})
            )
            exposure_total = exposure_df["exposure"].sum()
            exposure_df["exposure_pct"] = (exposure_df["exposure"] / exposure_total * 100) if exposure_total else 0
            exposure_df["feature"] = feature

            relativities_cat = relativities[relativities["feature"] == feature].copy()
            if not relativities_cat.empty:
                relativities_cat["value"] = self.relativities_calculator._map_categorical_series(feature, relativities_cat["value"])
                relativities_cat = relativities_cat.dropna(subset=["value"])
                relativities_cat = relativities_cat.groupby(["feature", "value"], as_index=False)["relativity"].mean()

            coef_table_cat = main_effects[main_effects["variable"] == feature].copy()

            feature_stats = relativities_cat.merge(
                coef_table_cat[["value", "coef", "p_value", "se", "se_pct"]],
                how="left",
                on=["value"],
            )
            feature_stats = feature_stats.merge(
                exposure_df[["feature", "value", "exposure", "exposure_pct"]],
                how="left",
                on=["feature", "value"],
            )
            variable_stats_frames.append(feature_stats)

        if not variable_stats_frames:
            return variable_stats
        variable_stats_cat = pd.concat(variable_stats_frames, ignore_index=True)
        return pd.concat([variable_stats, variable_stats_cat], ignore_index=True)

    def _get_numeric_features(self, features):
        logger.debug("Retrieving numeric features.")
        return [feature['variable'] for feature in features if feature['variableType'] == 'numeric' and feature['isInModel']]

    def _process_numeric_features(self, variable_stats, coef_table, numeric_features):
        logger.debug("Processing numeric features.")
        main_effects = self._parse_main_effects(coef_table)
        variable_stats_rows = []
        total_weight = self.relativities_calculator.train_set["weight"].sum()

        for feature in numeric_features:
            feature_effects = main_effects[main_effects["variable"] == feature].copy()
            feature_effects["parsed_spline"] = feature_effects["value"].map(self._parse_spline_term)
            spline_effects = feature_effects[feature_effects["parsed_spline"].notna()].copy()
            nonspline_effects = feature_effects[feature_effects["parsed_spline"].isna()].copy()

            base_row_added = False
            if not nonspline_effects.empty:
                for _, coef_row in nonspline_effects.iterrows():
                    variable_stats_rows.append({
                        "feature": feature,
                        "value": self.base_values.get(feature),
                        "relativity": 1,
                        "coef": coef_row["coef"],
                        "p_value": coef_row["p_value"],
                        "se": coef_row["se"],
                        "se_pct": coef_row["se_pct"],
                        "exposure": total_weight,
                        "exposure_pct": 100,
                    })
                    base_row_added = True
            if not base_row_added:
                variable_stats_rows.append({
                    "feature": feature,
                    "value": self.base_values.get(feature),
                    "relativity": 1,
                    "coef": 0,
                    "p_value": 1,
                    "se": 0,
                    "se_pct": 0,
                    "exposure": total_weight,
                    "exposure_pct": 100,
                })

            if spline_effects.empty:
                continue

            feature_series = pd.to_numeric(self.relativities_calculator.train_set[feature], errors="coerce")
            segment_weight_cache = {}
            for _, coef_row in spline_effects.iterrows():
                parsed_term = coef_row["parsed_spline"]
                segment_key = (
                    parsed_term["feature_idx"],
                    parsed_term["segment_idx"],
                    parsed_term["min_value"],
                    parsed_term["max_value"],
                )
                if segment_key not in segment_weight_cache:
                    in_segment = (feature_series >= parsed_term["min_value"]) & (feature_series <= parsed_term["max_value"])
                    segment_weight_cache[segment_key] = self.relativities_calculator.train_set.loc[in_segment, "weight"].sum()
                segment_weight = segment_weight_cache[segment_key]
                variable_stats_rows.append({
                    "feature": feature,
                    "value": self._format_segment_term(parsed_term),
                    "relativity": 1,
                    "coef": coef_row["coef"],
                    "p_value": coef_row["p_value"],
                    "se": coef_row["se"],
                    "se_pct": coef_row["se_pct"],
                    "exposure": segment_weight,
                    "exposure_pct": (segment_weight / total_weight * 100) if total_weight else 0,
                })

        if not variable_stats_rows:
            return variable_stats

        variable_stats_num = pd.DataFrame(variable_stats_rows, columns=[
            "feature", "value", "relativity", "coef", "p_value", "se", "se_pct", "exposure", "exposure_pct"
        ])
        return pd.concat([variable_stats, variable_stats_num], ignore_index=True)

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
