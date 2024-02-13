import tempfile

import kfp

from skit_pipelines import constants as pipeline_constants
from skit_pipelines.components import (
    fetch_tagged_dataset_op,
    slack_notification_op,
    upload2s3_op,
)


@kfp.dsl.pipeline(
    name="Fetch Tagged Dataset Pipeline",
    description="fetches tagged dataset from tog with respective arguments",
)
def fetch_tagged_calls_dataset(
    org_id: str,
    job_id: str = "",
    labelstudio_project_id: str = "",
    start_date: str = "",
    end_date: str = "",
    timezone: str = "Asia/Kolkata",
    task_type: str = "conversation",
    notify: str = "",
    channel: str = "",
    slack_thread: str = "",
):
    """
    A pipeline to fetch tagged dataset.

    .. _p_fetch_tagged_calls_dataset:

    Example payload to invoke via slack integrations:

        @charon run fetch_tagged_calls_dataset

        .. code-block:: python

            {
                "org_id": 1,
                "job_id": "4011",
                "start_date": "2020-01-01",
                "end_date": "2020-01-01"
            }

    To use labelstudio:

        @charon run fetch_tagged_calls_dataset

        .. code-block:: python

            {
                "org_id": 1,
                "labelstudio_project_id": "40",
                "start_date": "2020-01-01",
                "end_date": "2020-01-01"
            }

    :param org_id: reference path to save the metrics.
    :type org_id: str
    :param job_ids: The job ids as per tog. Optional if labestudio project id is provided.
    :type job_id: str
    :param labelstudio_project_id: The labelstudio project id (this is a number) since this is optional, defaults to "".
    :type labelstudio_project_id: str
    :param start_date: The start date range (YYYY-MM-DD) to filter tagged data.
    :type start_date: str
    :param end_date: The end date range (YYYY-MM-DD) to filter tagged data
    :type end_date: str
    :param timezone: The timezone to apply for multi-region datasets, defaults to "Asia/Kolkata"
    :type timezone: str, optional
    :param task_type: https://github.com/skit-ai/skit-labels#task-types, defaults to "conversation"
    :type task_type: str, optional
    :param notify: A comma separated list of slack ids: "@apples, @orange.fruit" etc, defaults to ""
    :type notify: str, optional
    :param channel: The slack channel to send the notification, defaults to ""
    :type channel: str, optional
    :param slack_thread: The slack thread to send the notification, defaults to ""
    :type slack_thread: str, optional
    """
    tagged_df = fetch_tagged_dataset_op(
        job_id=job_id,
        project_id=labelstudio_project_id,
        task_type=task_type,
        timezone=timezone,
        start_date=start_date,
        end_date=end_date,
    )
    tagged_df.execution_options.caching_strategy.max_cache_staleness = (
        "P0D"  # disables caching
    )
    s3_upload = upload2s3_op(
        path_on_disk=tagged_df.outputs["output"],
        reference=f"datasets/{org_id}_{job_id}",
        file_type=f"tagged",
        bucket=pipeline_constants.KUBEFLOW_SANDBOX_BUCKET,
        ext=".csv",
    )

    notification_text = f"Here is your data for {org_id=} and {job_id=}."
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


__all__ = ["fetch_tagged_calls_dataset"]
