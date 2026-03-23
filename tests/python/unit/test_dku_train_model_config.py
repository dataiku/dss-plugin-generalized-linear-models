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


def test_normalize_spline_segments_caps_each_feature_to_five_knots():
    raw = [
        {"min_value": 0, "max_value": 10, "degree": 1},
        {"min_value": 10, "max_value": 20, "degree": 1},
        {"min_value": 20, "max_value": 30, "degree": 1},
        {"min_value": 30, "max_value": 40, "degree": 1},
        {"min_value": 40, "max_value": 50, "degree": 1},
        {"min_value": 50, "max_value": 60, "degree": 1},
        {"min_value": 60, "max_value": 70, "degree": 1},
    ]

    normalized = DKUVisualMLConfig._normalize_spline_segments(raw)

    assert len(normalized) == 6
    assert normalized[-1] == {"min_value": 50.0, "max_value": 60.0, "degree": 1}


def test_get_feature_spline_features_caps_flat_backward_compatible_definitions():
    config = DKUVisualMLConfig()
    config.variables = {
        "DriverAge": {
            "spline_definitions": [
                {"min_value": 0, "max_value": 10, "degree": 1},
                {"min_value": 10, "max_value": 20, "degree": 1},
                {"min_value": 20, "max_value": 30, "degree": 1},
                {"min_value": 30, "max_value": 40, "degree": 1},
                {"min_value": 40, "max_value": 50, "degree": 1},
                {"min_value": 50, "max_value": 60, "degree": 1},
                {"min_value": 60, "max_value": 70, "degree": 1},
            ]
        }
    }

    normalized = config.get_feature_spline_features("DriverAge")

    assert len(normalized) == 1
    assert len(normalized[0]) == 6
    assert normalized[0][-1] == {"min_value": 50.0, "max_value": 60.0, "degree": 1}


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


def test_normalize_categorical_groups_filters_invalid_and_duplicates():
    raw_groups = [
        ["A", "B", "B"],
        ["B", "C"],  # "B" already used
        ["D"],       # too short
        "bad",
        ["E", "F", "G"],
    ]

    normalized = DKUVisualMLConfig._normalize_categorical_groups(raw_groups)

    assert normalized == [["A", "B"], ["E", "F", "G"]]


def test_get_feature_categorical_groups_supports_backend_and_frontend_keys():
    config = DKUVisualMLConfig()
    config.variables = {
        "Area": {
            "categorical_groups": [["A", "B"], ["C", "D"]],
        },
        "Region": {
            "categoricalGroups": [["X", "Y"]],
        },
    }

    assert config.get_feature_categorical_groups("Area") == [["A", "B"], ["C", "D"]]
    assert config.get_feature_categorical_groups("Region") == [["X", "Y"]]


def test_build_categorical_custom_handling_code_includes_groups():
    code = DKUVisualMLConfig.build_categorical_custom_handling_code(
        base_level="A",
        categorical_groups=[["A", "B"], ["C", "D"]],
    )

    assert "from processors.processors import rebase_mode" in code
    assert '"base_level": \'A\'' in code
    assert '"categorical_groups": [[\'A\', \'B\'], [\'C\', \'D\']]' in code


def test_update_model_parameters_parses_single_weight_exposure_and_offsets():
    config = DKUVisualMLConfig()
    config.update_model_parameters({
        "targetColumn": "claim_count",
        "exposureColumn": "exposure",
        "sampleWeightColumn": "sample_w",
        "offsetColumns": ["offset_a", "offset_b", "offset_a"],
        "variables": {},
    })

    assert config.target_column == "claim_count"
    assert config.exposure_column == "exposure"
    assert config.sample_weight_column == "sample_w"
    assert config.offset_columns == ["offset_a", "offset_b"]


def test_get_model_features_excludes_target_exposure_sample_weight_and_offsets():
    config = DKUVisualMLConfig()
    config.target_column = "target"
    config.exposure_column = "exposure"
    config.sample_weight_column = "sample_weight"
    config.offset_columns = ["offset_a", "offset_b"]
    config.variables = {
        "target": {"included": True},
        "exposure": {"included": True},
        "sample_weight": {"included": True},
        "offset_a": {"included": True},
        "offset_b": {"included": True},
        "feature_1": {"included": True},
        "feature_2": {"included": False},
    }

    assert config.get_model_features() == ["feature_1"]


def test_get_excluded_features_excludes_only_model_features():
    config = DKUVisualMLConfig()
    config.target_column = "target"
    config.exposure_column = "exposure"
    config.sample_weight_column = "sample_weight"
    config.offset_columns = ["offset_a", "offset_b"]
    config.variables = {
        "target": {"included": False},
        "exposure": {"included": False},
        "sample_weight": {"included": False},
        "offset_a": {"included": False},
        "offset_b": {"included": False},
        "feature_1": {"included": True},
        "feature_2": {"included": False},
        "feature_3": {"included": False},
    }

    assert config.get_excluded_features() == ["feature_2", "feature_3"]
