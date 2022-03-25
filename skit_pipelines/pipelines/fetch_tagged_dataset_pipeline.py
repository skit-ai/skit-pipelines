from typing import Optional

import kfp
import os
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
    job_id: str,
    task_type: str,
    timezone: str,
    start_date: str,
    end_date: str,
): 

    calls = fetch_tagged_dataset_op(
        job_id=job_id,
        task_type=task_type,
        timezone=timezone,
        start_date=start_date,
        end_date=end_date,

    )

    s3_upload = upload2s3_op(
        org_id,
        f"tagged",
        pipeline_constants.BUCKET,
        ext=".csv",
        path_on_disk=calls.output,
    )
    notification_text = f"Here is your data."
    slack_notification_op(notification_text, s3_path=s3_upload.output)
