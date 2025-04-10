import numpy as np
import pandas as pd

class rebase_mode():
    """This processor applies dummy vectorisation, but drops the dummy column with the mode. Only applies to categorical variables
    """
    def __init__(self, config):
        self.mode_column = config["base_level"]
    def fit(self, series):
        # identify the mode of the column, returns as a text value
        self.modalities = np.unique(series)
        self.columns = set(self.modalities)
        self.columns = list(self.columns)
        self.columns.remove(self.mode_column)
        self.column_name = series.name
    def transform(self, series):
        to_replace={m: self.mode_column for m in np.unique(series) if m not in self.modalities}
        new_series = series.replace(to_replace=to_replace)
        # obtains the dummy encoded dataframe, but drops the dummy column with the mode identified
        df = pd.get_dummies(new_series.values)
        if self.mode_column in df:
            df = df.drop(self.mode_column, axis = 1)
        for c in self.columns:
            if c not in df.columns:
                df[c] = 0
        df = df[self.columns]
        return df