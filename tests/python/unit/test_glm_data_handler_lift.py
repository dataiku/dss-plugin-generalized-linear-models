import pandas as pd

from glm_handler.glm_data_handler import GlmDataHandler


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
