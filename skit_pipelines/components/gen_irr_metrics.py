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

    pred_df = pd.read_csv(data_path)

    with open(os.path.join(output_path,output_file_name),"wt") as f:
        print(intent_report(pred_df["true_label_column"],pred_df["pred_label_column"]),file=f)



gen_irr_metrics_op = kfp.components.create_component_from_func(
    gen_irr_metrics, base_image=pipeline_constants.BASE_IMAGE
)
