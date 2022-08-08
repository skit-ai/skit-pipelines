import kfp
from kfp.components import InputPath, OutputPath

from skit_pipelines import constants as pipeline_constants


def gen_asr_metrics(
    data_path: InputPath(str),
    output_path: OutputPath(str),
    true_label_column: str = "transcript_y",
    pred_label_column: str = "utterances",
):

    import os

    import pandas as pd
    from eevee.metrics.asr import asr_report
    from loguru import logger
    from tabulate import tabulate

    from skit_pipelines import constants as pipeline_constants

    pred_df = pd.read_csv(data_path)

    pred_df_columns = set(pred_df)
    logger.debug(f"Columns in pred_df = {pred_df_columns}")

    # eevee.metrics.asr.asr_report expects `id` column, but skit-labels format csv contains `data_id` column.
    if (
        pipeline_constants.ID not in pred_df_columns
        and pipeline_constants.DATA_ID in pred_df_columns
    ):
        pred_df[pipeline_constants.ID] = pred_df[pipeline_constants.DATA_ID]

    logger.debug(
        f"Generating ASR report on true_label col = ({true_label_column}) and pred_label col = ({pred_label_column})"
    )

    report, breakdown, ops = asr_report(
        pred_df[[pipeline_constants.ID, true_label_column]].rename(
            columns={true_label_column: "transcription"}
        ),
        pred_df[[pipeline_constants.ID, pred_label_column]].rename(
            columns={pred_label_column: "utterances"}
        ),
        dump=True,
    )

    os.mkdir(output_path)
    with open(os.path.join(output_path, "report.txt"), "wt") as fo:
        print(report, file=fo)
    breakdown.to_csv(os.path.join(output_path, "dump.csv"))
    ops.to_csv(os.path.join(output_path, "ops.csv"))

    logger.debug(f"Generated ASR Eval report:")
    print(report)


gen_asr_metrics_op = kfp.components.create_component_from_func(
    gen_asr_metrics, base_image=pipeline_constants.BASE_IMAGE
)
