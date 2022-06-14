import kfp
from kfp.components import InputPath, OutputPath

from skit_pipelines import constants as pipeline_constants


def gen_confusion_matrix(
    data_path: InputPath(str),
    output_path: OutputPath(str),
    true_label_column: str = "intent",
    pred_label_column: str = "intent",
):

    import pandas as pd
    from loguru import logger
    from tabulate import tabulate

    pred_df = pd.read_csv(data_path)

    pred_df_columns = set(pred_df)
    logger.debug(f"Columns in pred_df = {pred_df_columns}")

    logger.debug(
        f"Generating confusion matrix on true_label col = ({true_label_column}) and pred_label col = ({pred_label_column})"
    )

    cm_df = pd.crosstab(pred_df[true_label_column], pred_df[pred_label_column])
    cm_df.to_csv(output_path, index=False)
    logger.debug(f"Generated confusion matrix:")
    logger.debug(tabulate(cm_df, headers="keys", tablefmt="github"))


gen_confusion_matrix_op = kfp.components.create_component_from_func(
    gen_confusion_matrix, base_image=pipeline_constants.BASE_IMAGE
)
