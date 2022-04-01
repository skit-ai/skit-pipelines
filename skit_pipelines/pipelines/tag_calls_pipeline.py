import kfp

from skit_pipelines import constants as pipeline_constants
from skit_pipelines.components import (
    org_auth_token_op,
    tag_calls_op,
    slack_notification_op
)


@kfp.dsl.pipeline(
    name="Tag Calls Pipeline",
    description="Uploads calls to database for tagging",
)
def run_tag_calls(org_id: int, job_id: int, s3_path: str):
    auth_token = org_auth_token_op(org_id)
    tag_calls_output = tag_calls_op(
        input_file=s3_path,
        job_id=job_id,
        token=auth_token.output,
    )
    df_size, errors = tag_calls_output.outputs
    notification_text = f"Uploaded {s3_path} ({df_size}, {org_id=}) for tagging to {job_id=}."
    if errors:
        notification_text += f" Errors: {errors=}"
    task_no_cache = slack_notification_op(notification_text, '')
    task_no_cache.execution_options.caching_strategy.max_cache_staleness = (
        "P0D"  # disables caching
    )
