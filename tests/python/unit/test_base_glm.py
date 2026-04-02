import numpy as np
import pytest

from glum import (
    BinomialDistribution,
    GammaDistribution,
    InverseGaussianDistribution,
    NegativeBinomialDistribution,
    NormalDistribution,
    PoissonDistribution,
    TweedieDistribution,
)

import generalized_linear_models.dku_glm as dku_glm
from generalized_linear_models.dku_glm import BinaryClassificationGLM, RegressionGLM


def _base_kwargs():
    return {"family_name": "gaussian"}


@pytest.mark.parametrize(
    "kwargs, message",
    [
        ({"penalty": -0.1}, "penalty should be positive"),
        ({"l1_ratio": 1.5}, "l1_ratio should be between 0 and 1"),
        (
            {"family_name": "negative_binomial", "alpha": 0.001},
            "alpha should be between 0.01 and 2",
        ),
        (
            {
                "family_name": "negative_binomial",
                "negative_binomial_link": "power",
                "power": "foo",
            },
            "power should be defined with a numeric value",
        ),
        (
            {"family_name": "tweedie", "tweedie_link": "power", "power": "foo"},
            "power should be defined with a numeric value",
        ),
        (
            {"family_name": "tweedie", "var_power": "foo"},
            "var_power should be defined with a numeric value",
        ),
    ],
)
def test_base_glm_init_validation(kwargs, message):
    params = _base_kwargs()
    params.update(kwargs)
    with pytest.raises(ValueError, match=message):
        RegressionGLM(**params)


@pytest.mark.parametrize(
    "family, extra_kwargs, expected_family, expected_cls",
    [
        ("binomial", {}, "binomial", BinomialDistribution),
        ("gamma", {}, "gamma", GammaDistribution),
        ("gaussian", {}, "gaussian", NormalDistribution),
        ("inverse_gaussian", {}, "inverse.gaussian", InverseGaussianDistribution),
        (
            "negative_binomial",
            {"alpha": 0.5},
            "negative.binomial (0.5)",
            NegativeBinomialDistribution,
        ),
        ("poisson", {}, "poisson", PoissonDistribution),
        ("tweedie", {"var_power": 1.1}, "tweedie (1.1)", TweedieDistribution),
    ],
)
def test_assign_family_sets_expected_distribution(
    family, extra_kwargs, expected_family, expected_cls
):
    params = _base_kwargs()
    params.update(extra_kwargs)
    params["family_name"] = family
    model = RegressionGLM(**params)
    assert model.family == expected_family
    assert isinstance(model.family_glum_class, expected_cls)


def test_offsets_and_exposures_computation():
    model = RegressionGLM(
        family_name="gaussian",
        offset_mode="OFFSETS/EXPOSURES",
        column_labels=["feature", "offset_col", "exposure_col"],
        offset_columns=["offset_col"],
        exposure_columns=["exposure_col"],
    )
    X = np.array([[1.0, 0.1, 2.0], [2.0, 0.2, 4.0]])

    offsets, exposures = model.get_offsets_and_exposures(X)
    np.testing.assert_allclose(offsets[:, 0], [0.1, 0.2])
    np.testing.assert_allclose(exposures[:, 0], [2.0, 4.0])

    combined = model.compute_aggregate_offset(offsets, exposures)
    expected = np.array([0.1 + np.log(2.0), 0.2 + np.log(4.0)])
    np.testing.assert_allclose(combined, expected)


def test_compute_aggregate_offset_requires_positive_exposure():
    model = RegressionGLM(family_name="gaussian")
    offsets = np.array([[0.0], [0.2]])
    exposures = np.array([[1.0], [-1.0]])

    with pytest.raises(ValueError, match="Exposure columns contains some negative values"):
        model.compute_aggregate_offset(offsets, exposures)


def test_get_offsets_and_exposures_requires_configured_columns():
    model = RegressionGLM(
        family_name="gaussian",
        offset_mode="OFFSETS",
        column_labels=["feature"],
        offset_columns=[],
    )
    X = np.array([[1.0]])

    with pytest.raises(
        ValueError, match="OFFSETS mode is selected but no offset column is defined"
    ):
        model.get_offsets_and_exposures(X)


def test_process_fixed_columns_removes_offsets_exposures_and_na_columns():
    model = RegressionGLM(
        family_name="gaussian",
        offset_mode="OFFSETS/EXPOSURES",
        column_labels=[
            "feat1",
            "offset_col",
            "feat2",
            "exposure_col",
            "feat3_N/A",
        ],
        offset_columns=["offset_col"],
        exposure_columns=["exposure_col"],
    )
    model.offset_indices = [1]
    model.exposure_indices = [3]
    X = np.arange(10).reshape(2, 5)

    processed = model.process_fixed_columns(X.copy())

    np.testing.assert_array_equal(processed, X[:, [0, 2]])
    assert model.final_labels == ["feat1", "feat2"]
    assert sorted(model.removed_indices) == [1, 3, 4]


def test_compute_coefs_inserts_zero_for_removed_features():
    model = RegressionGLM(family_name="gaussian")

    class DummyModel:
        coef_ = np.array([1.0, -1.0])
        intercept_ = 0.5

    model.fitted_model = DummyModel()
    model.removed_indices = [2, 0, 2]

    model.compute_coefs(prediction_is_classification=False)

    np.testing.assert_array_equal(model.coef_, np.array([0.0, 1.0, 0.0, -1.0]))
    assert model.intercept_ == 0.5


def test_compute_coefs_wraps_classification_outputs():
    model = BinaryClassificationGLM()

    class DummyModel:
        coef_ = np.array([0.3])
        intercept_ = 0.2

    model.fitted_model = DummyModel()
    model.removed_indices = None

    model.compute_coefs(prediction_is_classification=True)

    assert model.intercept_ == [0.2]
    np.testing.assert_array_equal(model.coef_, np.array([[0.3]]))


def test_set_interactions_uses_config(monkeypatch):
    captured = {}

    class FakeInteractions:
        def __init__(self, first, second):
            captured["first"] = first
            captured["second"] = second

        def transform(self, X, labels):
            return X

    monkeypatch.setattr(dku_glm, "Interactions", FakeInteractions)

    model = RegressionGLM(
        family_name="gaussian",
        interaction_columns_first=["col_a"],
        interaction_columns_second=["col_b"],
    )

    model.set_interactions()

    assert captured["first"] == ["col_a"]
    assert captured["second"] == ["col_b"]


def test_binary_prediction_helpers_use_predict_target(monkeypatch):
    outputs = []

    def fake_predict_target(self, X):
        outputs.append(X.shape)
        return np.array([0.4, 0.6])

    monkeypatch.setattr(BinaryClassificationGLM, "predict_target", fake_predict_target)

    model = BinaryClassificationGLM()

    preds = model.predict(np.zeros((2, 1)))
    assert preds.tolist() == [False, True]

    probas = model.predict_proba(np.zeros((2, 1)))
    np.testing.assert_array_equal(probas[:, 1], np.array([0.4, 0.6]))
    np.testing.assert_array_equal(probas.sum(axis=1), np.ones(2))

    assert outputs == [(2, 1), (2, 1)]
