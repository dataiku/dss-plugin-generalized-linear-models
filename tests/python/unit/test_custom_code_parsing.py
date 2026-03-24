from dku_visual_ml.custom_code_parsing import (
    extract_base_level_from_custom_handling_code,
    extract_processor_config_from_custom_code,
)


def test_extract_processor_config_from_custom_code_returns_rebase_mode_config():
    custom_code = (
        "from processors.processors import rebase_mode\n"
        "processor = rebase_mode({'base_level': 'A', 'categorical_groups': [['A', 'B']]})\n"
    )

    processor_name, config_dict = extract_processor_config_from_custom_code(
        custom_code,
        ("rebase_mode",),
    )

    assert processor_name == "rebase_mode"
    assert config_dict == {"base_level": "A", "categorical_groups": [["A", "B"]]}


def test_extract_base_level_from_custom_code_ast_single_quoted_string():
    custom_code = (
        "from processors.processors import save_base\n"
        "processor = save_base({'base_level': 'BrandA'})\n"
    )

    base_level, processor_name, parsing_path = extract_base_level_from_custom_handling_code(custom_code)

    assert base_level == "BrandA"
    assert processor_name == "save_base"
    assert parsing_path == "ast"


def test_extract_base_level_from_custom_code_ast_double_quoted_string():
    custom_code = (
        "from processors.processors import save_base\n"
        'processor = save_base({"base_level": "BrandA"})\n'
    )

    base_level, processor_name, parsing_path = extract_base_level_from_custom_handling_code(custom_code)

    assert base_level == "BrandA"
    assert processor_name == "save_base"
    assert parsing_path == "ast"


def test_extract_base_level_from_custom_code_ast_numeric():
    custom_code = (
        "from processors.processors import continuous_spline\n"
        'processor = continuous_spline({"base_level": 50, "spline_features": []})\n'
    )

    base_level, processor_name, parsing_path = extract_base_level_from_custom_handling_code(custom_code)

    assert base_level == 50
    assert processor_name == "continuous_spline"
    assert parsing_path == "ast"


def test_extract_base_level_from_custom_code_ast_none():
    custom_code = (
        "from processors.processors import save_base\n"
        "processor = save_base({'base_level': None})\n"
    )

    base_level, processor_name, parsing_path = extract_base_level_from_custom_handling_code(custom_code)

    assert base_level is None
    assert processor_name == "save_base"
    assert parsing_path == "ast"


def test_extract_base_level_from_custom_code_regex_fallback():
    custom_code = "processor = save_base({'base_level': 'BrandA'\n"

    base_level, processor_name, parsing_path = extract_base_level_from_custom_handling_code(custom_code)

    assert base_level == "BrandA"
    assert processor_name is None
    assert parsing_path == "regex_fallback"


def test_extract_base_level_from_release_105_legacy_numeric_mode_column():
    custom_code = (
        "import pandas as pd\n"
        "import numpy as np\n"
        "class save_base():\n"
        "    def __init__(self):\n"
        "        self.mode_column = None\n"
        "    def fit(self, series):\n"
        "        self.mode_column = 45\n"
        "processor = save_base()"
    )

    base_level, processor_name, parsing_path = extract_base_level_from_custom_handling_code(custom_code)

    assert base_level == 45.0
    assert processor_name is None
    assert parsing_path == "legacy_mode_column"


def test_extract_base_level_from_release_105_legacy_categorical_mode_column():
    custom_code = (
        "import numpy as np\n"
        "import pandas as pd\n"
        "class rebase_mode():\n"
        "    def __init__(self):\n"
        "        self.mode_column = None\n"
        "    def fit(self, series):\n"
        "        self.mode_column = \"A\"\n"
        "processor = rebase_mode()"
    )

    base_level, processor_name, parsing_path = extract_base_level_from_custom_handling_code(custom_code)

    assert base_level == "A"
    assert processor_name is None
    assert parsing_path == "legacy_mode_column"


def test_extract_base_level_from_release_203_numeric_config_style():
    custom_code = (
        "from dataiku.base.model_plugin import prepare_for_plugin\n"
        "prepare_for_plugin('generalized-linear-models', 'generalized-linear-models_regression')\n"
        "from processors.processors import save_base\n"
        'processor = save_base({"base_level": 45})\n'
    )

    base_level, processor_name, parsing_path = extract_base_level_from_custom_handling_code(custom_code)

    assert base_level == 45
    assert processor_name == "save_base"
    assert parsing_path == "ast"


def test_extract_base_level_from_release_203_categorical_config_style():
    custom_code = (
        "from dataiku.base.model_plugin import prepare_for_plugin\n"
        "prepare_for_plugin('generalized-linear-models', 'generalized-linear-models_regression')\n"
        "from processors.processors import rebase_mode\n"
        'processor = rebase_mode({"base_level": "A"})\n'
    )

    base_level, processor_name, parsing_path = extract_base_level_from_custom_handling_code(custom_code)

    assert base_level == "A"
    assert processor_name == "rebase_mode"
    assert parsing_path == "ast"
