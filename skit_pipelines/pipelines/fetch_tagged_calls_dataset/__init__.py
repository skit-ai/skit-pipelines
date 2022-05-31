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
    job_id: int,
    start_date: str,
    end_date: str,
    timezone: str = "Asia/Kolkata",
    task_type: str = "conversation",
    notify: str = "",
):
    """
    A pipeline to fetch tagged dataset.

    .. _p_fetch_tagged_calls_dataset:

    :param org_id: reference path to save the metrics.
    :type org_id: str
    :param job_id: The annotation dataset id.
    :type job_id: int
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
    """
    tagged_df = fetch_tagged_dataset_op(
        job_id,
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
        org_id=org_id,
        file_type=f"tagged",
        bucket=pipeline_constants.BUCKET,
        ext=".csv",
    )

    notification_text = f"Here is your data for {org_id=} and {job_id=}."
    with kfp.dsl.Condition(notify == True, "notify").after(s3_upload) as check1:
        task_no_cache = slack_notification_op(
            notification_text, s3_path=s3_upload.output
        )
        task_no_cache.execution_options.caching_strategy.max_cache_staleness = (
            "P0D"  # disables caching
        )
