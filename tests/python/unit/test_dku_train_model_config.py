import pytest

from dku_visual_ml.dku_train_model_config import DKUVisualMLConfig


def test_normalize_spline_segments_filters_and_coerces_values():
    raw = [
        {"min_value": "16", "max_value": 25, "degree": "2"},
        {"min_value": 25, "max_value": 65, "degree": 0},
        {"min_value": 65, "max_value": 100, "degree": 1.9},
        {"min_value": 10, "max_value": 20},
        "bad",
    ]

    normalized = DKUVisualMLConfig._normalize_spline_segments(raw)

    assert normalized == [
        {"min_value": 16.0, "max_value": 25.0, "degree": 2},
        {"min_value": 25.0, "max_value": 65.0, "degree": 0},
        {"min_value": 65.0, "max_value": 100.0, "degree": 1},
    ]


@pytest.mark.parametrize("raw", [None, {}, "bad", 1, 1.2])
def test_normalize_spline_segments_rejects_non_list(raw):
    assert DKUVisualMLConfig._normalize_spline_segments(raw) == []


def test_get_feature_spline_features_returns_empty_for_missing_feature():
    config = DKUVisualMLConfig()
    config.variables = {}
    assert config.get_feature_spline_features("missing") == []


def test_get_feature_spline_features_returns_normalized_values():
    config = DKUVisualMLConfig()
    config.variables = {
        "DriverAge": {
            "spline_features": [
                [
                    {"min_value": 16, "max_value": 25, "degree": 2},
                    {"min_value": "bad", "max_value": 65, "degree": 0},
                ],
                [
                    {"min_value": 25, "max_value": 100, "degree": 1}
                ],
            ]
        }
    }

    assert config.get_feature_spline_features("DriverAge") == [
        [{"min_value": 16.0, "max_value": 25.0, "degree": 2}],
        [{"min_value": 25.0, "max_value": 100.0, "degree": 1}],
    ]


def test_build_numeric_custom_handling_code_uses_splines_when_present():
    spline_features = [[{"min_value": 16.0, "max_value": 25.0, "degree": 2}]]
    code = DKUVisualMLConfig.build_numeric_custom_handling_code(
        base_level=45.0,
        spline_features=spline_features,
    )

    assert "from processors.processors import continuous_spline" in code
    assert '"base_level": 45.0' in code
    assert '"spline_features":' in code


def test_build_numeric_custom_handling_code_falls_back_to_save_base():
    code = DKUVisualMLConfig.build_numeric_custom_handling_code(
        base_level=45.0,
        spline_features=[],
    )

    assert "from processors.processors import save_base" in code
    assert "continuous_spline" not in code


def test_build_numeric_custom_handling_code_requires_base_level_for_splines():
    with pytest.raises(ValueError, match="Spline features require a base_level"):
        DKUVisualMLConfig.build_numeric_custom_handling_code(
            base_level=None,
            spline_features=[[{"min_value": 16.0, "max_value": 25.0, "degree": 2}]],
        )
