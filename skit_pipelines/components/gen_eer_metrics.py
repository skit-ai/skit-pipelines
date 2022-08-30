import kfp
from kfp.components import InputPath, OutputPath

from skit_pipelines import constants as pipeline_constants


def gen_eer_metrics(
    data_path: InputPath(str),
    output_path: OutputPath(str)
):

    import pandas as pd
    from eevee.metrics import entity_report

    df = pd.read_csv(data_path)
    
    truth_df = df[["data_id", "truth_entities_with_duckling"]]
    pred_df = df[["data_id", "predicted_entities_with_modifications"]]

    truth_df.rename(columns={
        "data_id": "id",
        "truth_entities_with_duckling": "entities",
    }, inplace=True)

    pred_df.rename(columns={
        "data_id": "id",
        "predicted_entities_with_modifications": "entities",
    }, inplace=True)

    print(truth_df.columns)
    print(pred_df.columns)

    op = entity_report(truth_df, pred_df)
    
    op.to_csv(output_path)

gen_eer_metrics_op = kfp.components.create_component_from_func(
    gen_eer_metrics, base_image=pipeline_constants.BASE_IMAGE
)


# if __name__ == "__main__":

    # gen_eer_metrics("duck_4284.csv", "op.csv")
    # gen_eer_metrics("duck_4333.csv", "op.csv")

