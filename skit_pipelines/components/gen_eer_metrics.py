import kfp
from kfp.components import InputPath, OutputPath

from skit_pipelines import constants as pipeline_constants


def gen_eer_metrics(
    data_path: InputPath(str),
    output_path: OutputPath(str),
    fp_path: OutputPath(str),
    fn_path: OutputPath(str),
    mm_path: OutputPath(str),
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

    op = entity_report(truth_df, pred_df, dump=True)
    
    op.to_csv(output_path)
    pd.read_csv("./fp.csv").to_csv(fp_path, index=False)
    pd.read_csv("./fn.csv").to_csv(fn_path, index=False)
    pd.read_csv("./mm.csv").to_csv(mm_path, index=False)

gen_eer_metrics_op = kfp.components.create_component_from_func(
    gen_eer_metrics, base_image=pipeline_constants.BASE_IMAGE
)


# if __name__ == "__main__":


#     gen_eer_metrics(
#         data_path="duck_4284.csv", 
#         output_path="op.csv",
#         fp_path="fp.csv",
#         fn_path="fn.csv",
#         mm_path="mm.csv"
#         )
    # gen_eer_metrics("duck_4333.csv", "op.csv")


