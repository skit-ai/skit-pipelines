import kfp

from skit_pipelines.components import fetch_calls_op, slack_notification_op


@kfp.dsl.pipeline(
    name="Fetch Calls Pipeline",
    description="fetches calls from production db with respective arguments",
)
def run_fetch_calls(
    client_id: int,
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
    notify: bool = False,
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

    with kfp.dsl.Condition(notify == True, "notify").after(
        calls
    ) as check1:
        notification_text = f"Finished a request for {call_quantity} calls. Fetched from {start_date} to {end_date} for {client_id=}."
        task_no_cache = slack_notification_op(notification_text, s3_path=calls.output)
        task_no_cache.execution_options.caching_strategy.max_cache_staleness = (
            "P0D"  # disables caching
        )
