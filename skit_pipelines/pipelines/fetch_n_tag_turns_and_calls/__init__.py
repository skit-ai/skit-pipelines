import kfp

from skit_pipelines.components import (
    fetch_calls_for_slots_op,
    fetch_calls_op,
    org_auth_token_op,
    slack_notification_op,
    tag_calls_op,
)


@kfp.dsl.pipeline(
    name="Fetch and push for tagging turns & calls pipeline",
    description="fetches calls from production db with respective arguments and uploads turns & calls to labelstudio for tagging intent, entities, slots & call metrics.",
)
def fetch_n_tag_turns_and_calls(
    client_id: int,
    org_id: str,
    lang: str,
    data_label: str,
    start_date: str = "",
    end_date: str = "",
    job_ids: str = "",
    labelstudio_project_id: str = "",
    call_project_id: str = "",
    ignore_callers: str = "",
    use_case: str = "",
    flow_name: str = "",
    min_duration: str = "",
    asr_provider: str = "",
    states: str = "",
    reported: bool = False,
    call_quantity: int = 200,
    call_type: str = "",
    start_date_offset: int = 0,
    end_date_offset: int = 0,
    start_time_offset: int = 0,
    end_time_offset: int = 0,
    notify: str = "",
    channel: str = "",
    slack_thread: str = "",
    on_prem: bool = False,
):
    """
    A pipeline to randomly sample calls and upload for annotating turns for intents & entities and annotating calls for slots & call level metrics.

    .. _p_fetch_n_tag_turns_and_calls:

    Example payload to invoke via slack integrations:

        @charon run fetch_n_tag_turns_and_calls

        .. code-block:: python

            {
                "client_id": 41,
                "org_id": 34,
                "lang": "en",
                "start_date": "2022-11-10",
                "end_date": "2022-11-11",
                "labelstudio_project_id": 195,
                "call_project_id": 194
            }

    To use labelstudio:

        @charon run fetch_n_tag_turns_and_calls

        .. code-block:: python

            {
                "org_id": 34,
                "client_id": 41,
                "start_date": "2022-09-16",
                "end_date": "2022-09-19",
                "lang": "en",
                "reported": false,
                "call_quantity": 1000,
                "flow_name" : "indigo_domain_tuning_english"
                "labelstudio_project_id": "135",
                "call_project_id": 194
            }

    :param client_id: The client id as per api-gateway.
    :type client_id: int

    :param org_id: The organization id as per api-gateway.
    :type org_id: str

    :param job_ids: The job ids as per tog. Optional if labestudio project id is provided.
    :type job_ids: str

    :param labelstudio_project_id: The labelstudio project id for turn level tagging (intent & entities) (this is a number) since this is optional, defaults to "".
    :type labelstudio_project_id: str

    :param call_project_id: The labelstudio project id for call level tagging (slots & call metrics) (this is a number) since this is optional, defaults to "".
    :type call_project_id: str

    :param start_date: The start date range to filter calls in YYYY-MM-DD format.
    :type start_date: str

    :param lang: The language code of the calls to filter. eg: en, hi, ta, te, etc.
    :type lang: str

    :param end_date: The end date range to filter calls in YYYY-MM-DD format.
    :type end_date: str

    :param ignore_callers: Comma separated list of callers to ignore, defaults to ""
    :type ignore_callers: str, optional

    :param reported: Pick only reported calls, defaults to False
    :type reported: bool

    :param use_case: Voice bot project's use-case, defaults to ""
    :type use_case: str, optional

    :param flow_name: Identifier for a whole/part of a voicebot conversation flow, defaults to ""
    :type flow_name: str, optional

    :param min_duration: Call duration filter, defaults to ""
    :type min_duration: str, optional

    :param asr_provider: The ASR vendor (google/VASR), defaults to ""
    :type asr_provider: str, optional

    :param states: Filter calls in a comma separated list of states, defaults to ""
    :type states: str, optional

    :param start_date_offset: Offset the start date by an integer value, defaults to 0
    :type start_date_offset: int, optional

    :param end_date_offset: Offset the end date by an integer value, defaults to 0
    :type end_date_offset: int, optional

    :param start_time_offset: Offset the start time by an integer value, defaults to 0
    :type start_time_offset: int, optional

    :param end_time_offset: Offset the end time by an integer value, defaults to 0
    :type end_time_offset: int, optional

    :param call_quantity: Number of calls to sample, defaults to 200
    :type call_quantity: int, optional

    :param call_type: inbound, outbound vs subtesting call filters. We can currently choose only one of these, or defaults to "INBOUND" and "OUTBOUND" both
    :type call_type: str, optional

    :param notify: Whether to send a slack notification, defaults to ""
    :type notify: str, optional

    :param channel: The slack channel to send the notification, defaults to ""
    :type channel: str, optional

    :param slack_thread: The slack thread to send the notification, defaults to ""
    :type slack_thread: float, optional

    :param on_prem: Whether the pipeline is run on prem or not, defaults to False
    :type on_prem: bool, optional

    :param data_label: A label to identify the source of a datapoint
    :type data_label: str
    """
    calls = fetch_calls_op(
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
        states=states,
        on_prem=on_prem,
    )

    calls.execution_options.caching_strategy.max_cache_staleness = (
        "P0D"  # disables caching
    )

    auth_token = org_auth_token_op(org_id)
    auth_token.execution_options.caching_strategy.max_cache_staleness = (
        "P0D"  # disables caching
    )

    # uploads data for turn level intent, entity & transcription tagging
    tag_turns_output = tag_calls_op(
        input_file=calls.output,
        job_ids=job_ids,
        project_id=labelstudio_project_id,
        token=auth_token.output,
        org_id=org_id,
        data_label=data_label,
    )

    fetch_slot_and_calls_output = fetch_calls_for_slots_op(
        untagged_records_path=calls.output,
        org_id=org_id,
        language_code=lang,
        start_date=start_date,
        end_date=end_date,
    )

    # uploads data for call & slot level tagging to labelstudio
    tag_calls_output = tag_calls_op(
        input_file=fetch_slot_and_calls_output.output,
        job_ids="",
        project_id="",
        token=auth_token.output,
        org_id=org_id,
        call_project_id=call_project_id,
        data_label=data_label,
    )

    with kfp.dsl.Condition(notify != "", "notify").after(tag_turns_output) as check1:
        df_sizes = tag_turns_output.outputs["df_sizes"]
        errors = tag_turns_output.outputs["errors"]

        notification_text = f"""Finished a request for {call_quantity} calls. Fetched from {start_date} to {end_date} for {client_id=}.
        Uploaded {getattr(calls, 'output')} ({df_sizes}, {org_id=}) for tagging to {job_ids=} or {labelstudio_project_id=}."""
        notification_text += f"\nErrors: {errors}" if errors else ""

        task_no_cache = slack_notification_op(
            notification_text, channel=channel, cc=notify, thread_id=slack_thread
        )
        task_no_cache.execution_options.caching_strategy.max_cache_staleness = (
            "P0D"  # disables caching
        )

        df_sizes2 = tag_calls_output.outputs["df_sizes"]
        errors2 = tag_calls_output.outputs["errors"]

        notification_text = f"""Finished a request for {call_quantity} calls. Fetched from {start_date} to {end_date} for {client_id=}.
        Uploaded {getattr(fetch_slot_and_calls_output, 'output')} ({df_sizes2}, {org_id=}) for call & slot tagging to {call_project_id=}."""
        notification_text += f"\nErrors: {errors2}" if errors else ""

        task_no_cache2 = slack_notification_op(
            notification_text, channel=channel, cc=notify, thread_id=slack_thread
        )
        task_no_cache2.execution_options.caching_strategy.max_cache_staleness = (
            "P0D"  # disables caching
        )


__all__ = ["fetch_n_tag_turns_and_calls"]
