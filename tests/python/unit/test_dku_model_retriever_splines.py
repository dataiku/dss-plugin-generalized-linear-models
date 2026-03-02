import pytest

pytest.importorskip("dataiku.doctor.posttraining.model_information_handler")

from dku_visual_ml.dku_model_retrival import VisualMLModelRetriver


def _make_retriever():
    return VisualMLModelRetriver.__new__(VisualMLModelRetriver)


def test_extract_spline_features_from_continuous_spline_code():
    retriever = _make_retriever()
    feature_settings = {
        "customHandlingCode": (
            "from processors.processors import continuous_spline\n"
            'processor = continuous_spline({"base_level": 50, "spline_features": '
            '[[{"min_value": 16, "max_value": 20, "degree": 2}], '
            '[{"min_value": 20, "max_value": 100, "degree": 1}]]})\n'
        )
    }

    assert retriever._extract_base_level(feature_settings) == 50
    assert retriever._extract_spline_features(feature_settings) == [
        [{"min_value": 16.0, "max_value": 20.0, "degree": 2}],
        [{"min_value": 20.0, "max_value": 100.0, "degree": 1}],
    ]


def test_extract_spline_features_backward_compat_with_definitions():
    retriever = _make_retriever()
    feature_settings = {
        "customHandlingCode": (
            "from processors.processors import continuous_spline\n"
            'processor = continuous_spline({"base_level": 50, "definitions": '
            '[{"min_value": 16, "max_value": 20, "degree": 2}]})\n'
        )
    }

    assert retriever._extract_spline_features(feature_settings) == [
        [{"min_value": 16.0, "max_value": 20.0, "degree": 2}]
    ]


def test_extract_spline_features_returns_empty_for_non_spline_processor():
    retriever = _make_retriever()
    feature_settings = {
        "customHandlingCode": (
            "from processors.processors import save_base\n"
            'processor = save_base({"base_level": 50})\n'
        )
    }

    assert retriever._extract_spline_features(feature_settings) == []


def test_extract_categorical_groups_from_rebase_mode_code():
    retriever = _make_retriever()
    feature_settings = {
        "customHandlingCode": (
            "from processors.processors import rebase_mode\n"
            'processor = rebase_mode({"base_level": "A", "categorical_groups": '
            '[["A", "B"], ["C", "D"]]})\n'
        )
    }

    assert retriever._extract_categorical_groups(feature_settings) == [["A", "B"], ["C", "D"]]
