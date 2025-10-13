from dataiku.customrecipe import get_recipe_config
from dku_config import DkuConfig

from regression_splines.dku_reg_splines import RegressionSplines
from commons import get_input_output
# define inputs
(input_dataset, output_dataset) = get_input_output()
recipe_config = get_recipe_config()

dku_config = DkuConfig()
df = input_dataset.get_dataframe()

# define variables
dku_config.add_param(
    name="column_name",
    value=recipe_config.get("column_name"),
    checks=[{
        "type": "in",
        "op": df.columns
    }],
    required=True
)

dku_config.add_param(
    name="knots",
    value=recipe_config.get("knots"),
    required=True
)

dku_config.add_param(
    name="degree_freedom",
    value=recipe_config.get("degree_freedom"),
    checks=[{
        "type": "between",
        "op": (0, 3)
    }],
    required=True
)

dku_config.add_param(
    name="new_col_prefix",
    value=recipe_config.get("new_col_prefix"),
    required=True
)

# fits splines
regression_splines = RegressionSplines(dku_config.column_name, dku_config.degree_freedom,
                                       dku_config.knots, dku_config.new_col_prefix)
output_dataset_df = regression_splines.run_spline_creation(df)

# Write recipe outputs
output_dataset.write_with_schema(output_dataset_df)