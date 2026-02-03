from generalized_linear_models.dku_glm import RegressionGLM, link
import statsmodels.api as sm
from testing_utils import testing_dict
import generalized_linear_models.link as link
from glum import GammaDistribution
from numpy.testing import assert_almost_equal


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
        regression_model = RegressionGLM(
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
        regression_model.assign_family()
        actual.append(regression_model.get_link_function())

    for act, exp in zip(actual, expected):
        assert type(act) == type(exp)


def test_regression():
    data = sm.datasets.scotland.load()
    X = data.exog.to_numpy()
    y = data.endog.to_numpy()

    regression_model = RegressionGLM(
        penalty=0.0,
        offset_mode='BASIC',
        family_name='gamma',
        binomial_link=None,
        gamma_link="inverse_power",
        gaussian_link=None,
        inverse_gaussian_link=None,
        poisson_link=None,
        negative_binomial_link=None,
        tweedie_link=None,
        alpha=1,
        l1_ratio=1,
        power=1,
        var_power=1)
    regression_model.column_labels = data.exog_name

    regression_model.fit(X, y)
    bic = regression_model.fitted_model.bic(X,y)
    aic = regression_model.fitted_model.aic(X,y)
    predictions = regression_model.fitted_model.predict(X)
    deviance = GammaDistribution().deviance(y, predictions)
    actual_metrics = [bic, aic, deviance]

    expected_metrics = [192.67724083842805, 180.95135361603025, 0.08738851641699652]
    for act, exp in zip(actual_metrics, expected_metrics):
        assert_almost_equal(act, exp, decimal=8)
    
    actual_coefs = regression_model.coef_.tolist()
    expected_coefs = [4.96176830e-05,  2.03442259e-03, -7.18142874e-05,  1.11852013e-04,
       -1.46751504e-07, -5.18683112e-04, -2.42717498e-06]

    for act, exp in zip(actual_coefs, expected_coefs):
        assert_almost_equal(act, exp, decimal=8)

def test_regression_regularized():
    data = sm.datasets.scotland.load()
    X = data.exog.to_numpy()
    y = data.endog.to_numpy()
    penalty = 0.05
    l1_ratio = 0.5
    
    regression_model = RegressionGLM(
        penalty=penalty,
        offset_mode='BASIC',
        family_name='gaussian',
        binomial_link=None,
        gamma_link=None,
        gaussian_link='identity',
        inverse_gaussian_link=None,
        poisson_link=None,
        negative_binomial_link=None,
        tweedie_link=None,
        alpha=1,
        l1_ratio=l1_ratio,
        power=1,
        var_power=1)
    regression_model.column_labels = data.exog_name

    regression_model.fit(X, y)
    actual_intercept = regression_model.intercept_
    expected_intercept = 117.25972889136088
    assert_almost_equal(actual_intercept, expected_intercept, decimal=8)

    actual_coeffs = regression_model.coef_.tolist()
    expected_coeffs = [-8.21616874e-02, -4.04677477e+00,  2.77749123e-01, -4.19380027e-01,
        3.97194059e-04, 1.58391613e+00, 4.31070244e-03]
    
    for act, exp in zip(actual_coeffs, expected_coeffs):
        assert_almost_equal(act, exp, decimal=6)


def test_regression_offset():
    data = sm.datasets.scotland.load()
    X = data.exog.to_numpy()
    y = data.endog.to_numpy()

    regression_model = RegressionGLM(
        penalty=0.0,
        offset_mode='OFFSETS',
        family_name='gaussian',
        binomial_link=None,
        gamma_link=None,
        gaussian_link='identity',
        inverse_gaussian_link=None,
        poisson_link=None,
        negative_binomial_link=None,
        tweedie_link=None,
        alpha=1,
        l1_ratio=1,
        power=1,
        var_power=1,
        offset_columns=['COUTAX', 'COUTAX_FEMALEUNEMP'])

    regression_model.column_labels = data.exog_name

    regression_model.fit(X, y)

    actual_intercept = regression_model.intercept_
    expected_intercept = -19181.13398080061

    assert_almost_equal(actual_intercept, expected_intercept, decimal=8)

    actual_coeffs = regression_model.coef_.tolist()
    expected_coeffs = [0, -6.0979164787e+02, -7.6774362552e+01,  1.8442285217e+02,
       -2.0043622454e-01, 8.2804923521e+02, 0]
    
    for act, exp in zip(actual_coeffs, expected_coeffs):
        assert_almost_equal(act, exp, decimal=8)

def test_regression_exposure():
    data = sm.datasets.scotland.load()
    X = data.exog.to_numpy()
    y = data.endog.to_numpy()

    regression_model = RegressionGLM(
        penalty=0.0,
        offset_mode='OFFSETS/EXPOSURES',
        family_name='poisson',
        binomial_link=None,
        gamma_link=None,
        gaussian_link=None,
        inverse_gaussian_link=None,
        poisson_link='log',
        negative_binomial_link=None,
        tweedie_link=None,
        alpha=1,
        l1_ratio=1,
        power=1,
        var_power=1,
        offset_columns=['UNEMPF'],
        exposure_columns=['COUTAX'])
    regression_model.column_labels = data.exog_name

    regression_model.fit(X, y)

    actual_intercept = regression_model.intercept_
    expected_intercept = -6.010622687340117

    assert_almost_equal(actual_intercept, expected_intercept, decimal=8)

    actual_coeffs = regression_model.coef_.tolist()
    expected_coeffs = [ 0.00000000e+00,  0.00000000e+00,  1.40475935e-01, -1.97538883e-01,
  2.30857075e-04, -7.58148554e-01, -7.11379211e-04]
    
    for act, exp in zip(actual_coeffs, expected_coeffs):
        assert_almost_equal(act, exp, decimal=8)

def test_regression_prediction():
    data = sm.datasets.scotland.load()
    X = data.exog.to_numpy()
    y = data.endog.to_numpy()

    regression_model = RegressionGLM(
        penalty=0.0,
        offset_mode='OFFSETS/EXPOSURES',
        family_name='poisson',
        binomial_link=None,
        gamma_link=None,
        gaussian_link=None,
        inverse_gaussian_link=None,
        poisson_link='log',
        negative_binomial_link=None,
        tweedie_link=None,
        alpha=1,
        l1_ratio=1,
        power=1,
        var_power=1,
        exposure_columns=['COUTAX'])
    
    regression_model.column_labels = data.exog_name

    regression_model.fit(X, y)
    actual_predictions = regression_model.predict(X)
    expected_predictions = [57.76802588, 54.47997709, 51.6377914 , 53.31193146, 69.02232649,
       57.23920141, 66.62034567, 66.67240667, 57.71413605, 62.42490877,
       55.06389148, 60.63319335, 60.577439  , 62.88577001, 61.13078062,
       78.16279826, 56.36494114, 73.9596681 , 66.32083011, 52.79675766,
       63.15624222, 69.63126407, 50.52415796, 55.38377951, 66.98836753,
       53.97285276, 54.53709653, 57.7956278 , 65.84038082, 60.16808029,
       76.9708523 , 66.34417941]

    for act, exp in zip(actual_predictions, expected_predictions):
        assert_almost_equal(act, exp, decimal=8)
