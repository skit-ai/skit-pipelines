import kfp

from skit_pipelines import constants as pipeline_constants
from skit_pipelines.components import (
    create_true_intent_labels_op,
    eevee_irr_with_yamls_op,
    extract_info_from_dataset_op,
    fetch_tagged_dataset_op,
    gen_confusion_matrix_op,
    gen_irr_metrics_op,
    push_irr_to_postgres_op,
    slack_notification_op,
    upload2s3_op,
)

INTENT_Y = pipeline_constants.INTENT_Y
BUCKET = pipeline_constants.BUCKET


@kfp.dsl.pipeline(
    name="Eval IRR pipeline for tog & labelstudio tagged datasets",
    description="Produces intent metrics given a tog-job/labelstudio-project.",
)
def irr_from_tog(
    org_id: str = "",
    job_id: str = "",
    labelstudio_project_id: str = "",
    start_date: str = "",
    end_date: str = "",
    start_date_offset: int = 0,
    end_date_offset: int = 0,
    timezone: str = "Asia/Kolkata",
    true_label_column: str = "intent_y",
    pred_label_column: str = "raw.intent",
    mlwr: bool = False,
    slu_project_name: str = "",
    eevee_intent_alias_yaml_github_path: str = "",
    eevee_intent_groups_yaml_github_path: str = "",
    eevee_intent_layers_yaml_github_path: str = "",
    notify: str = "",
    channel: str = "",
    slack_thread: str = "",
):
    """
    Evaluates a given tog/labelstudio tagged intent dataset with production SLU predictions.
    When passed with mlwr=True, it pushes the intent metrics to intent_metrics table.

    .. _p_irr_from_tog:

    Example payload to invoke this pipeline via slack integrations:

        @charon run irr_from_tog

        .. code-block:: python

            {
                "org_id": 1,
                "job_id": "4011",
                "start_date": "2022-06-01",
                "end_date": "2022-08-01"
            }


    To push tog job intent metrics to db, when using full eevee facilities like gropuing, aliasing, layers etc [RECOMMENDED]:

        @charon run irr_from_tog

        .. code-block:: python

            {
                "job_id": "4242",
                "start_date": "2022-06-01",
                "end_date": "2022-07-20",
                "mlwr": "true",
                "slu_project_name": "oppo",
                "eevee_intent_alias_yaml_github_path": "intents/oppo/alias.yaml",
                "eevee_intent_groups_yaml_github_path": "intents/oppo/groups.yaml",
                "eevee_intent_layers_yaml_github_path": "intents/oppo/layers.yaml"
            }


    To push tog job intent metrics to db (without eevee yamls) & get the results same for slack:

        @charon run irr_from_tog

        .. code-block:: python

            {
                "org_id": 34,
                "job_id": "3091",
                "start_date": "2022-06-01",
                "end_date": "2022-07-20",
                "mlwr": "true",
                "slu_project_name": "indigo"
            }


    To use labelstudio:

        @charon run irr_from_tog

        .. code-block:: python

            {
                "org_id": 1,
                "labelstudio_project_id": "61",
                "start_date": "2022-06-01",
                "end_date": "2022-08-01"
            }

    :param org_id: reference path to save the metrics on s3.
    :type org_id: str

    :param job_id: intent tog job IDs.
    :type job_id: str

    :param labelstudio_project_id: intent labelstudio project IDs.
    :type labelstudio_project_id: str

    :param start_date: The start date range to filter calls in YYYY-MM-DD format.
    :type start_date: str

    :param end_date: The end date range to filter calls in YYYY-MM-DD format.
    :type end_date: str

    :param start_date_offset: Offset the start date by an integer value, defaults to 0
    :type start_date_offset: int, optional

    :param end_date_offset: Offset the end date by an integer value, defaults to 0
    :type end_date_offset: int, optional

    :param timezone: The timezone to apply for multi-region datasets, defaults to "Asia/Kolkata"
    :type timezone: str, optional

    :param true_label_column: Column name of ground-truth which will be used for eevee intent evaluation.
    :type true_label_column: str, optional

    :param pred_label_column: Column name of SLU production predictions which will be used for eevee intent evaluation.
    :type pred_label_column: str, optional

    :param mlwr: when True, pushes the eevee intent metrics to ML Metrics DB, intent_metrics table for MLWR.
    :type use_state: bool, optional

    :param slu_project_name: name of the slu deployment which we are tracking
    :type slu_project_name: str, optional

    :param eevee_intent_alias_yaml_github_path: eevee's intent_report alias.yaml, refer docs `here <https://skit-ai.github.io/eevee/metrics/intents.html#aliasing>`_ . Upload your yaml to eevee-yamls repository `here <https://github.com/skit-ai/eevee-yamls>`_ & pass the relative path of the yaml from base of the repository.
    :type eevee_intent_alias_yaml_github_path: str, optional

    :param eevee_intent_groups_yaml_github_path: eevee's intent_report groups.yaml, refer docs `here <https://skit-ai.github.io/eevee/metrics/intents.html#grouping>`_ . Upload your yaml to eevee-yamls repository `here: <https://github.com/skit-ai/eevee-yamls>`_ & pass the relative path of the yaml from base of the repository.
    :type eevee_intent_groups_yaml_github_path: str, optional

    :param eevee_intent_layers_yaml_github_path: eevee's intent_layers_report layers.yaml, refer docs `here <https://skit-ai.github.io/eevee/metrics/intents.html#layers-of-an-intent>`_ . Upload your yaml to eevee-yamls repository `here <https://github.com/skit-ai/eevee-yamls>`_ & pass the relative path of the yaml from base of the repository.
    :type eevee_intent_layers_yaml_github_path: str, optional

    :param notify: A comma separated list of slack ids: "@apples, @orange.fruit" etc, defaults to ""
    :type notify: str, optional

    :param channel: The slack channel to send the notification, defaults to ""
    :type channel: str, optional

    :param slack_thread: The slack thread to send the notification, defaults to ""
    :type slack_thread: str, optional
    """

    # gets the tog job / labelstudio dataset
    tagged_data_op = fetch_tagged_dataset_op(
        job_id=job_id,
        project_id=labelstudio_project_id,
        timezone=timezone,
        start_date=start_date,
        end_date=end_date,
        start_date_offset=start_date_offset,
        end_date_offset=end_date_offset,
    )

    tagged_data_op.execution_options.caching_strategy.max_cache_staleness = (
        "P0D"  # disables caching
    )

    # Create true label column
    preprocess_data_op = create_true_intent_labels_op(
        tagged_data_op.outputs["output"]
    ).after(tagged_data_op)

    with kfp.dsl.Condition(mlwr == False, "mlwr-publish-to-slack"):

        # use eevee for comparing ground-truth tog/label studio annotated values
        # with actual production prediction values present in the same tog/label studio
        # dataset.
        irr_op = gen_irr_metrics_op(
            preprocess_data_op.outputs["output"],
            true_label_column=true_label_column,
            pred_label_column=pred_label_column,
        )

        # confusion matrix on the same ground-truth tog/labelstudio dataset
        # vs SLU production predictions
        confusion_matrix_op = gen_confusion_matrix_op(
            preprocess_data_op.outputs["output"],
            true_label_column=true_label_column,
            pred_label_column=pred_label_column,
        )

        # upload tagged dataset eevee metrics.
        upload_irr = upload2s3_op(
            path_on_disk=irr_op.outputs["output"],
            reference=org_id,
            file_type="xlmr-irr-metrics",
            bucket=BUCKET,
            ext=".csv",
        ).after(irr_op)
        upload_irr.execution_options.caching_strategy.max_cache_staleness = (
            "P0D"  # disables caching
        )

        # upload confusion matrix.
        upload_cm = upload2s3_op(
            path_on_disk=confusion_matrix_op.outputs["output"],
            reference=org_id,
            file_type="xlmr-confusion-matrix",
            bucket=BUCKET,
            ext=".csv",
        ).after(confusion_matrix_op)
        upload_cm.execution_options.caching_strategy.max_cache_staleness = (
            "P0D"  # disables caching
        )

        with kfp.dsl.Condition(notify != "", name="slack_notify").after(
            upload_irr
        ) as irr_check:
            notification_text = f"Here's the IRR report."
            code_block = f"aws s3 cp {upload_irr.output} ."
            irr_notif = slack_notification_op(
                notification_text,
                channel=channel,
                cc=notify,
                code_block=code_block,
                thread_id=slack_thread,
            )
            irr_notif.execution_options.caching_strategy.max_cache_staleness = (
                "P0D"  # disables caching
            )

        with kfp.dsl.Condition(notify != "", name="slack_notify").after(
            upload_cm
        ) as cm_check:
            notification_text = f"Here's the confusion matrix."
            code_block = f"aws s3 cp {upload_cm.output} ."
            cm_notif = slack_notification_op(
                notification_text,
                channel=channel,
                cc=notify,
                code_block=code_block,
                thread_id=slack_thread,
            )
            cm_notif.execution_options.caching_strategy.max_cache_staleness = (
                "P0D"  # disables caching
            )

    with kfp.dsl.Condition(mlwr == True, "mlwr-publish-to-ml-metrics-db"):

        extracted_info = extract_info_from_dataset_op(
            tagged_data_op.outputs["output"],
            timezone=timezone,
            tog_job_id=job_id,
            labelstudio_project_id=labelstudio_project_id,
        ).after(tagged_data_op)
        extracted_info.execution_options.caching_strategy.max_cache_staleness = (
            "P0D"  # disables caching
        )

        yamls_irr_op = eevee_irr_with_yamls_op(
            preprocess_data_op.outputs["output"],
            true_label_column=true_label_column,
            pred_label_column=pred_label_column,
            eevee_intent_alias_yaml_github_path=eevee_intent_alias_yaml_github_path,
            eevee_intent_groups_yaml_github_path=eevee_intent_groups_yaml_github_path,
            eevee_intent_layers_yaml_github_path=eevee_intent_layers_yaml_github_path,
            tog_job_id=job_id,
            labelstudio_project_id=labelstudio_project_id
        ).after(preprocess_data_op)

        pushed_stat = push_irr_to_postgres_op(
            yamls_irr_op.outputs["output"],
            extracted_info.outputs["output"],
            slu_project_name=slu_project_name,
            timezone=timezone,
        ).after(yamls_irr_op, extracted_info)
        pushed_stat.execution_options.caching_strategy.max_cache_staleness = (
            "P0D"  # disables caching
        )


__all__ = ["irr_from_tog"]
