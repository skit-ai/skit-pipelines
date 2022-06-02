import kfp

from skit_pipelines.components import (
    fetch_calls_op,
    upload2sheet_op,
    read_json_key_op,
    slack_notification_op,
)

@kfp.dsl.pipeline(
    name="Fetch and push for calls to gogole sheets pipeline",
    description="fetches calls from production db with respective arguments and uploads calls to google sheets for Call tagging",
)
def fetch_calls_n_push_to_sheets(
    client_id: int,
    org_id: str,
    start_date: str,
    lang: str,
    end_date: str,
    ignore_callers: str,
    use_case: str,
    flow_name: str,
    min_duration: str,
    asr_provider: str,
    reported: bool = False,
    call_quantity: int = 200,
    call_type: str = "INBOUND",
    sheet_id: str = "",
    notify: str = "",
    channel: str = "",
):
    untagged_records_s3_path = fetch_calls_op(
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
    
    untagged_records_s3_path.execution_options.caching_strategy.max_cache_staleness = (
        "P0D" # disables caching
    )
    
    upload = upload2sheet_op(
        untagged_records_s3_path.output,
        org_id=org_id,
        sheet_id=sheet_id,
        language_code=lang,
        flow_name=flow_name,
    )
    
    upload.execution_options.caching_strategy.max_cache_staleness = (
        "P0D" # disables caching
    )

    notification_text_op: str = read_json_key_op("notification_text", upload.outputs["output_json"])
    notification_text_op.display_name = "get-upload2sheet-notification-text"

    notification_text_op.execution_options.caching_strategy.max_cache_staleness = (
        "P0D" # disables caching
    )

    notification_text = f"{getattr(notification_text_op, 'output')}"

    with kfp.dsl.Condition(notify != "", "notify").after(upload) as check3:
        task_no_cache = slack_notification_op(notification_text, "", channel=channel, cc=notify)
        task_no_cache.execution_options.caching_strategy.max_cache_staleness = (
            "P0D"  # disables caching
        )

__all__ = ["run_fetch_calls_n_push_to_sheets"]