import pytest

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
