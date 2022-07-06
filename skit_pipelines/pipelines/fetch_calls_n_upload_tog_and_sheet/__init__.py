from typing import Optional

import kfp

from skit_pipelines.components import (
    fetch_calls_op,
    org_auth_token_op,
    read_json_key_op,
    slack_notification_op,
    tag_calls_op,
    upload2sheet_op,
)


@kfp.dsl.pipeline(
    name="Fetch calls and push to tog and sheet",
    description="fetches calls from production db with respective arguments and uploads the same set of calls to both tog (for intent, region, and transcription tagging) and a google sheet (for Call tagging and SCR analysis)",
)
def fetch_calls_n_upload_tog_and_sheet(
    client_id: int,
    org_id: str,
    job_ids: str,
    start_date: str,
    lang: str,
    end_date: str,
    ignore_callers: str,
    use_case: str,
    flow_name: str,
    min_duration: str,
    asr_provider: str,
    start_date_offset: int = 0,
    end_date_offset: int = 0,
    start_time_offset: int = 0,
    end_time_offset: int = 0,
    reported: bool = False,
    states: Optional[str] = None,
    call_quantity: int = 200,
    call_type: str = "INBOUND",
    sheet_id: str = "",
    notify: str = "",
    channel: str = "",
    slack_thread: str = "",
    on_prem: bool = False,
):
    calls = fetch_calls_op(
        client_id=client_id,
        start_date=start_date,
        end_date=end_date,
        lang=lang,
        start_date_offset=start_date_offset,
        end_date_offset=end_date_offset,
        start_time_offset=start_time_offset,
        end_time_offset=end_time_offset,
        call_quantity=call_quantity,
        call_type=call_type,
        ignore_callers=ignore_callers,
        reported=reported,
        states=states,
        use_case=use_case,
        flow_name=flow_name,
        min_duration=min_duration,
        asr_provider=asr_provider,
        on_prem=on_prem,
    )

    calls.execution_options.caching_strategy.max_cache_staleness = (
        "P0D"  # disables caching
    )

    auth_token = org_auth_token_op(org_id)
    auth_token.execution_options.caching_strategy.max_cache_staleness = (
        "P0D"  # disables caching
    )

    tag_calls_output = tag_calls_op(
        input_file=calls.output,
        job_ids=job_ids,
        token=auth_token.output,
    )

    upload = upload2sheet_op(
        calls.output,
        org_id=org_id,
        sheet_id=sheet_id,
        language_code=lang,
        flow_name=flow_name,
    )
    upload.execution_options.caching_strategy.max_cache_staleness = (
        "P0D"  # disables caching
    )

    actual_num_calls_fetched_op = read_json_key_op(
        "actual_num_calls_fetched", upload.outputs["output_json"]
    )
    actual_num_calls_fetched_op.display_name = "get-actual-num-calls-fetched"
    actual_num_calls_fetched_op.execution_options.caching_strategy.max_cache_staleness = (
        "P0D"  # disables caching
    )

    num_calls_uploaded_to_sheet_op = read_json_key_op(
        "num_calls_uploaded", upload.outputs["output_json"]
    )
    num_calls_uploaded_to_sheet_op.display_name = "get-num-calls-uploaded-to-sheet"
    num_calls_uploaded_to_sheet_op.execution_options.caching_strategy.max_cache_staleness = (
        "P0D"  # disables caching
    )

    spread_sheet_url_op = read_json_key_op(
        "spread_sheet_url", upload.outputs["output_json"]
    )
    spread_sheet_url_op.display_name = "get-spread-sheet-url"
    spread_sheet_url_op.execution_options.caching_strategy.max_cache_staleness = (
        "P0D"  # disables caching
    )

    upload_to_sheet_errors_op = read_json_key_op(
        "errors", upload.outputs["output_json"]
    )
    upload_to_sheet_errors_op.display_name = "get-upload-to-sheet-errors"
    upload_to_sheet_errors_op.execution_options.caching_strategy.max_cache_staleness = (
        "P0D"  # disables caching
    )

    with kfp.dsl.Condition(notify != "", "notify").after(
        upload_to_sheet_errors_op
    ) as check1:
        df_sizes = tag_calls_output.outputs["df_sizes"]
        errors = tag_calls_output.outputs["errors"]
        notification_text = f"""
    *Made a request for:* {call_quantity} calls
    *For the client id:* {client_id}
    *For language code:* {lang}
    *For flow name*: {flow_name}\n
    *Fetched CSV s3 url:* <{getattr(calls, 'output')}|s3 link>
    *Number of calls actually fetched:* {getattr(actual_num_calls_fetched_op, 'output')} (this is the number of unique calls present in above fetchd CSV)
    *Number of calls pushed for Call tagging:* {getattr(num_calls_uploaded_to_sheet_op, 'output')}
    *Google sheet url:* <{getattr(spread_sheet_url_op, 'output')}|link>
    *Number of user turns pushed to each of the tog job ids ({job_ids}):* {df_sizes} respectively. (these are the number of user turns present in the {getattr(actual_num_calls_fetched_op, 'output')} fetched calls)\n
    *Note:* If there are 0 calls fetched, no new worksheet will be created in your google spreadsheet. No data will be uploaded to the tog jobs as well.\n
    *Errors while uploading to tog:* {errors}
    *Errors while uploading to sheet:* {getattr(upload_to_sheet_errors_op, 'output')}
    """

        task_no_cache = slack_notification_op(
            notification_text, channel=channel, cc=notify
        )
        task_no_cache.execution_options.caching_strategy.max_cache_staleness = (
            "P0D"  # disables caching
        )


__all__ = ["fetch_calls_n_upload_tog_and_sheet"]
