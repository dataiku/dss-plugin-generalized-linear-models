import pandas as pd

from glm_handler.glm_data_handler import GlmDataHandler
from chart_formatters.lift_chart import LiftChartFormatter


def test_sort_and_cumsum_exposure_uses_ranking_exposure_when_provided():
    handler = GlmDataHandler()
    df = pd.DataFrame(
        {
            "predicted": [100.0, 50.0],
            "weight": [10.0, 1.0],      # sample weight style column
            "exposure": [100.0, 10.0],  # true exposure for risk ranking
        }
    )

    sorted_df = handler.sort_and_cumsum_exposure(df.copy(), "weight", ranking_exposure="exposure")

    # ranked by predicted/exposure: 1.0 (first row) then 5.0 (second row)
    assert list(sorted_df["predicted"]) == [100.0, 50.0]
    assert sorted_df["exposure_cumsum"].iloc[-1] == 1.0
    # cumsum mass uses the provided cumsum weight directly
    # row masses: 10 then 1 -> first cumsum is 10/11
    assert abs(sorted_df["exposure_cumsum"].iloc[0] - (10.0 / 11.0)) < 1e-9


def test_sort_and_cumsum_exposure_defaults_to_predicted_when_no_ranking_exposure():
    handler = GlmDataHandler()
    df = pd.DataFrame(
        {
            "predicted": [100.0, 50.0],
            "weight": [10.0, 1.0],
        }
    )

    sorted_df = handler.sort_and_cumsum_exposure(df.copy(), "weight")

    # ranked by predicted ascending
    assert list(sorted_df["predicted"]) == [50.0, 100.0]
    assert sorted_df["exposure_cumsum"].iloc[-1] == 1.0


def test_sort_and_cumsum_exposure_does_not_square_when_weight_is_exposure():
    handler = GlmDataHandler()
    df = pd.DataFrame(
        {
            "predicted": [10.0, 50.0],
            "exposure": [1.0, 9.0],
        }
    )

    sorted_df = handler.sort_and_cumsum_exposure(df.copy(), "exposure", ranking_exposure="exposure")

    # ranked by predicted/exposure: 10 then ~5.56, so second row first
    assert list(sorted_df["predicted"]) == [50.0, 10.0]
    # cumsum uses exposure only (not exposure^2)
    assert abs(sorted_df["exposure_cumsum"].iloc[0] - 0.9) < 1e-9


def test_aggregate_metrics_by_bin_can_label_with_ranking_metric():
    handler = GlmDataHandler()
    df = pd.DataFrame(
        {
            "bin": [1, 1, 2, 2],
            "weight": [1.0, 1.0, 1.0, 1.0],
            "weighted_target": [10.0, 20.0, 30.0, 40.0],
            "weighted_predicted": [12.0, 18.0, 33.0, 39.0],
            "predicted": [1590.0, 8300.0, 2450.0, 10400.0],
            "raw_predict": [1.1, 1.3, 1.4, 1.6],
        }
    )

    aggregated = handler.aggregate_metrics_by_bin(df, "weight", "target", label_column="raw_predict")

    assert list(aggregated["binInterval"]) == ["1.1-1.3", "1.4-1.6"]


def test_lift_chart_formatter_uses_raw_predict_labels_when_exposure_is_present():
    class StubModelRetriever:
        exposure_columns = "exposure"
        target_column = "target"

    handler = GlmDataHandler()
    formatter = LiftChartFormatter(StubModelRetriever(), handler)
    dataset = pd.DataFrame(
        {
            "predicted": [1590.0, 8300.0, 2450.0, 10400.0],
            "weight": [1.0, 1.0, 1.0, 1.0],
            "exposure": [1000.0, 5000.0, 1400.0, 5200.0],
            "target": [10.0, 20.0, 30.0, 40.0],
            "weighted_target": [10.0, 20.0, 30.0, 40.0],
            "weighted_predicted": [1590.0, 8300.0, 2450.0, 10400.0],
        }
    )

    processed = formatter.get_lift_chart(nb_bins=2, train_set=dataset, test_set=dataset)
    train_processed = processed[processed["dataset"] == "train"].reset_index(drop=True)

    assert list(train_processed["Category"]) == ["1.59-1.66", "1.75-2.0"]
