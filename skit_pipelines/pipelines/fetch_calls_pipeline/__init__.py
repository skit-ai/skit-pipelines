import kfp

from skit_pipelines import constants as pipeline_constants
from skit_pipelines.components import fetch_calls_op, slack_notification_op

USE_FSM_URL = pipeline_constants.USE_FSM_URL
REMOVE_EMPTY_AUDIOS = False if USE_FSM_URL else True


@kfp.dsl.pipeline(
    name="Fetch Calls Pipeline",
    description="fetches calls from production db with respective arguments",
)
def fetch_calls_pipeline(
    lang: str,
    start_date: str = "",
    end_date: str = "",
    client_id: str = "",
    ignore_callers: str = "",
    reported: bool = False,
    template_id: str = "",
    use_case: str = "",
    flow_name: str = "",
    min_duration: str = "",
    asr_provider: str = "",
    states: str = "",
    intents: str = "",
    call_quantity: int = 200,
    call_type: str = "",
    remove_empty_audios: bool = REMOVE_EMPTY_AUDIOS,
    notify: str = "",
    channel: str = "",
    slack_thread: str = "",
    use_fsm_url: bool = False,
    flow_ids: str = "",
):
    """
    A pipeline to randomly sample calls for a given voice-bot project.

    .. _p_fetch_calls_pipeline:


    Example payload to invoke this pipeline via slack integrations:

        @charon run fetch_calls_pipeline

        .. code-block:: python

            {
                "client_id": 1,
                "start_date": "2020-01-01",
                "lang": "en",
                "end_date": "2020-01-01",
                "reported": false,
                "call_quantity": 200
            }

    :param client_id: The comma separated client ids as per fsm db.
    :type client_id: str, optional
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
    :param template_id: The flow template id to filter calls, defaults to ""
    :type template_id: str, optional
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
    :param intents: Filter turns in sampled calls from a comma separated list of intents, defaults to ""
    :type intents: str, optional
    :param call_quantity: Number of calls to sample, defaults to 200
    :type call_quantity: int, optional
    :param call_type: inbound, outbound vs subtesting call filters. We can currently choose only one of these, or defaults to "INBOUND" and "OUTBOUND" both
    :type call_type: str, optional
    :param remove_empty_audios: to remove calls with call audios being empty/broken, defaults to True
    :type remove_empty_audios: bool
    :param notify: A comma separated list of slack ids: "@apples, @orange.fruit" etc, defaults to ""
    :type notify: str, optional
    :param channel: The slack channel to send the notification, defaults to ""
    :type channel: str, optional
    :param slack_thread: The slack thread to send the notification, defaults to ""
    :type slack_thread: str, optional
    :param use_fsm_url: Whether to use turn audio url from fsm or s3 path., defaults to False
    :type use_fsm_url: bool, optional
    :param flow_id: Id for a whole/part of a voicebot conversation flow, defaults to ""
    :type flow_id: str, optional
    """
    
    calls = fetch_calls_op(
        client_id=client_id,
        start_date=start_date,
        end_date=end_date,
        lang=lang,
        call_quantity=call_quantity,
        call_type=call_type,
        ignore_callers=ignore_callers,
        reported=reported,
        template_id=template_id,
        use_case=use_case,
        flow_name=flow_name,
        min_duration=min_duration,
        asr_provider=asr_provider,
        intents=intents,
        states=states,
        remove_empty_audios=remove_empty_audios,
        use_fsm_url=USE_FSM_URL or use_fsm_url,
        flow_ids=flow_ids
    )
    calls.execution_options.caching_strategy.max_cache_staleness = (
        "P0D"  # disables caching
    )

    with kfp.dsl.Condition(notify != "", "notify").after(calls) as check1:
        notification_text = f"Finished a request for {call_quantity} calls. Fetched from {start_date} to {end_date} for {client_id=}."
        code_block = f"aws s3 cp {calls.output} ."
        task_no_cache = slack_notification_op(
            notification_text,
            channel=channel,
            cc=notify,
            code_block=code_block,
            thread_id=slack_thread,
        )
        task_no_cache.execution_options.caching_strategy.max_cache_staleness = (
            "P0D"  # disables caching
        )


__all__ = ["fetch_calls_pipeline"]
