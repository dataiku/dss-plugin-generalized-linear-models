from generalized_linear_models.dku_glm import BinaryClassificationGLM
import statsmodels.api as sm
import generalized_linear_models.link as link
from glum import BinomialDistribution
from numpy.testing import assert_almost_equal
from testing_utils import testing_dict

def test_link_function():
    expected = [
        "log",
        "identity",
        link.InversePower(),
        link.InverseSquared(),
        "log",
        "cloglog",
        link.Power(1)
    ]

    actual = []

    for test in testing_dict:
        test_params = testing_dict[test]
        binary_model = BinaryClassificationGLM(
            penalty=0.0,
            offset_mode='BASIC',
            family_name=test_params['family_name'],
            binomial_link=test_params['binomial_link'],
            gamma_link=test_params['gamma_link'],
            gaussian_link=test_params['gaussian_link'],
            inverse_gaussian_link=test_params['inverse_gaussian_link'],
            poisson_link=test_params['poisson_link'],
            negative_binomial_link=test_params['negative_binomial_link'],
            tweedie_link=test_params['tweedie_link'],
            alpha=1,
            l1_ratio=1,
            power=1,
            var_power=1)
        binary_model.assign_family()
        actual.append(binary_model.get_link_function())

    for act, exp in zip(actual, expected):
        assert type(act) == type(exp)



def test_classification():
    data = sm.datasets.ccard.load()
    X = data.exog.to_numpy()
    X = X[:, :3]
    y = data.exog.to_numpy()
    y= y[:, 3]

    binary_model = BinaryClassificationGLM(
        penalty=0.0,
        offset_mode='BASIC',
        family_name='binomial',
        binomial_link='logit',
        gamma_link=None,
        gaussian_link=None,
        inverse_gaussian_link=None,
        poisson_link=None,
        negative_binomial_link=None,
        tweedie_link=None,
        alpha=1,
        l1_ratio=1,
        power=1,
        var_power=1)
    
    binary_model.column_labels = data.exog_name[:3]

    binary_model.fit(X, y)
    # bic, aic, deviance
    bic = binary_model.fitted_model.bic(X,y)
    aic = binary_model.fitted_model.aic(X,y)
    predictions = binary_model.fitted_model.predict(X)
    deviance = BinomialDistribution().deviance(y, predictions)
    actual_metrics = [bic, aic, deviance]

    expected_metrics = [87.28150026085339, 78.17483578478917, 70.17483578478917]

    for act, exp in zip(actual_metrics, expected_metrics):
        assert_almost_equal(act, exp, decimal=12)

    [actual_coefs] = binary_model.coef_.tolist()
    expected_coefs = [0.10960659, -0.45391489,  0.14102368]

    for act, exp in zip(actual_coefs, expected_coefs):
        assert_almost_equal(act, exp, decimal=8)


def test_classification_predictions():
    data = sm.datasets.ccard.load()
    X = data.exog.to_numpy()
    X = X[:, :3]
    y = data.exog.to_numpy()
    y = y[:, 3]

    binary_model = BinaryClassificationGLM(
        penalty=0.0,
        offset_mode='BASIC',
        family_name='binomial',
        binomial_link='logit',
        gamma_link=None,
        gaussian_link=None,
        inverse_gaussian_link=None,
        poisson_link=None,
        negative_binomial_link=None,
        tweedie_link=None,
        alpha=1,
        l1_ratio=1,
        power=1,
        var_power=1)
    
    binary_model.column_labels = data.exog_name[:3]

    binary_model.fit(X, y)
    actual_predictions = [x > 0.5 for x in binary_model.predict(X)]
    expected_predictions = [True,
    False, True, False, True, False, False, False, True, False, False, False, False, True, True, True, False, False, True, True, False, False, True, False, False, False, False,
    True, True, False, False, False, False, False, False, False, False, False, True, False, False, False, False, False, True, False, False, False, False, False, False, True,
    True, False, False, False, False, False, False, False, False, False, False, True, False, False, True, True, True, False, False, True]

    for act, exp in zip(actual_predictions, expected_predictions):
        assert act == exp
