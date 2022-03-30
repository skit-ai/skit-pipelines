from typing import Optional

import kfp

from skit_pipelines import constants as pipeline_constants
from skit_pipelines.components import (
    fetch_calls_op,
    slack_notification_op,
    upload2s3_op,
)


@kfp.dsl.pipeline(
    name="Fetch Calls Pipeline",
    description="fetches calls from production db with respective arguments",
)
def run_fetch_calls(
    org_id: int,
    start_date: str,
    lang: str,
    end_date: str,
    call_quantity: int,
    call_type: str,
    ignore_callers: str,
    reported: str,
    use_case: str,
    flow_name: str,
    min_duration: str,
    asr_provider: str,
):
    calls = fetch_calls_op(
        org_id=org_id,
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
        org_id=org_id,
        file_type=f"{lang}-untagged",
        bucket=pipeline_constants.BUCKET,
        ext=".csv",
    )
    s3_upload.execution_options.caching_strategy.max_cache_staleness = (
        "P0D"  # disables caching
    )
    notification_text = f"Finished a request for {call_quantity} calls. Fetched from {start_date} to {end_date} for {org_id=}."
    task_no_cache = slack_notification_op(notification_text, s3_path=s3_upload.output)
    task_no_cache.execution_options.caching_strategy.max_cache_staleness = (
        "P0D"  # disables caching
    )
