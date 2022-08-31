import kfp

from skit_pipelines import constants as pipeline_constants
from skit_pipelines.components import (
    extract_info_from_dataset_op,
    fetch_tagged_dataset_op,
    modify_entity_tog_dataset_op,
    gen_eer_metrics_op,
    push_eer_to_postgres_op,
    slack_notification_op,
    upload2s3_op,
)

BUCKET = pipeline_constants.BUCKET


@kfp.dsl.pipeline(
    name="Eval EER pipeline for tog & labelstudio tagged datasets",
    description="Produces entity metrics given a tog-job/labelstudio-project.",
)
def eer_from_tog(
    org_id: str = "",
    job_id: str = "",
    labelstudio_project_id: str = "",
    start_date: str = "",
    end_date: str = "",
    start_date_offset: int = 0,
    end_date_offset: int = 0,
    timezone: str = "Asia/Kolkata",
    mlwr: bool = False,
    slu_project_name: str = "",
    notify: str = "",
    channel: str = "",
    slack_thread: str = "",
):
    """
    Evaluates a given tog/labelstudio tagged entity dataset with production SLU predictions.
    When passed with mlwr=True, it pushes the entity metrics to entity_metrics table.

    .. _p_eer_from_tog:

    Example payload to invoke this pipeline via slack integrations:

        @charon run eer_from_tog

        .. code-block:: python

            {
                "org_id": 129,
                "job_id": "4333",
                "start_date": "2022-06-01",
                "end_date": "2022-08-01"
            }


    To push tog job entity metrics to db [RECOMMENDED]:

        @charon run eer_from_tog

        .. code-block:: python

            {
                "job_id": "4333",
                "start_date": "2022-06-01",
                "end_date": "2022-07-20",
                "mlwr": "true",
                "slu_project_name": "american_finance"
            }


    To push tog job entity metrics to db (without eevee yamls) & get the results same for slack:

        @charon run eer_from_tog

        .. code-block:: python

            {
                "org_id": 129,
                "job_id": "4333",
                "start_date": "2022-06-01",
                "end_date": "2022-07-20",
                "mlwr": "true",
                "slu_project_name": "american_finance"
            }


    To use labelstudio:

        @charon run eer_from_tog

        .. code-block:: python

            {
                "org_id": 1,
                "labelstudio_project_id": "61",
                "start_date": "2022-06-01",
                "end_date": "2022-08-01"
            }

    :param org_id: reference path to save the metrics on s3.
    :type org_id: str

    :param job_id: entity tog job IDs.
    :type job_id: str

    :param labelstudio_project_id: entity labelstudio project IDs.
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

    :param mlwr: when True, pushes the eevee entity metrics to ML Metrics DB, entity_metrics table for MLWR.
    :type use_state: bool, optional

    :param slu_project_name: name of the slu deployment which we are tracking
    :type slu_project_name: str, optional

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


    modified_df = modify_entity_tog_dataset_op(
        tagged_data_op.outputs["output"],
        timezone=timezone
    )
    modified_df.execution_options.caching_strategy.max_cache_staleness = (
        "P0D"  # disables caching
    )

    with kfp.dsl.Condition(mlwr == False, "mlwr-publish-to-slack"):

        # use eevee for comparing ground-truth tog/label studio annotated values
        # with actual production prediction values present in the same tog/label studio
        # dataset.
        eer_op = gen_eer_metrics_op(
            modified_df.outputs["output"],
        )
        eer_op.execution_options.caching_strategy.max_cache_staleness = (
            "P0D"  # disables caching
        )


        # upload tagged dataset eevee metrics.
        upload_eer = upload2s3_op(
            path_on_disk=eer_op.outputs["output"],
            reference=org_id,
            file_type="eevee_entity_metrics",
            bucket=BUCKET,
            ext=".csv",
        ).after(eer_op)
        upload_eer.execution_options.caching_strategy.max_cache_staleness = (
            "P0D"  # disables caching
        )



        upload_fp = upload2s3_op(
            path_on_disk=eer_op.outputs["fp"],
            reference=org_id,
            file_type="eevee_eer_fp",
            bucket=BUCKET,
            ext=".csv",
        ).after(eer_op)
        upload_fp.execution_options.caching_strategy.max_cache_staleness = (
            "P0D"  # disables caching
        )

        upload_fn = upload2s3_op(
            path_on_disk=eer_op.outputs["fn"],
            reference=org_id,
            file_type="eevee_eer_fn",
            bucket=BUCKET,
            ext=".csv",
        ).after(eer_op)
        upload_fn.execution_options.caching_strategy.max_cache_staleness = (
            "P0D"  # disables caching
        )


        upload_mm = upload2s3_op(
            path_on_disk=eer_op.outputs["mm"],
            reference=org_id,
            file_type="eevee_eer_mm",
            bucket=BUCKET,
            ext=".csv",
        ).after(eer_op)
        upload_mm.execution_options.caching_strategy.max_cache_staleness = (
            "P0D"  # disables caching
        )

        with kfp.dsl.Condition(notify != "", name="slack_notify").after(
            upload_eer
        ) as eer_check:
            notification_text = f"Here's the entity error report."
            code_block = f"aws s3 cp {upload_eer.output} ."
            eer_notif = slack_notification_op(
                notification_text,
                channel=channel,
                cc=notify,
                code_block=code_block,
                thread_id=slack_thread,
            )
            eer_notif.execution_options.caching_strategy.max_cache_staleness = (
                "P0D"  # disables caching
            )

            notification_text = f"Here are the false positives."
            code_block = f"aws s3 cp {upload_fp.output} ."
            eer_fp_notif = slack_notification_op(
                notification_text,
                channel=channel,
                cc=notify,
                code_block=code_block,
                thread_id=slack_thread,
            ).after(eer_notif)
            eer_fp_notif.execution_options.caching_strategy.max_cache_staleness = (
                "P0D"  # disables caching
            )

            notification_text = f"Here are the false negatives."
            code_block = f"aws s3 cp {upload_fn.output} ."
            eer_fn_notif = slack_notification_op(
                notification_text,
                channel=channel,
                cc=notify,
                code_block=code_block,
                thread_id=slack_thread,
            ).after(eer_notif)
            eer_fn_notif.execution_options.caching_strategy.max_cache_staleness = (
                "P0D"  # disables caching
            )

            notification_text = f"Here are the mismatches."
            code_block = f"aws s3 cp {upload_mm.output} ."
            eer_mm_notif = slack_notification_op(
                notification_text,
                channel=channel,
                cc=notify,
                code_block=code_block,
                thread_id=slack_thread,
            ).after(eer_notif)
            eer_mm_notif.execution_options.caching_strategy.max_cache_staleness = (
                "P0D"  # disables caching
            )



    with kfp.dsl.Condition(mlwr == True, "mlwr-publish-to-ml-metrics-db"):

        extracted_info = extract_info_from_dataset_op(
            tagged_data_op.outputs["output"],
            timezone=timezone,
        ).after(tagged_data_op)
        extracted_info.execution_options.caching_strategy.max_cache_staleness = (
            "P0D"  # disables caching
        )

        eer_op = gen_eer_metrics_op(
            modified_df.outputs["output"],
        )
        eer_op.execution_options.caching_strategy.max_cache_staleness = (
            "P0D"  # disables caching
        )

        pushed_stat = push_eer_to_postgres_op(
            eer_op.outputs["output"],
            extracted_info.outputs["output"],
            slu_project_name=slu_project_name,
            timezone=timezone,
        ).after(eer_op, extracted_info)
        pushed_stat.execution_options.caching_strategy.max_cache_staleness = (
            "P0D"  # disables caching
        )


__all__ = ["eer_from_tog"]
