import kfp
from kfp.components import InputPath, OutputPath

from skit_pipelines import constants as pipeline_constants


def gen_irr_metrics(
    data_path: InputPath(str),
    output_path: OutputPath(str),
    true_label_column: str,
    pred_label_column: str,
    output_file_name: str = "irr_metrics.txt",
):

    import pandas as pd
    from eevee.metrics import intent_report

    from loguru import logger

    pred_df = pd.read_csv(data_path)

    logger.debug(f"Generating IRR report on true_label col = ({true_label_column}) and pred_label col = ({pred_label_column})")

    with open(os.path.join(output_path,output_file_name),"wt") as f:
        report = intent_report(pred_df["true_label_column"],pred_df["pred_label_column"])
        print(report,file=f)
        logger.debug(f"Generated IRR report:")
        logger.debug(report)



gen_irr_metrics_op = kfp.components.create_component_from_func(
    gen_irr_metrics, base_image=pipeline_constants.BASE_IMAGE
)
