import kfp

from skit_pipelines.components import (
    org_auth_token_op,
    read_json_key_op,
    slack_notification_op,
    tag_calls_op,
)


@kfp.dsl.pipeline(
    name="Tag Calls Pipeline",
    description="Uploads calls to database for tagging",
)
def run_tag_calls(org_id: str, job_ids: str, s3_path: str, notify: bool = False):
    auth_token = org_auth_token_op(org_id)
    auth_token.execution_options.caching_strategy.max_cache_staleness = (
            "P0D"  # disables caching
    )
    tag_calls_output = tag_calls_op(
        input_file=s3_path,
        job_ids=job_ids,
        token=auth_token.output,
    )
    df_sizes = read_json_key_op("df_sizes", tag_calls_output.outputs["output_json"])
    df_sizes.display_name = "get-df-size"
    errors = read_json_key_op("errors", tag_calls_output.outputs["output_json"])
    errors.display_name = "get-any-errors"

    notification_text = (
        f"Uploaded {s3_path} ({getattr(df_sizes, 'output')}, {org_id=}) for tagging to {job_ids=}.\nErrors: {getattr(errors, 'output')}"
    )
    
    with kfp.dsl.Condition(notify == True, "notify").after(errors) as check1:
        task_no_cache = slack_notification_op(notification_text, "")
        task_no_cache.execution_options.caching_strategy.max_cache_staleness = (
            "P0D"  # disables caching
        )
