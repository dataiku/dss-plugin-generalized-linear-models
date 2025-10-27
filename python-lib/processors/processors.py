import numpy as np
import pandas as pd

class rebase_mode():
    """This processor applies dummy vectorisation, but drops the dummy column with the mode. Only applies to categorical variables
    """
    def __init__(self, config):
        self.mode_column = config["base_level"]
    def fit(self, series):
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

class save_base():
    """This processor applies no transformation but saves a base level
    """
    def __init__(self, config):
        self.mode_column = config["base_level"]
        self.modalities = None  # Initialize modalities here

    def fit(self, series):
        self.modalities = np.unique(series)

    def transform(self, series):
        return pd.DataFrame(series)

def rebase_mode_string(base_level):
    return ('import numpy as np\n'
            'import pandas as pd\n'
            'class rebase_mode():\n'
            '    """This processor applies dummy vectorisation, but drops the dummy column with the mode. Only applies to categorical variables\n'
            '    """\n'
            '    def __init__(self):\n'
            '        self.mode_column = None\n'
            '    def fit(self, series):\n'
            '        # identify the mode of the column, returns as a text value\n'
            '        self.modalities = np.unique(series)\n'
            '        self.mode_column = "' + base_level + '"\n'
            '        self.columns = set(self.modalities)\n'
            '        self.columns = list(self.columns)\n'
            '        self.columns.remove(self.mode_column)\n'
            '        self.column_name = series.name\n'
            '    def transform(self, series):\n'
            '        to_replace={m: self.mode_column for m in np.unique(series) if m not in self.modalities}\n'
            '        new_series = series.replace(to_replace=to_replace)\n'
            '        # obtains the dummy encoded dataframe, but drops the dummy column with the mode identified\n'
            '        df = pd.get_dummies(new_series.values)\n'
            '        if self.mode_column in df:\n'
            '            df = df.drop(self.mode_column, axis = 1)\n'
            '        for c in self.columns:\n'
            '            if c not in df.columns:\n'
            '                df[c] = 0\n'
            '        df = df[self.columns]\n'
            '        return df\n'
            'processor = rebase_mode()')

def save_base_string(base_level):
    return ('import pandas as pd\n'
            'import numpy as np\n'
            'class save_base():\n'
            '    """This processor applies no transformation but saves a base level\n'
            '    """\n'
            '    def __init__(self):\n'
            '        self.mode_column = None\n'
            '    def fit(self, series):\n'
            '        # define the base level\n'
            '        self.mode_column = '+ str(base_level) + '\n'
            '        self.modalities = np.unique(series)\n'
            '    def transform(self, series):\n'
            '        return pd.DataFrame(series)\n'
            '    \n'
            'processor = save_base()')