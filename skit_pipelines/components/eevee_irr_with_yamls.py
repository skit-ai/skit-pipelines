import kfp
from kfp.components import InputPath, OutputPath

from skit_pipelines import constants as pipeline_constants


def eevee_irr_with_yamls(
    data_path: InputPath(str),
    output_path: OutputPath(str),
    true_label_column: str = "intent_y",
    pred_label_column: str = "intent_x",
    eevee_intent_alias_yaml_github_path: str = "",
    eevee_intent_groups_yaml_github_path: str = "",
    eevee_intent_layers_yaml_github_path: str = "",
    tog_job_id=None,
    labelstudio_project_id=None,
):

    import pickle
    import re
    import traceback
    from pprint import pprint

    import pandas as pd
    import requests
    import yaml
    from eevee.metrics import intent_layers_report, intent_report
    from loguru import logger

    from skit_pipelines import constants as pipeline_constants

    def get_yaml_from_github_if_exists(eevee_yaml_github_path: str):

        if not eevee_yaml_github_path:
            return None

        try:
            eevee_yaml_url = f"{pipeline_constants.EEVEE_RAW_FILE_GITHUB_REPO_URL}{eevee_yaml_github_path}"
            logger.debug(f"{eevee_yaml_url=}")
            headers = requests.structures.CaseInsensitiveDict()
            headers[
                "Authorization"
            ] = f"token {pipeline_constants.PERSONAL_ACCESS_TOKEN_GITHUB}"

            response = requests.get(eevee_yaml_url, headers=headers)
            logger.info(response.status_code)
            if response.status_code == requests.codes.OK:

                loaded_yaml = yaml.safe_load(response.content)

                pprint(loaded_yaml)
                return loaded_yaml

        except Exception as e:
            logger.exception(e)
            print(traceback.print_exc())

        return None

    intent_alias = get_yaml_from_github_if_exists(eevee_intent_alias_yaml_github_path)
    intent_groups = get_yaml_from_github_if_exists(eevee_intent_groups_yaml_github_path)
    intent_layers = get_yaml_from_github_if_exists(eevee_intent_layers_yaml_github_path)

    pred_labels = pd.read_csv(data_path)

    pred_labels_columns = set(pred_labels)
    logger.debug(f"Columns in pred_labels = {pred_labels_columns}")

    # eevee.metrics.intent_report expects `id` column, but skit-labels format csv contains `data_id` column.
    if (
        pipeline_constants.ID not in pred_labels_columns
        and pipeline_constants.DATA_ID in pred_labels_columns
    ):
        pred_labels[pipeline_constants.ID] = pred_labels[pipeline_constants.DATA_ID]

    true_label_column = pipeline_constants.INTENT_Y

    pred_label_column = "raw.intent"

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
        # removing eevee's in_scope grouped metrics:
        # https://github.com/skit-ai/eevee/blob/896f0e1536412669743b593dd2dc539161ebe23d/eevee/metrics/classification.py#L100
        if "in_scope" in grouped_metrics_dict:
            grouped_metrics_dict.pop("in_scope")
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
        key = re.sub("[-_]?intent(s)?", "", key, flags=re.I)
        modified_metrics[key] = value

    logger.debug("modified key names of intents collected: ")
    logger.debug(modified_metrics.keys())

    with open(output_path, "wb") as f:
        pickle.dump(modified_metrics, f)


eevee_irr_with_yamls_op = kfp.components.create_component_from_func(
    eevee_irr_with_yamls, base_image=pipeline_constants.BASE_IMAGE
)


if __name__ == "__main__":

    #     _ = eevee_irr_with_yamls(
    #         data_path="mod_4242.csv",
    #         output_path="metrics.pkl",
    #         true_label_column="intent_y",
    #         pred_label_column="raw.intent",
    #         eevee_intent_alias_yaml_github_path="intents/oppo/alias.yaml",
    #         eevee_intent_groups_yaml_github_path="intents/oppo/groups.yaml",
    #         eevee_intent_layers_yaml_github_path="intents/oppo/layers.yaml",
    #         tog_job_id=4242,
    #     )

    # _ = eevee_irr_with_yamls(
    #     data_path="mod_4242.csv",
    #     output_path="metrics.pkl",
    #     true_label_column="intent_y",
    #     pred_label_column="raw.intent",
    #     tog_job_id=4242,
    # )

    # _ = eevee_irr_with_yamls(
    #     data_path="l34.csv",
    #     output_path="metrics.pkl",
    #     true_label_column="tag",
    #     pred_label_column="intent",
    #     eevee_intent_alias_yaml_github_path="intents/indigo/alias.yaml",
    #     eevee_intent_groups_yaml_github_path="intents/indigo/groups.yaml",
    #     labelstudio_project_id=116
    # )

    # _ = eevee_irr_with_yamls(
    #     data_path="sbi.csv",
    #     output_path="metrics.pkl",
    #     true_label_column="tag",
    #     pred_label_column="intent",
    #     # eevee_intent_alias_yaml_github_path="intents/indigo/alias.yaml",
    #     # eevee_intent_groups_yaml_github_path="intents/indigo/groups.yaml",
    #     labelstudio_project_id=152,
    # )

    _ = eevee_irr_with_yamls(
        data_path="bleh.csv",
        output_path="metrics.pkl",
        true_label_column="tag",
        pred_label_column="intent",
        # eevee_intent_alias_yaml_github_path="intents/indigo/alias.yaml",
        # eevee_intent_groups_yaml_github_path="intents/indigo/groups.yaml",
        labelstudio_project_id=116,
    )