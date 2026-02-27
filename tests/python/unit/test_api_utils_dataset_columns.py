import pandas as pd

from backend.api_utils import calculate_base_levels


def test_calculate_base_levels_includes_numeric_bounds():
    df = pd.DataFrame(
        {
            "num_col": [1.0, 2.5, 3.0],
            "cat_col": ["a", "b", "a"],
            "exposure": [1.0, 2.0, 3.0],
        }
    )

    columns = calculate_base_levels(df, exposure_column="exposure")
    by_name = {col["column"]: col for col in columns}

    assert by_name["num_col"]["type"] == "numerical"
    assert by_name["num_col"]["minValue"] == 1.0
    assert by_name["num_col"]["maxValue"] == 3.0

    assert by_name["cat_col"]["type"] == "categorical"
    assert by_name["cat_col"]["minValue"] is None
    assert by_name["cat_col"]["maxValue"] is None


def test_calculate_base_levels_handles_missing_numeric_values():
    df = pd.DataFrame(
        {
            "num_col": [None, 2.0, 4.0],
            "cat_col": ["x", "y", "x"],
        }
    )

    columns = calculate_base_levels(df)
    by_name = {col["column"]: col for col in columns}

    assert by_name["num_col"]["minValue"] == 2.0
    assert by_name["num_col"]["maxValue"] == 4.0
