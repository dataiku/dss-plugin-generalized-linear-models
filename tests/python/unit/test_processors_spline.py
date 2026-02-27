import pandas as pd

from processors.processors import continuous_spline


def test_continuous_spline_generates_columns_for_nested_features():
    series = pd.Series([16.0, 18.0, 25.0, 40.0], name="DriverAge")
    processor = continuous_spline(
        {
            "base_level": 50,
            "spline_features": [
                [{"min_value": 16, "max_value": 20, "degree": 2}],
                [{"min_value": 20, "max_value": 100, "degree": 1}],
            ],
        }
    )

    processor.fit(series)
    transformed = processor.transform(series)

    assert transformed.shape[0] == 4
    assert transformed.shape[1] == 3
    assert any(col.startswith("DriverAge_f1_s1_") for col in transformed.columns)
    assert any(col.startswith("DriverAge_f2_s1_") for col in transformed.columns)


def test_continuous_spline_backward_compat_with_flat_definitions():
    series = pd.Series([10.0, 20.0, 30.0], name="x")
    processor = continuous_spline(
        {
            "base_level": 10,
            "definitions": [{"min_value": 10, "max_value": 30, "degree": 1}],
        }
    )

    processor.fit(series)
    transformed = processor.transform(series)

    assert transformed.shape[1] == 1
