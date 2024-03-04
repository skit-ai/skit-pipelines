import kfp

from skit_pipelines import constants as pipeline_constants
from skit_pipelines.components import (
    fetch_tagged_data_label_store_op,
    slack_notification_op,
    upload2s3_op,
)


@kfp.dsl.pipeline(
    name="Fetch annotated data from label store",
    description="A pipeline aimed at querying intent, entity, and transcriptions that happen across Skit",
)
def fetch_tagged_data_from_labelstore(
    flow_id: str,
    start_date: str = "",
    end_date: str = "",
    limit: int = 2000,
    notify: str = "",
    channel: str = "",
    slack_thread: str = "",
    data_labels: str = "",
):
    """
    A pipeline aimed at querying intent, entity, and transcriptions that happen across Skit

    .. _p_fetch_tagged_data_from_labelstore:

    Example payload to invoke via slack integrations:

        @charon run fetch_tagged_data_from_labelstore

        .. code-block:: python

            {
                "flow_id": "294",
                "limit": 20,
                "start_date": "2022-11-12",
                "end_date": "2022-11-16",
                "data_labels": "Client, Live"
            }

    :param flow_id: The id of the flow from which annotated data should be queried
    :type flow_id: str

    :param start_date: The start date range (YYYY-MM-DD) to filter tagged data. defaults to yesterday
    :type start_date: str, optional

    :param end_date: The end date range (YYYY-MM-DD) to filter tagged data, defaults to today
    :type end_date: str, optional

    :param limit: Number of annotations to fetch, defaults to 2000
    :type limit: int, optional

    :param notify: Whether to send a slack notification, defaults to ""
    :type notify: str, optional

    :param channel: The slack channel to send the notification, defaults to ""
    :type channel: str, optional

    :param slack_thread: The slack thread to send the notification, defaults to ""
    :type slack_thread: float, optional

    :param data_labels: Comma seperated data labels to filter, defaults to ""
    :type data_labels: str, optional
    """
    tagged_df = fetch_tagged_data_label_store_op(
        flow_id=flow_id,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        data_labels=data_labels,
    )

    tagged_df.execution_options.caching_strategy.max_cache_staleness = (
        "P0D"  # disables caching
    )

    s3_upload = upload2s3_op(
        path_on_disk=tagged_df.outputs["output"],
        reference=f"{flow_id}-{start_date}-{end_date}",
        file_type=f"annotations-with-call-context",
        bucket=pipeline_constants.KUBEFLOW_SANDBOX_BUCKET,
        ext=".csv",
    )

    s3_upload.execution_options.caching_strategy.max_cache_staleness = (
        "P0D"  # disables caching
    )

    notification_text = (
        f"Here is your data for {flow_id=} and date_range: {start_date=}, {end_date=}."
    )
    code_block = f"aws s3 cp {s3_upload.output} ."
    with kfp.dsl.Condition(notify != "", "notify").after(s3_upload) as check1:
        task_no_cache = slack_notification_op(
            notification_text,
            code_block=code_block,
            cc=notify,
            channel=channel,
            thread_id=slack_thread,
        )
        task_no_cache.execution_options.caching_strategy.max_cache_staleness = (
            "P0D"  # disables caching
        )


__all__ = ["fetch_tagged_data_from_labelstore"]
