import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

class rebase_mode():
    """This processor applies dummy vectorisation, but drops the dummy column with the mode. Only applies to categorical variables
    """
    def __init__(self, config):
        self.base_level = config["base_level"]
    def fit(self, series):
        self.modalities = np.unique(series)
        self.columns = set(self.modalities)
        self.columns = list(self.columns)
        self.columns.remove(self.base_level)
        self.column_name = series.name
    def transform(self, series):
        to_replace={m: self.base_level for m in np.unique(series) if m not in self.modalities}
        new_series = series.replace(to_replace=to_replace)
        # obtains the dummy encoded dataframe, but drops the dummy column with the mode identified
        df = pd.get_dummies(new_series.values)
        if self.base_level in df:
            df = df.drop(self.base_level, axis = 1)
        for c in self.columns:
            if c not in df.columns:
                df[c] = 0
        df = df[self.columns]
        return df

class save_base():
    """This processor applies no transformation but saves a base level
    """
    def __init__(self, config):
        self.base_level = config["base_level"]
        self.modalities = None  # Initialize modalities here

    def fit(self, series):
        self.modalities = np.unique(series)

    def transform(self, series):
        return pd.DataFrame(series)


class continuous_spline():
    """This processor creates piecewise spline features with standard scaling
    
    Config should contain:
    - 'spline_features': list of list of dicts with 'min_value', 'max_value', 'degree'
    
    Example config:
    {
        "spline_features": [
            [
                {"min_value": 16, "max_value": 25, "degree": 2},
                {"min_value": 25, "max_value": 100, "degree": 1}
            ]
        ]
    }
    """
    def __init__(self, config):
        self.base_level = config["base_level"]
        self.spline_features = config.get("spline_features", [])
        if not self.spline_features:
            # Backward compatibility for historical config shape.
            definitions = config.get("definitions", [])
            if definitions:
                self.spline_features = [definitions]
        self.spline_features = self.spline_features[:3]
        self.scaler = StandardScaler()
        self.feature_names = []
        self.column_name = None
        
    def fit(self, series):
        """Fit the processor on training data
        
        Args:
            series: pandas Series with continuous values
        """
        self.column_name = series.name
        
        # Generate spline features on training data
        spline_features = self._generate_splines(series)
        
        # Store feature names
        self.feature_names = list(spline_features.columns)
        
        # Fit the scaler on these features
        self.scaler.fit(spline_features)
        
        return self
        
    def transform(self, series):
        """Transform data by creating spline features and scaling them
        
        Args:
            series: pandas Series with continuous values
            
        Returns:
            pd.DataFrame with scaled spline features
        """
        # Generate spline features
        spline_features = self._generate_splines(series)
        
        # Apply standard scaling
        scaled_features = self.scaler.transform(spline_features)
        
        # Convert back to DataFrame with proper column names
        result_df = pd.DataFrame(
            scaled_features,
            index=spline_features.index,
            columns=self.feature_names
        )
        
        return result_df
        
    def _generate_splines(self, series):
        """Generate raw spline features before scaling
        
        Args:
            series: pandas Series with continuous values
            
        Returns:
            pd.DataFrame with raw spline features
        """
        x_col = series.values
        generated_features = {}
        
        for feature_idx, segments in enumerate(self.spline_features, start=1):
            for segment_idx, d in enumerate(segments, start=1):
                min_v = d['min_value']
                max_v = d['max_value']
                deg = d['degree']

                # Base ramp: 0 below min, linear inside, constant above max
                ramp = np.clip(x_col, min_v, max_v) - min_v

                # Generate polynomial features up to degree
                for power in range(1, deg + 1):
                    feat_name = (
                        f"{self.column_name}_f{feature_idx}_s{segment_idx}"
                        f"_{min_v}_{max_v}_d{power}"
                    )
                    generated_features[feat_name] = ramp ** power

        if not generated_features:
            generated_features[f"{self.column_name}_spline_default"] = np.zeros_like(x_col, dtype=float)
        
        return pd.DataFrame(generated_features, index=series.index)
