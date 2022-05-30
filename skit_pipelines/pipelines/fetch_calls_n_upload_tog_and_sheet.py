import kfp

from skit_pipelines.components import (
    fetch_calls_op,
    org_auth_token_op,
    read_json_key_op,
    upload2sheet_op,
    slack_notification_op,
    tag_calls_op,
)


@kfp.dsl.pipeline(
    name="Fetch calls and push to tog and sheet",
    description="fetches calls from production db with respective arguments and uploads the same set of calls to both tog (for intent, region, and transcription tagging) and a google sheet (for CRR tagging and SCR analysis)",
)
def fetch_calls_n_upload_tog_and_sheet(
    client_id: int,
    org_id: str,
    job_ids: str,
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
    call_type: str = "INBOUND",
    sheet_id: str = "",
    notify: str = "",
    channel: str = "",
):
    from datetime import date

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

    calls.execution_options.caching_strategy.max_cache_staleness = (
        "P0D" # disables caching
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

    df_sizes = read_json_key_op("df_sizes", tag_calls_output.outputs["output_json"])
    df_sizes.display_name = "get-df-size"
    errors = read_json_key_op("errors", tag_calls_output.outputs["output_json"])
    errors.display_name = "get-any-errors"

    upload_sheets_notification_text_op: str = read_json_key_op("notification_text", upload.outputs["output_json"])
    upload_sheets_notification_text_op.display_name = "get-upload2sheet-notification-text"
    upload_sheets_notification_text_op.execution_options.caching_strategy.max_cache_staleness = (
        "P0D" # disables caching
    )

    upload_to_sheet_errors: str = read_json_key_op("errors", upload.outputs["output_json"])
    upload_to_sheet_errors.display_name = "get-upload-to-sheet-errors"
    upload_to_sheet_errors.execution_options.caching_strategy.max_cache_staleness = (
        "P0D" # disables caching
    )

    notification_text = f"""
        Finished a request for {call_quantity} calls. Fetched for date: {date.today().strftime('%d-%m-%Y')} for {client_id=}.
        Uploaded {getattr(calls, 'output')} ({getattr(df_sizes, 'output')}, {org_id=}) for tagging to {job_ids=}.\nErrors: {getattr(errors, 'output')}

        \n{getattr(upload_sheets_notification_text_op, 'output')}\nErrors while uploading to sheet: {getattr(upload_to_sheet_errors, 'output')}
    """

    with kfp.dsl.Condition(notify != "", "notify").after(errors) as check1:
        task_no_cache = slack_notification_op(notification_text, "", channel=channel, cc=notify)
        task_no_cache.execution_options.caching_strategy.max_cache_staleness = (
            "P0D"  # disables caching
        )
