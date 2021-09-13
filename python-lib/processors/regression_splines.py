import numpy as np
import pandas as pd
from patsy import dmatrix, build_design_matrices


class RegressionSplines:
    """This processor adds a new `clipped_column` column which
    clips the `original_column` at its 10th highest value"""

    def __init__(self, degree_freedom, knots, new_col_prefix, keep_original):
        self.degree_freedom = degree_freedom
        self.knots = knots
        self.new_col_prefix = new_col_prefix
        self.formula_string = f"bs(x, knots={self.knots}, degree={self.degree_freedom}, include_intercept=False)"
        self.original_col = None
        self.keep_original = keep_original
        self.train_data = None

    def fit(self, series):
        self.original_col = series.name
        self.train_data = [min(series), max(series)]

    def rename_columns(self, df):
        num_cols = len(df.columns)
        new_cols = [i + '_Spline_' + str(j) for i, j in zip([self.new_col_prefix] * num_cols, range(num_cols))]
        df.columns = new_cols
        return df

    def generate_splines(self, series):
        design_info = dmatrix(self.formula_string, {"x": self.train_data}).design_info
        transformed_x = build_design_matrices([design_info], {'x': series}, return_type='dataframe')[0]
        transformed_x.drop('Intercept', axis=1, inplace=True)
        return transformed_x

    def concatenate(self, original_df, feature_splines):
        if not self.keep_original:
            original_df = None
        return pd.concat([original_df, feature_splines], axis=1)

    def transform(self, series):
        feature_splines = self.generate_splines(series)
        feature_splines = self.rename_columns(feature_splines)

        new_df = self.concatenate(series, feature_splines)

        return new_df

