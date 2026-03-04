import pandas as pd
import numpy as np
from logging_assist.logging import logger
from time import time
import re
import ast

class RelativitiesCalculator:
    """
    A class to handle interactions with a Dataiku model.

    Attributes:
        model_id (str): The ID of the model.
        model (dataiku.Model): The Dataiku model object.
        full_model_id (str): The full model ID of the active model version.
        model_info_handler (PredictionModelInformationHandler): Handler for model information.
    """

    def __init__(self, data_handler, model_retriever, prepared_train_set=None, prepared_test_set=None, base_values=None, modalities=None, variable_types=None):
        """
        Initializes the ModelHandler with a specific model ID.

        Args:
            model_id (str): The ID of the model to handle.
        """
        self.data_handler = data_handler
        self.model_retriever = model_retriever
        self._categorical_group_mapping_cache = {}
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
    
    def _predict_from_df(self, df):
        preprocessed_data = self.model_retriever.predictor.preprocess(df)
        predictions_array = self.model_retriever.predictor._clf.predict(preprocessed_data[0])
        return predictions_array

    def _get_feature_preprocessing_params(self, feature):
        params = getattr(self.model_retriever.predictor, "params", None)
        if params is None:
            return {}
        preprocessing_params = getattr(params, "preprocessing_params", {}) or {}
        per_feature = preprocessing_params.get("per_feature", {}) if isinstance(preprocessing_params, dict) else {}
        return per_feature.get(feature, {}) if isinstance(per_feature, dict) else {}

    def _get_categorical_groups(self, feature):
        feature_params = self._get_feature_preprocessing_params(feature)
        custom_code = feature_params.get("customHandlingCode", "")
        if "rebase_mode" not in custom_code:
            return []
        try:
            parsed = ast.parse(custom_code)
        except SyntaxError:
            return []
        for node in ast.walk(parsed):
            if not isinstance(node, ast.Assign):
                continue
            value = node.value
            if not isinstance(value, ast.Call):
                continue
            if not isinstance(value.func, ast.Name) or value.func.id != "rebase_mode":
                continue
            if not value.args:
                continue
            try:
                config_dict = ast.literal_eval(value.args[0])
            except (ValueError, SyntaxError):
                continue
            raw_groups = config_dict.get("categorical_groups", []) if isinstance(config_dict, dict) else []
            if not isinstance(raw_groups, list):
                return []
            normalized_groups = []
            seen_modalities = set()
            for raw_group in raw_groups:
                if not isinstance(raw_group, list):
                    continue
                normalized_group = []
                for modality in raw_group:
                    modality_str = str(modality)
                    if modality_str in seen_modalities or modality_str in normalized_group:
                        continue
                    normalized_group.append(modality_str)
                if len(normalized_group) < 2:
                    continue
                normalized_groups.append(normalized_group)
                seen_modalities.update(normalized_group)
            return normalized_groups
        return []

    def get_categorical_group_mapping(self, feature):
        if feature in self._categorical_group_mapping_cache:
            return self._categorical_group_mapping_cache[feature]
        groups = self._get_categorical_groups(feature)
        mapping = {}
        for group in groups:
            label = "|".join(sorted(str(v) for v in group))
            for modality in group:
                mapping[str(modality)] = label
        self._categorical_group_mapping_cache[feature] = mapping
        return mapping

    def _map_categorical_value(self, feature, value):
        if self.variable_types.get(feature) != "CATEGORY":
            return value
        mapping = self.get_categorical_group_mapping(feature)
        return mapping.get(str(value), str(value))

    def _map_categorical_series(self, feature, series):
        if self.variable_types.get(feature) != "CATEGORY":
            return series
        mapping = self.get_categorical_group_mapping(feature)
        if not mapping:
            return series
        mapped_series = series.copy()
        non_null_mask = mapped_series.notna()
        original_values = mapped_series.loc[non_null_mask].astype(str)
        remapped_values = original_values.map(mapping).fillna(original_values)
        mapped_series.loc[non_null_mask] = remapped_values
        return mapped_series

    @staticmethod
    def _is_valid_value(value):
        return value is not None and not pd.isna(value)

    def _resolve_exposure_column(self, dataset):
        exposure_column = self.model_retriever.exposure_columns
        if exposure_column and exposure_column in dataset.columns:
            return exposure_column
        return None

    def _resolve_sample_weight_column(self, dataset):
        sample_weight_column = None
        if hasattr(self.model_retriever, "get_sample_weight_column"):
            sample_weight_column = self.model_retriever.get_sample_weight_column()
        if sample_weight_column and sample_weight_column in dataset.columns:
            return sample_weight_column
        return None

    def _compute_effective_weight(self, dataset):
        exposure_column = self._resolve_exposure_column(dataset)
        sample_weight_column = self._resolve_sample_weight_column(dataset)
        if exposure_column and sample_weight_column:
            return dataset[exposure_column] * dataset[sample_weight_column]
        if exposure_column:
            return dataset[exposure_column]
        if sample_weight_column:
            return dataset[sample_weight_column]
        return pd.Series(1.0, index=dataset.index)

    def _get_modality_mass(self, dataset):
        exposure_column = self._resolve_exposure_column(dataset)
        if exposure_column:
            return dataset[exposure_column]
        return self._compute_effective_weight(dataset)

    def compute_base_values(self):
        logger.info("Computing base values on initiation.")
        params = self.model_retriever.predictor.params
        preprocessing_features = params.preprocessing_params['per_feature']

        for feature, config in preprocessing_features.items():
            raw_base_level = self.extract_base_level(config['customHandlingCode'])
            self.variable_types[feature] = config['type']
            if self.variable_types[feature] == "CATEGORY":
                self.base_values[feature] = self._map_categorical_value(feature, raw_base_level)
            else:
                self.base_values[feature] = raw_base_level
            self.modalities[feature] = self.train_set[feature].unique()

        logger.info("Base values computed and modalities extracted.")

    def get_base_values(self):
        logger.info(f"Getting base values")
        return self.base_values

    def extract_base_level(self, custom_code):
        """
        Extracts Base Level from preprocessing custom code.
        Supports string and numeric (int/float) values.
        """
        base_level = None
        # Match either a quoted string or a signed integer/float
        pattern = r'"base_level":\s*(?:"([^"]+)"|([+-]?\d+(?:\.\d+)?))'
        match = re.search(pattern, custom_code)
        base_level = None
        if match:
            if match.group(1) is not None:
                base_level = match.group(1)
            elif match.group(2) is not None:
                # Convert numeric string to float to support decimals
                num_str = match.group(2)
                try:
                    base_level = float(num_str)
                except ValueError:
                    base_level = None
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
        return self._predict_from_df(sample_train_row)[0]

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
    
    def _build_modeled_relativities_df(self, raw_relativities_df):
        if raw_relativities_df.empty:
            return raw_relativities_df
        modeled_rows = []
        for feature, feature_df in raw_relativities_df.groupby("feature", dropna=False):
            if feature in ("base",):
                modeled_rows.extend(feature_df.to_dict("records"))
                continue
            if self.variable_types.get(feature) != "CATEGORY":
                modeled_rows.extend(feature_df.to_dict("records"))
                continue
            feature_df = feature_df.copy()
            feature_df["value"] = self._map_categorical_series(feature, feature_df["value"])
            feature_df = feature_df.groupby(["feature", "value"], as_index=False)["relativity"].mean()
            modeled_rows.extend(feature_df.to_dict("records"))
        return pd.DataFrame(modeled_rows, columns=["feature", "value", "relativity"])

    def get_relativities_df(self, modeled_categorical=False):
        """
        Computes and returns the relativities DataFrame for the model.
        (Optimized with batch prediction)
        Returns:
            pd.DataFrame: The relativities DataFrame.
        """
        logger.info("Computing relativities DataFrame.")
        sample_train_row = self.initialize_baseline()
        baseline_prediction = self.calculate_baseline_prediction(sample_train_row)

        self.relativities = {'base': {'base': baseline_prediction}}
        used_features = self.model_retriever.get_used_features()

        dfs_to_predict = []
        features_and_values = [] # To map results back

        for feature in used_features:
            feature_type = self.model_retriever.features[feature]['type']
            base_value = self.base_values[feature]
            self.relativities[feature] = {}

            modality_mass = self._get_modality_mass(self.train_set)
            if feature_type == "CATEGORY":
                mapped_feature = self._map_categorical_series(feature, self.train_set[feature])
                mass_per_group = modality_mass.groupby(mapped_feature).sum()
                values_to_process = mass_per_group.index.tolist()
            else:
                exposure_per_modality = modality_mass.groupby(self.train_set[feature]).sum()
                values_to_process = exposure_per_modality.nlargest(99).index.tolist()
            if self._is_valid_value(base_value) and base_value not in values_to_process:
                values_to_process.append(base_value)

            for value in values_to_process:
                if value == base_value:
                    self.relativities[feature][value] = 1.0
                    continue
                
                train_row_copy = sample_train_row.copy()
                train_row_copy[feature] = value
                dfs_to_predict.append(train_row_copy)
                features_and_values.append((feature, value))

        if dfs_to_predict:
            logger.info(f"Predicting batch of {len(dfs_to_predict)} rows for relativities...")
            batch_df = pd.concat(dfs_to_predict, ignore_index=True)
            batch_predictions = self._predict_from_df(batch_df)
            
            for i, (feature, value) in enumerate(features_and_values):
                prediction = batch_predictions[i]
                relativity = prediction / baseline_prediction
                self.relativities[feature][value] = relativity

        raw_relativities_df = self.construct_relativities_df()
        self.relativities_raw = {
            feature: dict(values) for feature, values in self.relativities.items()
        }
        self.relativities_modeled_df = self._build_modeled_relativities_df(raw_relativities_df)
        logger.info("Relativities DataFrame computed")
        if modeled_categorical:
            return self.relativities_modeled_df.copy()
        return raw_relativities_df

    def get_relativities_interactions_df(self):
        """
        Computes and returns the relativities DataFrame for the model.
        (Optimized with batch prediction)
        Returns:
            pd.DataFrame: The relativities DataFrame.
        """
        logger.info("Computing relativities DataFrame.")
        sample_train_row = self.initialize_baseline()
        baseline_prediction = self.calculate_baseline_prediction(sample_train_row)

        self.relativities_interaction = {}
        interactions = self.model_retriever.get_interactions()
        
        dfs_to_predict = []
        features_and_values_list = [] # To map results back

        for interaction in interactions:
            interaction_first = interaction[0]
            interaction_second = interaction[1]
            
            base_value_first = self.base_values[interaction_first]
            base_value_second = self.base_values[interaction_second]
            
            # Initialize the nested dictionary structure
            if interaction_first not in self.relativities_interaction:
                self.relativities_interaction[interaction_first] = {}
            if interaction_second not in self.relativities_interaction[interaction_first]:
                self.relativities_interaction[interaction_first][interaction_second] = {}
            if base_value_first not in self.relativities_interaction[interaction_first][interaction_second]:
                 self.relativities_interaction[interaction_first][interaction_second][base_value_first] = {}
            
            # Set base relativity
            self.relativities_interaction[interaction_first][interaction_second][base_value_first][base_value_second] = 1.0
            
            type_first = self.variable_types.get(interaction_first)
            type_second = self.variable_types.get(interaction_second)

            if type_first == 'CATEGORY':
                values_to_process_first = sorted({
                    self._map_categorical_value(interaction_first, value)
                    for value in self.modalities[interaction_first]
                })
            else:
                values_to_process_first = [base_value_first]

            if type_second == 'CATEGORY':
                values_to_process_second = sorted({
                    self._map_categorical_value(interaction_second, value)
                    for value in self.modalities[interaction_second]
                })
            else:
                values_to_process_second = [base_value_second]
            
            for value_first in values_to_process_first:
                for value_second in values_to_process_second:
                    if value_first == base_value_first and value_second == base_value_second:
                        continue # Skip base case, already set to 1.0

                    train_row_copy = sample_train_row.copy()
                    train_row_copy[interaction_first] = value_first
                    train_row_copy[interaction_second] = value_second
                    dfs_to_predict.append(train_row_copy)
                    features_and_values_list.append((interaction_first, interaction_second, value_first, value_second))

        # Predict on the entire batch at once
        if dfs_to_predict:
            logger.info(f"Predicting batch of {len(dfs_to_predict)} rows for interactions...")
            batch_df = pd.concat(dfs_to_predict, ignore_index=True)
            batch_predictions = self._predict_from_df(batch_df)
            
            # Map results back
            for i, (f1, f2, v1, v2) in enumerate(features_and_values_list):
                prediction = batch_predictions[i]
                relativity = prediction / baseline_prediction
                if v1 not in self.relativities_interaction[f1][f2]:
                    self.relativities_interaction[f1][f2][v1] = {}
                self.relativities_interaction[f1][f2][v1][v2] = relativity

        relativities_interaction_df = self.construct_relativities_interaction_df()
        logger.info("Relativities DataFrame computed")
        return relativities_interaction_df

    def apply_weights_to_data(self, test_set):
        used_features = self.model_retriever.get_used_features()
        print(f"Using feature list of {used_features}")
        test_set['weight'] = self._compute_effective_weight(test_set)
        test_set['weighted_target'] = test_set[self.model_retriever.target_column] * test_set['weight']
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

        predicted = self._predict_from_df(dataset)
        dataset['predicted'] = predicted
        dataset['weight'] = self._compute_effective_weight(dataset)

        dataset['weighted_target'] = dataset[self.model_retriever.target_column] * dataset['weight']
        dataset['weighted_predicted'] = dataset['predicted'] * dataset['weight']
        
        logger.info(f"{dataset_type.capitalize()} dataset prepared: {dataset.shape}")
        return dataset
    
    def compute_base_predictions_variable(self, test_set, used_features, feature, max_modalities=100, grouping_info=None):
        logger.info(f"Starting compute_base_predictions for {feature}")
        start_time = time()
        base_data = {}
        copy_test_df = test_set.copy()
        modality_mass = self._get_modality_mass(copy_test_df)
        feature_type = self.variable_types.get(feature, None)
        exposure_col = self._resolve_exposure_column(copy_test_df)
        if exposure_col is not None:
            copy_test_df[exposure_col] = 1

        bin_map = None
        if feature_type == 'CATEGORY':
            mapping_start = time()
            copy_test_df[feature] = self._map_categorical_series(feature, copy_test_df[feature])
            logger.info(
                "Categorical remap completed for %s in %.3fs (%s rows)",
                feature,
                time() - mapping_start,
                len(copy_test_df)
            )
            exposure_per_modality = modality_mass.groupby(copy_test_df[feature]).sum()
            top_modalities = exposure_per_modality.nlargest(max_modalities - 1).index
            copy_test_df[feature] = copy_test_df[feature].where(copy_test_df[feature].isin(top_modalities), other='Other')
            feature_df = copy_test_df.groupby(feature, as_index=False).first()
        elif feature_type == 'NUMERIC':
            unique_vals = copy_test_df[feature].nunique(dropna=True)
            if unique_vals > max_modalities:
                if grouping_info is None:
                    copy_test_df['feature_bin'] = pd.qcut(copy_test_df[feature], q=max_modalities, duplicates='drop')
                    def weighted_mean(x):
                        weights = modality_mass.loc[x.index].fillna(0)
                        weight_sum = weights.sum()
                        if weight_sum <= 0:
                            logger.warning(
                                "Zero-weight bin detected for %s; falling back to unweighted average.",
                                feature
                            )
                            return x[feature].mean()
                        return np.average(x[feature], weights=weights)
                    bin_means = copy_test_df.groupby('feature_bin').apply(weighted_mean)
                    bin_map = dict(zip(bin_means.index, bin_means.values))
                    # Map the bin containing the base_value to the base_value itself
                    base_value = self.base_values.get(feature, None)
                    if base_value is not None:
                        for bin_label in bin_map:
                            left = bin_label.left if hasattr(bin_label, 'left') else None
                            right = bin_label.right if hasattr(bin_label, 'right') else None
                            if left is not None and right is not None and left < base_value <= right:
                                bin_map[bin_label] = float(base_value)
                                break
                else:
                    bin_map = grouping_info
                    copy_test_df['feature_bin'] = pd.qcut(copy_test_df[feature], q=max_modalities, duplicates='drop')
                copy_test_df[feature] = copy_test_df['feature_bin'].map(bin_map).astype(float)
                feature_df = copy_test_df.groupby('feature_bin', as_index=False).first()
                feature_df[feature] = feature_df['feature_bin'].map(bin_map).astype(float)
                feature_df = feature_df.drop(columns=['feature_bin'])
            else:
                feature_df = copy_test_df.groupby(feature, as_index=False).first()
        else:
            feature_df = copy_test_df.groupby(feature, as_index=False).first()

        for other_feature in used_features:
            if other_feature != feature:
                feature_df[other_feature] = self.base_values[other_feature]

        predictions = self._predict_from_df(feature_df)
        base_data[feature] = pd.DataFrame({
            f'base_{feature}': predictions,
            feature: feature_df[feature]
        })

        logger.info(
            "Finished compute_base_predictions for %s in %.3fs",
            feature,
            time() - start_time
        )
        return base_data, bin_map
    
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
    
    def process_dataset_variable(self, dataset, dataset_name, variable, max_modalities=100):
        logger.info(f"Processing dataset {dataset_name}")
        used_features = self.model_retriever.get_used_features()
        # Compute base_data and get grouping info
        base_data, bin_map = self.compute_base_predictions_variable(dataset, used_features, variable, max_modalities=max_modalities)
        feature_type = self.variable_types.get(variable, None)
        modality_mass = self._get_modality_mass(dataset)
        grouped_dataset = dataset.copy()
        if feature_type == 'CATEGORY':
            mapping_start = time()
            grouped_dataset[variable] = self._map_categorical_series(variable, grouped_dataset[variable])
            logger.info(
                "Categorical remap in process_dataset_variable completed for %s in %.3fs (%s rows)",
                variable,
                time() - mapping_start,
                len(grouped_dataset)
            )
            exposure_per_modality = modality_mass.groupby(grouped_dataset[variable]).sum()
            top_modalities = exposure_per_modality.nlargest(max_modalities - 1).index
            grouped_dataset[variable] = grouped_dataset[variable].where(grouped_dataset[variable].isin(top_modalities), other='Other')
        elif feature_type == 'NUMERIC':
            unique_vals = grouped_dataset[variable].nunique(dropna=True)
            if unique_vals > max_modalities and bin_map is not None:
                grouped_dataset['feature_bin'] = pd.qcut(grouped_dataset[variable], q=max_modalities, duplicates='drop')
                grouped_dataset[variable] = grouped_dataset['feature_bin'].map(bin_map).astype(float)
                grouped_dataset = grouped_dataset.drop(columns=['feature_bin'])
        dataset = self.merge_predictions(grouped_dataset, base_data)
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
