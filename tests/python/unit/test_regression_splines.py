import pandas as pd
import pytest

from regression_splines.dku_reg_splines import RegressionSplines


def _make_df(values=None):
    if values is None:
        values = [0.0, 0.5, 1.0, 1.5]
    return pd.DataFrame({"feature": values})


def test_generate_splines_excludes_intercept_column():
    df = _make_df()
    spline = RegressionSplines(
        column_name="feature",
        degree_freedom=3,
        knots=[0.75, 1.25],
        new_col_prefix="spline",
    )

    transformed = spline.generate_splines(df)

    assert "Intercept" not in transformed.columns
    assert transformed.shape[0] == df.shape[0]
    assert transformed.shape[1] > 0


def test_run_spline_creation_appends_prefixed_columns():
    df = _make_df()
    spline = RegressionSplines(
        column_name="feature",
        degree_freedom=3,
        knots=[0.5, 1.0],
        new_col_prefix="basis",
    )

    result = spline.run_spline_creation(df.copy())

    new_cols = [col for col in result.columns if col.startswith("basis_")]
    assert len(new_cols) == result.shape[1] - df.shape[1]
    assert all(result[col].dtype.kind in {"f", "i"} for col in new_cols)


def test_run_spline_creation_requires_numeric_column():
    df = pd.DataFrame({"feature": ["a", "b", "c"]})
    spline = RegressionSplines(
        column_name="feature",
        degree_freedom=3,
        knots=[0.5],
        new_col_prefix="spline",
    )

    with pytest.raises(TypeError):
        spline.run_spline_creation(df)


def test_invalid_constructor_arguments_raise():
    with pytest.raises(TypeError):
        RegressionSplines("feature", degree_freedom=2.5, knots=[0.5], new_col_prefix="bad")

    with pytest.raises(TypeError):
        RegressionSplines("feature", degree_freedom=3, knots="notalist", new_col_prefix="bad")

    with pytest.raises(TypeError):
        RegressionSplines(
            "feature",
            degree_freedom=3,
            knots=[0.5, "bad"],
            new_col_prefix="bad",
        )
