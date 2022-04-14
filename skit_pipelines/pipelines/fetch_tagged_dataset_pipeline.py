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
def run_fetch_tagged_dataset(
    org_id: int,
    job_id: int,
    start_date: str,
    end_date: str,
    timezone: str = "Asia/Kolkata",
    task_type: str = "conversation",
    notify: bool = False
):
    tagged_df = fetch_tagged_dataset_op(
        job_id,
        task_type=task_type,
        timezone=timezone,
        start_date=start_date,
        end_date=end_date,
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
        task_no_cache = slack_notification_op(notification_text, s3_path=s3_upload.output)
        task_no_cache.execution_options.caching_strategy.max_cache_staleness = (
            "P0D"  # disables caching
        )
