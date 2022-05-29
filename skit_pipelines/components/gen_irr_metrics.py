import kfp
from kfp.components import InputPath, OutputPath

from skit_pipelines import constants as pipeline_constants


def gen_irr_metrics(
    data_path: InputPath(str),
    output_path: OutputPath(str),
    true_label_column: str,
    pred_label_column: str,
):

    import os

    import pandas as pd
    from eevee.metrics import intent_report
    from loguru import logger

    from skit_pipelines import constants as pipeline_constants

    pred_df = pd.read_csv(data_path)

    pred_df_columns = set(pred_df)
    logger.debug(f"Columns in pred_df = {pred_df_columns}")

    # eevee.metrics.intent_report expects `id` column, but skit-labels format csv contains `data_id` column.
    if (
        pipeline_constants.ID not in pred_df_columns
        and pipeline_constants.DATA_ID in pred_df_columns
    ):
        pred_df[pipeline_constants.ID] = pred_df[pipeline_constants.DATA_ID]

    logger.debug(
        f"Generating IRR report on true_label col = ({true_label_column}) and pred_label col = ({pred_label_column})"
    )

    with open(output_path, "wt") as f:
        report = intent_report(
            pred_df[[pipeline_constants.ID, true_label_column]].rename(
                columns={true_label_column: "intent"}
            ),
            pred_df[[pipeline_constants.ID, pred_label_column]].rename(
                columns={pred_label_column: "intent"}
            ),
        )
        print(report, file=f)
        logger.debug(f"Generated IRR report:")
        logger.debug(report)


gen_irr_metrics_op = kfp.components.create_component_from_func(
    gen_irr_metrics, base_image=pipeline_constants.BASE_IMAGE
)
