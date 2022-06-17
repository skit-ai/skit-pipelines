import kfp
from kfp.components import InputPath, OutputPath

from skit_pipelines import constants as pipeline_constants


def gen_err_metrics(
    data_path: InputPath(str),
    entity_report_path: OutputPath(str),
    # fp_path: OutputPath(str),
    # fn_path: OutputPath(str),
    # mm_path: OutputPath(str),
    true_label_column: str,
    pred_label_column: str,
):

    import pandas as pd
    from eevee.metrics import entity_report
    from loguru import logger

    df = pd.read_csv(data_path)
    true_df = df[
        [
            "id",
            true_label_column,
            "tag",
            "alternatives",
            "audio_url",
            "call_uuid",
            "state",
            "reftime",
        ]
    ]
    pred_df = df[["id", pred_label_column, "prediction"]]

    true_df = true_df.rename(columns={true_label_column: "entities"})
    pred_df = pred_df.rename(columns={pred_label_column: "entities"})
    report_df: pd.DataFrame = entity_report(true_df, pred_df, dump=True)
    logger.debug(f"Generated ERR report:")

    report_df.to_csv(entity_report_path, index=False)
    print(report_df)


gen_err_metrics_op = kfp.components.create_component_from_func(
    gen_err_metrics, base_image=pipeline_constants.BASE_IMAGE
)


if __name__ == "__main__":

    gen_err_metrics(
        "amey-vodafone.csv",
        "report.csv",
        "./fp.csv",
        "./fn.csv",
        "./mm.csv",
        "true_entities",
        "pred_entities",
    )

    # gen_err_metrics(
    #     "vinay-ashley.csv",
    #     "report.csv",
    #     "./fp.csv",
    #     "./fn.csv",
    #     "./mm.csv",
    #     "true_entities",
    #     "pred_entities"
    # )
