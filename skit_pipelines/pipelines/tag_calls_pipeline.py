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
def run_tag_calls(org_id: int, job_id: int, s3_path: str):
    auth_token = org_auth_token_op(org_id)
    tag_calls_output = tag_calls_op(
        input_file=s3_path,
        job_id=job_id,
        token=auth_token.output,
    )
    df_size = read_json_key_op("df_size", tag_calls_output.outputs["output_json"])
    df_size.display_name = "get-df-size"
    errors = read_json_key_op("errors", tag_calls_output.outputs["output_json"])
    errors.display_name = "get-any-errors"

    notification_text = (
        f"Uploaded {s3_path} ({df_size}, {org_id=}) for tagging to {job_id=}."
    )
    with kfp.dsl.Condition(errors.output != [], "check_any_errors").after(
        errors
    ) as check1:
        notification_text += f" Errors: {errors=}"
    task_no_cache = slack_notification_op(notification_text, "").after(check1)
    task_no_cache.execution_options.caching_strategy.max_cache_staleness = (
        "P0D"  # disables caching
    )
