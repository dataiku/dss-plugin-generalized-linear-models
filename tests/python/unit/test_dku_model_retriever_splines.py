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


def test_extract_base_level_from_save_base_single_quoted_string():
    retriever = _make_retriever()
    feature_settings = {
        "customHandlingCode": (
            "from processors.processors import save_base\n"
            "processor = save_base({'base_level': 'BrandA'})\n"
        )
    }

    assert retriever._extract_base_level(feature_settings) == "BrandA"


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


def test_get_exposure_columns_returns_none_when_not_configured():
    retriever = _make_retriever()
    retriever.algo_settings = {"params": {}}
    retriever.exposure_columns = None

    assert retriever.get_exposure_columns() is None


def test_get_offset_columns_returns_empty_list_when_not_configured():
    retriever = _make_retriever()
    retriever.algo_settings = {"params": {}}

    assert retriever.get_offset_columns() == []


def test_get_sample_weight_column_reads_from_core_params():
    retriever = _make_retriever()
    retriever.model_details = type(
        "Details",
        (),
        {
            "details": {
                "coreParams": {
                    "weight": {
                        "weightMethod": "SAMPLE_WEIGHT",
                        "sampleWeightVariable": "sample_w",
                    }
                }
            }
        },
    )()
    retriever.task = None

    assert retriever.get_sample_weight_column() == "sample_w"


def test_get_sample_weight_column_falls_back_to_task_settings():
    retriever = _make_retriever()
    retriever.model_details = type("Details", (), {"details": {"coreParams": {}}})()
    settings = type("Settings", (), {"get_raw": lambda self: {"weight": {"weightMethod": "SAMPLE_WEIGHT", "sampleWeightVariable": "sample_w"}}})()
    retriever.task = type("Task", (), {"get_settings": lambda self: settings})()

    assert retriever.get_sample_weight_column() == "sample_w"


def test_get_sample_weight_column_returns_none_for_no_weighting():
    retriever = _make_retriever()
    retriever.model_details = type(
        "Details",
        (),
        {"details": {"coreParams": {"weight": {"weightMethod": "NO_WEIGHTING"}}}},
    )()
    retriever.task = None

    assert retriever.get_sample_weight_column() is None


def test_get_sample_weight_column_raises_for_unsupported_weighting_method():
    retriever = _make_retriever()
    retriever.model_details = type(
        "Details",
        (),
        {"details": {"coreParams": {"weight": {"weightMethod": "CLASS_WEIGHT"}}}},
    )()
    retriever.task = None

    with pytest.raises(ValueError, match="Unsupported weighting method"):
        retriever.get_sample_weight_column()
