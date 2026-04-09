import pandas as pd

from processors.processors import continuous_spline, rebase_mode


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
    assert any(col.startswith("spline_f1_s1_") for col in transformed.columns)
    assert any(col.startswith("spline_f2_s1_") for col in transformed.columns)


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


def test_rebase_mode_groups_modalities_and_drops_grouped_base():
    series = pd.Series(["A", "B", "C", "D", "A"], name="Area")
    processor = rebase_mode(
        {
            "base_level": "A",
            "categorical_groups": [["A", "B"], ["C", "D"]],
        }
    )

    processor.fit(series)
    transformed = processor.transform(series)

    assert "A|B" not in transformed.columns
    assert "C|D" in transformed.columns
    assert transformed.shape[0] == len(series)


def test_rebase_mode_drops_fallback_level_when_base_absent():
    fit_series = pd.Series(["B", "C", "D", "C"], name="Area")
    transform_series = pd.Series(["B", "C", "D", "E"], name="Area")
    processor = rebase_mode(
        {
            "base_level": "A",  # absent during fit
            "categorical_groups": [["C", "D"]],
        }
    )

    processor.fit(fit_series)
    transformed = processor.transform(transform_series)

    # One level is still dropped even when configured base is absent, avoiding full dummy rank.
    unique_levels_after_mapping = set(["B", "C|D"])
    assert transformed.shape[1] == len(unique_levels_after_mapping) - 1
