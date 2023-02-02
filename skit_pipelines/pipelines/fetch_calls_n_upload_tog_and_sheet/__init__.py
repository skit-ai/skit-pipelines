from typing import Optional

import kfp

from skit_pipelines import constants as pipeline_constants
from skit_pipelines.components import (
    fetch_calls_op,
    org_auth_token_op,
    read_json_key_op,
    slack_notification_op,
    tag_calls_op,
    upload2sheet_op,
)

USE_FSM_URL = pipeline_constants.USE_FSM_URL

@kfp.dsl.pipeline(
    name="Fetch calls and push to tog and sheet",
    description="fetches calls from production db with respective arguments and uploads the same set of calls to both tog (for intent, region, and transcription tagging) and a google sheet (for Call tagging and SCR analysis)",
)
def fetch_calls_n_upload_tog_and_sheet(
    client_id: int,
    org_id: str,
    job_ids: str,
    lang: str,
    data_label: str = "",
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
    states: str = "",
    call_quantity: int = 200,
    call_type: str = "",
    sheet_id: str = "",
    notify: str = "",
    channel: str = "",
    slack_thread: str = "",
    use_fsm_url: bool = False,
):
    """
    A pipeline to sample random calls and upload for tagging. Uploads the data to TOG (Intent/Entity/Transcription tagging)
    and google sheets (call tagging and SCR tagging)

    .. _p_fetch_calls_n_upload_tog_and_sheet:

    Example payload to invoke via slack integrations:

        @charon run fetch_calls_n_upload_tog_and_sheet

        .. code-block:: python

            {
                "client_id": "1",
                "org_id":"2",
                "lang": "en",
                "call_quantity": 500,
                "job_ids": "4001,4002,4003",
                "call_type": "INBOUND",
                "sheet_id": "1juSkziNwbEZ6-ZfNGBoy32gp_PlG_fdsohgSje1e1dI",
                "data_label": "Client"
            }

    :param client_id: The client id as per api-gateway.
    :type client_id: int

    :param org_id: The organization id as per api-gateway.
    :type org_id: str

    :param job_ids: The job ids as per tog. Optional if labestudio project id is provided.
    :type job_ids: str

    :param data_label: A label to identify the source of a datapoint
    :type data_label: str, optional. Defaults to "Live"

    :param start_date: The start date range to filter calls in YYYY-MM-DD format.
    :type start_date: str

    :param lang: The language code of the calls to filter. eg: en, hi, ta, te, etc.
    :type lang: str

    :param end_date: The end date range to filter calls in YYYY-MM-DD format.
    :type end_date: str

    :param sheet_id: The sheet id of the google sheet where calls need to be uploaded for call tagging and SCR tagging
    :type sheet_id: str

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

    :param call_type: INBOUND, OUTBOUND, or CALL_TEST call filters. We can currently choose only one of these, or defaults to "INBOUND" and "OUTBOUND" both
    :type call_type: str, optional

    :param notify: Whether to send a slack notification, defaults to ""
    :type notify: str, optional

    :param channel: The slack channel to send the notification, defaults to ""
    :type channel: str, optional

    :param slack_thread: The slack thread to send the notification, defaults to ""
    :type slack_thread: float, optional

    :param use_fsm_url: Whether to use turn audio url from fsm or s3 path., defaults to False
    :type use_fsm_url: bool, optional
    """
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
        use_fsm_url=USE_FSM_URL or use_fsm_url
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
        data_label=data_label,
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
