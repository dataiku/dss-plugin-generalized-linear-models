
import dataiku
import pandas as pd
import logging

from dataiku.customrecipe import get_input_names_for_role, get_output_names_for_role, get_recipe_config
from dku_visual_ml.dku_model_retrival import VisualMLModelRetriver
from glm_handler.glm_data_handler import GlmDataHandler
from glm_handler.dku_relativites_calculator import RelativitiesCalculator
from chart_formatters.variable_level_stats import VariableLevelStatsFormatter
from dataiku.customrecipe import get_recipe_config
from dku_config import DkuConfig

logger = logging.getLogger(__name__)

dku_config = DkuConfig()

dku_config.add_param(
    name="dku_model",
    value=get_input_names_for_role('input_ML_Model')[0],
    required=True
)

dku_config.add_param(
    name="variable_level_stats_output_dataset_name",
    value=get_output_names_for_role('variable_level_stats')[0],
    required=True
)

model = dataiku.Model(dku_config.dku_model)

# -------------------------------------------------------------------------------- NOTEBOOK-CELL: CODE
full_model_id = model.get_definition()['lastExportedFrom']
model_retriever = VisualMLModelRetriver(full_model_id)
data_handler = GlmDataHandler()
relativities_calculator = RelativitiesCalculator(data_handler, model_retriever)
relativities_calculator.get_formated_predicted_base()
relativities_calculator.get_relativities_df()
variable_level_stats = VariableLevelStatsFormatter(
    model_retriever, data_handler, relativities_calculator
)
variable_stats = variable_level_stats.get_variable_level_stats()

# Write recipe outputs
dku_output_dataset = dataiku.Dataset(dku_config.variable_level_stats_output_dataset_name)
dku_output_dataset.write_with_schema(variable_stats)
