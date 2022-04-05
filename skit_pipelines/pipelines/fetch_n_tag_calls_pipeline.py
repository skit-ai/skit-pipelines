import kfp

from skit_pipelines import constants as pipeline_constants
from skit_pipelines.components import (
    fetch_calls_op,
    slack_notification_op,
    upload2s3_op,
    org_auth_token_op,
    tag_calls_op,
)


@kfp.dsl.pipeline(
    name="Fetch and push for tagging calls pipeline",
    description="fetches calls from production db with respective arguments and uploads calls to database for tagging",
)
def run_fetch_n_tag_calls(
    client_id: int,
    org_id: int,
    job_id: int,
    start_date: str,
    lang: str,
    end_date: str,
    ignore_callers: str,
    reported: str,
    use_case: str,
    flow_name: str,
    min_duration: str,
    asr_provider: str,
    call_quantity: int = 200,
    call_type: str = "inbound",
):
    calls = fetch_calls_op(
        client_id=client_id,
        start_date=start_date,
        end_date=end_date,
        lang=lang,
        call_quantity=call_quantity,
        call_type=call_type,
        ignore_callers=ignore_callers,
        reported=reported,
        use_case=use_case,
        flow_name=flow_name,
        min_duration=min_duration,
        asr_provider=asr_provider,
    )
    s3_upload = upload2s3_op(
        calls.outputs["output_string"],
        org_id=client_id,
        file_type=f"{lang}-untagged",
        bucket=pipeline_constants.BUCKET,
        ext=".csv",
    )
    s3_upload.execution_options.caching_strategy.max_cache_staleness = (
        "P0D"  # disables caching
    )
    
    auth_token = org_auth_token_op(org_id)
    tag_calls_output = tag_calls_op(
        input_file=s3_upload.output,
        job_id=job_id,
        token=auth_token.output,
    )
    df_size, errors = tag_calls_output.outputs
    
    notification_text = (
        f"""Finished a request for {call_quantity} calls. Fetched from {start_date} to {end_date} for {client_id=}.
        Uploaded {s3_upload} ({df_size}, {org_id=}) for tagging to {job_id=}."""
    )
    print(tag_calls_output.output)
    with kfp.dsl.Condition(tag_calls_output.output):
        notification_text += f" Errors: {errors=}"
        
    task_no_cache = slack_notification_op(notification_text, "").after(tag_calls_output)
    task_no_cache.execution_options.caching_strategy.max_cache_staleness = (
        "P0D"  # disables caching
    )
