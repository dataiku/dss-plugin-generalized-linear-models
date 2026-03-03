import pandas as pd

from glm_handler.dku_relativites_calculator import RelativitiesCalculator


class _Retriever:
    def __init__(self, exposure=None, sample_weight=None):
        self.exposure_columns = exposure
        self._sample_weight = sample_weight

    def get_sample_weight_column(self):
        return self._sample_weight


def _make_calculator(exposure=None, sample_weight=None):
    calc = RelativitiesCalculator.__new__(RelativitiesCalculator)
    calc.model_retriever = _Retriever(exposure=exposure, sample_weight=sample_weight)
    return calc


def test_compute_effective_weight_exposure_only():
    calc = _make_calculator(exposure="expo", sample_weight=None)
    df = pd.DataFrame({"expo": [2.0, 3.0]})

    series = calc._compute_effective_weight(df)

    assert list(series) == [2.0, 3.0]


def test_compute_effective_weight_sample_weight_only():
    calc = _make_calculator(exposure=None, sample_weight="sw")
    df = pd.DataFrame({"sw": [0.5, 2.0]})

    series = calc._compute_effective_weight(df)

    assert list(series) == [0.5, 2.0]


def test_compute_effective_weight_exposure_and_sample_weight():
    calc = _make_calculator(exposure="expo", sample_weight="sw")
    df = pd.DataFrame({"expo": [2.0, 3.0], "sw": [0.5, 2.0]})

    series = calc._compute_effective_weight(df)

    assert list(series) == [1.0, 6.0]


def test_get_modality_mass_prefers_exposure():
    calc = _make_calculator(exposure="expo", sample_weight="sw")
    df = pd.DataFrame({"expo": [2.0, 3.0], "sw": [0.5, 2.0]})

    series = calc._get_modality_mass(df)

    assert list(series) == [2.0, 3.0]
