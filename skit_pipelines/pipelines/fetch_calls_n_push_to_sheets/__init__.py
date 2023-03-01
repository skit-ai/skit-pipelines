import kfp

from skit_pipelines import constants as pipeline_constants
from skit_pipelines.components import (
    fetch_calls_op,
    read_json_key_op,
    slack_notification_op,
    upload2sheet_op,
)

USE_FSM_URL = pipeline_constants.USE_FSM_URL

@kfp.dsl.pipeline(
    name="Fetch and push for calls to gogole sheets pipeline",
    description="fetches calls from production db with respective arguments and uploads calls to google sheets for Call tagging",
)
def fetch_calls_n_push_to_sheets(
    org_id: str,
    lang: str,
    client_id: str = "",
    start_date: str = "",
    end_date: str = "",
    ignore_callers: str = "",
    use_case: str = "",
    flow_name: str = "",
    min_duration: str = "",
    asr_provider: str = "",
    start_date_offset: int = 0,
    end_date_offset: int = 0,
    start_time_offset: int = 0,
    end_time_offset: int = 0,
    reported: bool = False,
    call_quantity: int = 200,
    call_type: str = "",
    sheet_id: str = "",
    notify: str = "",
    channel: str = "",
    slack_thread: str = "",
    use_fsm_url: bool = False,
):
    untagged_records_s3_path = fetch_calls_op(
        client_id=client_id,
        start_date=start_date,
        end_date=end_date,
        lang=lang,
        call_quantity=call_quantity,
        call_type=call_type,
        start_date_offset=start_date_offset,
        end_date_offset=end_date_offset,
        start_time_offset=start_time_offset,
        end_time_offset=end_time_offset,
        ignore_callers=ignore_callers,
        reported=reported,
        use_case=use_case,
        flow_name=flow_name,
        min_duration=min_duration,
        asr_provider=asr_provider,
        use_fsm_url=USE_FSM_URL or use_fsm_url,
    )

    untagged_records_s3_path.execution_options.caching_strategy.max_cache_staleness = (
        "P0D"  # disables caching
    )

    upload = upload2sheet_op(
        untagged_records_s3_path.output,
        org_id=org_id,
        sheet_id=sheet_id,
        language_code=lang,
        flow_name=flow_name,
    )

    upload.execution_options.caching_strategy.max_cache_staleness = (
        "P0D"  # disables caching
    )

    notification_text_op: str = read_json_key_op(
        "notification_text", upload.outputs["output_json"]
    )
    notification_text_op.display_name = "get-upload2sheet-notification-text"

    notification_text_op.execution_options.caching_strategy.max_cache_staleness = (
        "P0D"  # disables caching
    )

    notification_text = f"{getattr(notification_text_op, 'output')}"

    with kfp.dsl.Condition(notify != "", "notify").after(upload) as check3:
        task_no_cache = slack_notification_op(
            notification_text, channel=channel, cc=notify, thread_id=slack_thread
        )
        task_no_cache.execution_options.caching_strategy.max_cache_staleness = (
            "P0D"  # disables caching
        )


__all__ = ["run_fetch_calls_n_push_to_sheets"]
