import dataiku
from dataiku.customrecipe import get_input_names_for_role, get_output_names_for_role
from dku_config import DkuConfig


def get_input_output():
    if len(get_input_names_for_role('input_dataset')) == 0:
        raise ValueError('No input dataset.')
    if len(get_output_names_for_role('output_dataset')) == 0:
        raise ValueError('No output dataset.')
    input_dataset_name = get_input_names_for_role('input_dataset')[0]
    input_dataset = dataiku.Dataset(input_dataset_name)
    output_dataset_name = get_output_names_for_role('output_dataset')[0]
    output_dataset = dataiku.Dataset(output_dataset_name)
    return (input_dataset, output_dataset)


def check_params(params):
    dku_config = DkuConfig()

    dku_config.add_param(
        name="family_name",
        value=params.get('family_name'),
        checks=[{
            "type": "in",
            "op": ["binomial", "gamma", "gaussian", "inverse_gaussian", "poisson", "negative_binomial", "tweedie"]
        }],
        required=True
    )

    if params.get('family_name') == 'binomial':
        dku_config.add_param(
            name="binomial_link",
            value=params.get('binomial_link'),
            checks=[{
                "type": "in",
                "op": ["cloglog", "log", "logit", "cauchy", "identity"]
            }],
            required=False
        )

    if params.get('family_name') == 'gamma':
        dku_config.add_param(
            name="gamma_link",
            value=params.get('gamma_link'),
            checks=[{
                "type": "in",
                "op": ["log", "identity", "inverse_power"]
            }],
            required=False
        )

    if params.get('family_name') == 'gaussian':
        dku_config.add_param(
            name="gaussian_link",
            value=params.get('gaussian_link'),
            checks=[{
                "type": "in",
                "op": ["log", "identity", "inverse_power"]
            }],
            required=False
        )

    if params.get('family_name') == 'inverse_gaussian':
        dku_config.add_param(
            name="inverse_gaussian_link",
            value=params.get('inverse_gaussian_link'),
            checks=[{
                "type": "in",
                "op": ["log", "inverse_squared", "identity", "inverse_power"]
            }],
            required=False
        )

    if params.get('family_name') == 'poisson':
        dku_config.add_param(
            name="poisson_link",
            value=params.get('poisson_link'),
            checks=[{
                "type": "in",
                "op": ["log", "identity"]
            }],
            required=False
        )

    if params.get('family_name') == 'negative_binomial':
        dku_config.add_param(
            name="negative_binomial_link",
            value=params.get('negative_binomial_link'),
            checks=[{
                "type": "in",
                "op": ["log", "cloglog", "identity", "power"]
            }],
            required=False
        )

    if params.get('family_name') == 'tweedie':
        dku_config.add_param(
            name="tweedie_link",
            value=params.get('tweedie_link'),
            checks=[{
                "type": "in",
                "op": ["log", "power"]
            }],
            required=False
        )

    if params.get('family_name') == 'negative_binomial':
        dku_config.add_param(
            name="alpha",
            value=params.get('alpha'),
            checks=[{
                "type": "between",
                "op": (0.01, 2)
            }],
            required=False
        )

    if (params.get('family_name') == 'negative_binomial' and params.get('negative_binomial_link') == 'power') or (
            params.get('family_name') == 'tweedie' and params.get('tweedie_link') == 'power'
    ):
        dku_config.add_param(
            name="power",
            value=params.get('power'),
            required=False
        )

    if not isinstance(params.get('penalty'), list):
        params['penalty'] = [params.get('penalty')]
    for i, penalty in enumerate(params.get('penalty')):
        dku_config.add_param(
            name="penalty_" + str(i),
            value=penalty,
            checks=[{
                "type": "sup_eq",
                "op": 0
            }],
            required=True
        )

    dku_config.penalty = [dku_config.get("penalty_" + str(i)) for i in range(len(params.get('penalty')))]

    if not isinstance(params.get('l1_ratio'), list):
        params['l1_ratio'] = [params.get('l1_ratio')]
    for i, l1_ratio in enumerate(params.get('l1_ratio')):
        dku_config.add_param(
            name="l1_ratio" + str(i),
            value=l1_ratio,
            checks=[{
                "type": "sup_eq",
                "op": 0
            },
                {
                    "type": "inf_eq",
                    "op": 1
                }
            ],
            required=True
        )

    dku_config.l1_ratio = [dku_config.get("l1_ratio" + str(i)) for i in range(len(params.get('l1_ratio')))]

    if params.get('family_name') == 'tweedie':
        dku_config.add_param(
            name="var_power",
            value=params.get('var_power'),
            required=False
        )

    dku_config.add_param(
        name="offset_mode",
        value=params.get('offset_mode'),
        checks=[{
            "type": "in",
            "op": ['BASIC', 'OFFSETS', 'OFFSETS/EXPOSURES']
        }],
        required=True
    )

    if dku_config.get('offset_mode') != 'BASIC':
        project_key = dataiku.get_custom_variables()["projectKey"]
        project = dataiku.api_client().get_project(project_key)

        allowed_datasets_names = [analysis['inputDataset'] for analysis in project.list_analyses()]

        dku_config.add_param(
            name="training_dataset",
            value=params.get('training_dataset'),
            checks=[{
                "type": "in",
                "op": allowed_datasets_names
            }],
            required=True
        )
        dataset = dataiku.Dataset(params.get('training_dataset'), project_key)

    if dku_config.get('offset_mode') != 'BASIC':
        if params.get('offset_columns'):
            for i, offset_column in enumerate(params.get('offset_columns')):
                dku_config.add_param(
                    name="offset_column_" + str(i),
                    value=offset_column,
                    checks=[{
                        "type": "in",
                        "op": dataset.get_dataframe().columns
                    }],
                    required=True
                )
            dku_config.offset_columns = params.get('offset_columns')

    if dku_config.get('offset_mode') == 'OFFSETS/EXPOSURES':
        if params.get('exposure_columns'):
            for i, exposure_column in enumerate(params.get('exposure_columns')):
                dku_config.add_param(
                    name="exposure_column_" + str(i),
                    value=exposure_column,
                    checks=[{
                        "type": "in",
                        "op": dataset.get_dataframe().columns
                    }],
                    required=True
                )
            dku_config.exposure_columns = params.get('exposure_columns')

    dku_config.add_param(
            name="solver",
            value=params.get("solver"),
            checks=[{
                "type": "in",
                "op": ['auto', 'irls-cd', 'irls-ls', 'lbfgs', 'trust-constr']
            }],
            required=True
        )
    
    dku_config.add_param(
            name="max_iter",
            value=params.get("max_iter"),
            checks=[{
                "type": "sup_eq",
                "op": 0
            }],
            required=True
        )
    
    dku_config.add_param(
            name="gradient_tol",
            value=params.get("gradient_tol"),
            checks=[{
                "type": "sup_eq",
                "op": 0
            }],
            required=True
        )
    
    dku_config.add_param(
            name="step_size_tol",
            value=params.get("step_size_tol"),
            checks=[{
                "type": "sup_eq",
                "op": 0
            }],
            required=False
        )

    return dku_config