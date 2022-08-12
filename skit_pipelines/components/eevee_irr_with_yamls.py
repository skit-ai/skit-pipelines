import kfp
from kfp.components import InputPath, OutputPath

from skit_pipelines import constants as pipeline_constants


def eevee_irr_with_yamls(
    data_path: InputPath(str),
    output_path: OutputPath(str),
    true_label_column: str = "intent_y",
    pred_label_column: str = "intent_x",
    eevee_intent_alias_yaml_s3_path: str = "",
    eevee_intent_groups_yaml_s3_path: str = "",
    eevee_intent_layers_yaml_s3_path: str = "",
):

    import re
    import traceback
    import tempfile
    import pickle
    from pprint import pprint

    import yaml
    import boto3
    import pandas as pd
    from eevee.metrics import intent_report, intent_layers_report
    from loguru import logger

    from skit_pipelines import constants as pipeline_constants

    s3_resource = boto3.client("s3")
    pattern = re.compile(r"^s3://(.+?)/(.+?)$")

    def get_yaml_from_s3_if_exists(eevee_yaml_s3_path: str):

        if not eevee_yaml_s3_path:
            return None

        try:
            logger.debug(f"{eevee_yaml_s3_path=}")
            bucket, key = pattern.match(eevee_yaml_s3_path).groups()
            logger.debug(f"{bucket=} {key=}")

            with tempfile.TemporaryFile("w") as fp:
                yaml_name = str(fp.name)
                s3_resource.download_file(bucket, key, yaml_name)
                
            with open(yaml_name, "r") as fp:
                loaded_yaml = yaml.safe_load(fp)
                
                pprint(loaded_yaml)

                return loaded_yaml
            
            
        except Exception as e:
            logger.exception(e)
            print(traceback.print_exc())

        return None


    intent_alias = get_yaml_from_s3_if_exists(eevee_intent_alias_yaml_s3_path)
    intent_groups = get_yaml_from_s3_if_exists(eevee_intent_groups_yaml_s3_path)
    intent_layers = get_yaml_from_s3_if_exists(eevee_intent_layers_yaml_s3_path)

    pred_labels = pd.read_csv(data_path)

    pred_labels_columns = set(pred_labels)
    logger.debug(f"Columns in pred_labels = {pred_labels_columns}")

    # eevee.metrics.intent_report expects `id` column, but skit-labels format csv contains `data_id` column.
    if (
        pipeline_constants.ID not in pred_labels_columns
        and pipeline_constants.DATA_ID in pred_labels_columns
    ):
        pred_labels[pipeline_constants.ID] = pred_labels[pipeline_constants.DATA_ID]

    logger.debug(
        f"Generating IRR report on true_label col = ({true_label_column}) and pred_label col = ({pred_label_column})"
    )

    true_labels = pred_labels[[pipeline_constants.ID, true_label_column]].rename(
        columns={true_label_column: "intent"}
    )

    pred_labels = pred_labels[[pipeline_constants.ID, pred_label_column]].rename(
        columns={pred_label_column: "intent"}
    )

    # report = intent_report(true_labels, pred_labels, return_output_as_dict=True)

    metrics = {}

    aliased_overall_report_dict = intent_report(
        true_labels,
        pred_labels,
        return_output_as_dict=True,
        intent_aliases=intent_alias,
    )

    metrics["overall"] = pd.DataFrame(aliased_overall_report_dict).T

    if intent_groups:
        grouped_metrics_dict = intent_report(
            true_labels,
            pred_labels,
            intent_groups=intent_groups,
            intent_aliases=intent_alias,
            breakdown=True,
        )
        metrics.update(grouped_metrics_dict)
    

    layers_dict = {}
    if intent_layers:
        layers_dict = intent_layers_report(
            true_labels,
            pred_labels,
            intent_layers=intent_layers,
            # breakdown=True,
        )
        logger.info("layers intent metrics")
        metrics["layers"] = pd.DataFrame(layers_dict)
        pprint(metrics["layers"])


    pprint(metrics)

    logger.debug("key intents collected: ")
    logger.debug(metrics.keys())

    modified_metrics = {}

    # removes "-intent", "_intents" at the end of the grouping
    # "inscop_intents" -> "inscope"
    # removes `-`, `_` before `intent`, and optional (s) in 
    # the end.
    for key, value in metrics.items():
        key = re.sub('[-_]?intent(s)?', '', key, flags=re.I)
        modified_metrics[key] = value

    logger.debug("modified key names of intents collected: ")
    logger.debug(modified_metrics.keys())
        
    
    with open(output_path, "wb") as f:
        pickle.dump(modified_metrics, f)


eevee_irr_with_yamls_op = kfp.components.create_component_from_func(
    eevee_irr_with_yamls, base_image=pipeline_constants.BASE_IMAGE
)


# if __name__ == "__main__":

#     _ = eevee_irr_with_yamls(
#         data_path="mod_4242.csv",
#         output_path="metrics.pkl",
#         true_label_column="intent_y",
#         pred_label_column="raw.intent",
#         eevee_intent_alias_yaml_s3_path="s3://vernacular-ml/irr-pipeline-resources/oppo/alias.yaml",
#         eevee_intent_groups_yaml_s3_path="s3://vernacular-ml/irr-pipeline-resources/oppo/groups.yaml",
#         eevee_intent_layers_yaml_s3_path="s3://vernacular-ml/irr-pipeline-resources/oppo/layers.yaml",
#     )

#     _ = eevee_irr_with_yamls(
#         data_path="mod_4242.csv",
#         output_path="metrics.pkl",
#         true_label_column="intent_y",
#         pred_label_column="raw.intent",
#     )