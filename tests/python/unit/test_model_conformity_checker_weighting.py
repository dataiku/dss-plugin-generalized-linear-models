from model_cache.model_conformity_checker import ModelConformityChecker


def _checker_with_weight(weight_details):
    checker = ModelConformityChecker.__new__(ModelConformityChecker)
    checker.model_details = type(
        "Details",
        (),
        {"details": {"coreParams": {"weight": weight_details}}},
    )()
    return checker


def test_check_no_weighting_accepts_no_weighting():
    checker = _checker_with_weight({"weightMethod": "NO_WEIGHTING"})
    assert checker.check_no_weighting() is True


def test_check_no_weighting_accepts_sample_weight():
    checker = _checker_with_weight(
        {"weightMethod": "SAMPLE_WEIGHT", "sampleWeightVariable": "sample_w"}
    )
    assert checker.check_no_weighting() is True


def test_check_no_weighting_rejects_unsupported_method():
    checker = _checker_with_weight({"weightMethod": "CLASS_WEIGHT"})
    assert checker.check_no_weighting() is False


def test_check_no_weighting_rejects_sample_weight_without_column():
    checker = _checker_with_weight({"weightMethod": "SAMPLE_WEIGHT"})
    assert checker.check_no_weighting() is False


def test_check_feature_handling_rejects_unsupported_role():
    checker = ModelConformityChecker.__new__(ModelConformityChecker)
    checker.model_details = type(
        "Details",
        (),
        {
            "details": {
                "preprocessing": {
                    "per_feature": {
                        "x": {"role": "EXPOSURE", "type": "NUMERIC", "rescaling": "NONE"},
                    }
                }
            }
        },
    )()

    assert checker.check_feature_handling() is False


def test_check_feature_handling_accepts_weight_role():
    checker = ModelConformityChecker.__new__(ModelConformityChecker)
    checker.model_details = type(
        "Details",
        (),
        {
            "details": {
                "preprocessing": {
                    "per_feature": {
                        "w": {"role": "WEIGHT", "type": "NUMERIC", "rescaling": "NONE"},
                    }
                }
            }
        },
    )()

    assert checker.check_feature_handling() is True
