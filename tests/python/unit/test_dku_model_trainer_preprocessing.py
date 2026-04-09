import pytest
from unittest.mock import Mock

pytest.importorskip("dataiku")

from dku_visual_ml.dku_model_trainer import VisualMLModelTrainer
from dku_visual_ml.dku_train_model_config import DKUVisualMLConfig


def _make_trainer():
    trainer = VisualMLModelTrainer.__new__(VisualMLModelTrainer)
    trainer.visual_ml_config = DKUVisualMLConfig()
    return trainer


def test_update_to_numeric_uses_continuous_spline_when_features_present():
    trainer = _make_trainer()
    fs = {}
    spline_features = [[{"min_value": 16.0, "max_value": 25.0, "degree": 2}]]

    updated = trainer.update_to_numeric(
        fs,
        base_level=45.0,
        processing="CUSTOM",
        spline_features=spline_features,
    )

    assert updated["numerical_handling"] == "CUSTOM"
    assert "continuous_spline" in updated["customHandlingCode"]
    assert '"spline_features":' in updated["customHandlingCode"]


def test_update_to_numeric_falls_back_to_save_base_without_features():
    trainer = _make_trainer()
    fs = {}

    updated = trainer.update_to_numeric(
        fs,
        base_level=45.0,
        processing="CUSTOM",
        spline_features=[],
    )

    assert updated["numerical_handling"] == "CUSTOM"
    assert "save_base" in updated["customHandlingCode"]
    assert "continuous_spline" not in updated["customHandlingCode"]


def test_update_to_numeric_uses_legacy_save_base_with_none_base_level():
    trainer = _make_trainer()
    fs = {}

    updated = trainer.update_to_numeric(
        fs,
        base_level=None,
        processing="CUSTOM",
        spline_features=[],
    )

    assert updated["numerical_handling"] == "CUSTOM"
    assert '"base_level": None' in updated["customHandlingCode"]
    assert "save_base" in updated["customHandlingCode"]


def test_update_to_numeric_requires_base_level_when_using_spline_features():
    trainer = _make_trainer()

    with pytest.raises(ValueError, match="Spline features require a base_level"):
        trainer.update_to_numeric(
            {},
            base_level=None,
            processing="CUSTOM",
            spline_features=[[{"min_value": 16.0, "max_value": 25.0, "degree": 2}]],
        )


def test_update_to_numeric_regular_processing_has_no_custom_code():
    trainer = _make_trainer()
    fs = {}

    updated = trainer.update_to_numeric(
        fs,
        base_level=None,
        processing="REGULAR",
        spline_features=[],
    )

    assert updated["numerical_handling"] == "REGULAR"
    assert updated["customHandlingCode"] == ""


def test_update_to_categorical_includes_categorical_groups():
    trainer = _make_trainer()
    fs = {}

    updated = trainer.update_to_categorical(
        fs,
        base_level="A",
        categorical_groups=[["A", "B"], ["C", "D"]],
    )

    assert updated["category_handling"] == "CUSTOM"
    assert "rebase_mode" in updated["customHandlingCode"]
    assert '"categorical_groups": [[\'A\', \'B\'], [\'C\', \'D\']]' in updated["customHandlingCode"]


def test_set_sample_weight_variable_sets_sample_weight_method():
    trainer = _make_trainer()
    trainer.visual_ml_config.sample_weight_column = "sample_w"
    settings = Mock()
    settings.get_raw.return_value = {"preprocessing": {"per_feature": {}}}
    trainer.mltask = Mock()
    trainer.mltask.get_settings.return_value = settings

    trainer.set_sample_weight_variable()

    settings.set_weighting.assert_called_once_with("SAMPLE_WEIGHT", "sample_w")
    settings.save.assert_called_once()


def test_set_sample_weight_variable_disables_weighting_when_missing():
    trainer = _make_trainer()
    trainer.visual_ml_config.sample_weight_column = None
    settings = Mock()
    settings.get_raw.return_value = {
        "preprocessing": {
            "per_feature": {
                "old_weight": {"role": "WEIGHT"},
                "feature_a": {"role": "INPUT"},
            }
        }
    }
    trainer.mltask = Mock()
    trainer.mltask.get_settings.return_value = settings

    trainer.set_sample_weight_variable()

    settings.set_weighting.assert_called_once_with("NO_WEIGHTING")
    settings.save.assert_called_once()


def test_update_mltask_modelling_params_clears_stale_family_link_keys():
    trainer = _make_trainer()
    trainer.visual_ml_config.distribution_function = "negative_binomial"
    trainer.visual_ml_config.link_function = "log"
    trainer.visual_ml_config.elastic_net_penalty = 0
    trainer.visual_ml_config.l1_ratio = 0
    trainer.visual_ml_config.theta = 1
    trainer.visual_ml_config.power = 1
    trainer.visual_ml_config.variance_power = 1.5
    trainer.visual_ml_config.get_interaction_variables = Mock(return_value=[])
    trainer.visual_ml_config.get_exposure_variable = Mock(return_value=None)
    trainer.visual_ml_config.get_offset_variables = Mock(return_value=[])

    settings = Mock()
    algo_settings = {
        "params": {
            "negative binomial_link": "log",
            "gaussian_link": "identity",
            "poisson_link": "log",
        }
    }
    settings.get_algorithm_settings.return_value = algo_settings

    trainer.mltask = Mock()
    trainer.mltask.get_settings.return_value = settings
    trainer.process_interaction_columns = Mock(return_value=([], []))

    trainer.update_mltask_modelling_params()

    params = algo_settings["params"]
    assert "negative binomial_link" not in params
    assert "gaussian_link" not in params
    assert "poisson_link" not in params
    assert params["negative_binomial_link"] == "log"
    assert params["family_name"] == "negative_binomial"
    settings.save.assert_called_once()
