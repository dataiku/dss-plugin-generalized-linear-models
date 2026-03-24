import ast
import re
from typing import Any, Dict, Optional, Sequence, Tuple


def extract_processor_config_from_custom_code(
    custom_handling_code: str,
    processor_names: Sequence[str],
) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
    if not isinstance(custom_handling_code, str) or not custom_handling_code.strip():
        return None, None

    try:
        parsed = ast.parse(custom_handling_code)
    except SyntaxError:
        return None, None

    processor_names_set = set(processor_names)
    for node in ast.walk(parsed):
        if not isinstance(node, ast.Assign):
            continue
        value = node.value
        if not isinstance(value, ast.Call):
            continue
        if not isinstance(value.func, ast.Name):
            continue
        if value.func.id not in processor_names_set:
            continue
        if not value.args:
            continue
        try:
            config_dict = ast.literal_eval(value.args[0])
        except (ValueError, SyntaxError):
            continue
        if isinstance(config_dict, dict):
            return value.func.id, config_dict

    return None, None


def extract_base_level_from_custom_handling_code(
    custom_handling_code: str,
) -> Tuple[Optional[Any], Optional[str], str]:
    processor_name, config_dict = extract_processor_config_from_custom_code(
        custom_handling_code,
        ("continuous_spline", "save_base", "rebase_mode"),
    )
    if isinstance(config_dict, dict) and "base_level" in config_dict:
        return config_dict.get("base_level"), processor_name, "ast"

    if not isinstance(custom_handling_code, str):
        return None, processor_name, "none"

    # Backward-compatible fallback for malformed snippets.
    # Supports both quote styles, numeric values and None literals.
    regex = re.compile(r"""['"]base_level['"]\s*:\s*([^,\}\n]+)""")
    match = regex.search(custom_handling_code)
    if match:
        value_token = match.group(1).strip()
        try:
            return ast.literal_eval(value_token), processor_name, "regex_fallback"
        except (ValueError, SyntaxError):
            normalized = value_token.strip().strip("'").strip('"')
            if normalized:
                return normalized, processor_name, "regex_fallback"

    # Legacy release/1.0.5 fallback where webapp-trained models stored:
    # self.mode_column = 45
    # self.mode_column = "A"
    legacy_match = re.search(
        r"""self\.mode_column\s*=\s*(?:"([^"]+)"|'([^']+)'|([+-]?\d+(?:\.\d+)?))""",
        custom_handling_code,
    )
    if not legacy_match:
        return None, processor_name, "none"

    if legacy_match.group(1) is not None:
        return legacy_match.group(1), processor_name, "legacy_mode_column"
    if legacy_match.group(2) is not None:
        return legacy_match.group(2), processor_name, "legacy_mode_column"
    if legacy_match.group(3) is not None:
        try:
            return float(legacy_match.group(3)), processor_name, "legacy_mode_column"
        except ValueError:
            return None, processor_name, "legacy_mode_column"

    return None, processor_name, "none"
