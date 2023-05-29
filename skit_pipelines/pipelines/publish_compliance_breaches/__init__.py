from typing import Optional

import kfp

from skit_pipelines.components import (
    fetch_calls_op,
    identify_compliance_breaches_llm_op,
    push_compliance_report_to_postgres_op,
    slack_notification_op,
)


@kfp.dsl.pipeline(
    name="Check calls for compliance breaches",
    description="""Fetches sampled calls from production db and checks for potential compliance breaches (only 
        for US collections application""",
)
def publish_compliance_breaches(
    lang: str,
    template_id: Optional[str] = None,
    start_date: str = "",
    end_date: str = "",
    start_date_offset: int = 0,
    end_date_offset: int = 0,
    reported: bool = False,
    call_quantity: int = 1000,
    notify: str = "",
    channel: str = "",
    slack_thread: str = "",
):
    """
    A pipeline to sample calls in a given time range and check if there are any compliance breaches. A LLM model is
    used to identify these breaches by sending entire conversations. The results are persisted in the 'ML_metrics'
    database from where they can be queried whenever required.

    .. _publish_compliance_breaches:

    Example payload to invoke via slack integrations:

    @charon run publish_compliance_breaches

    .. code-block:: python

        {
            "lang": "en",
            "template_id": 100,
            "start_date": "2022-11-10",
            "end_date": "2022-11-11",
            "reported": false,
            "call_quantity": 500
        }

    :param lang: The language code of the calls to filter. eg: en, hi, ta, te, etc.
    :type lang: str
    :param template_id: The flow template id to filter calls, defaults to ""
    :type template_id: str, optional
    :param start_date: The start date range to filter calls in YYYY-MM-DD format.
    :type start_date: str
    :param end_date: The end date range to filter calls in YYYY-MM-DD format.
    :type end_date: str
    :param start_date_offset: Number of days from current date to start querying calls
    :type start_date_offset: int, optional
    :param end_date_offset: Number of days from current date to stop querying calls
    :type end_date_offset: int, optional
    :param reported: Pick only reported calls, defaults to False
    :type reported: bool
    :param call_quantity: Number of calls to sample, defaults to 1000
    :type call_quantity: int, optional
    :param notify: A comma separated list of slack ids: "@apples, @orange.fruit" etc, defaults to ""
    :type notify: str, optional
    :param channel: The slack channel to send the notification, defaults to ""
    :type channel: str, optional
    :param slack_thread: The slack thread to send the notification, defaults to ""
    :type slack_thread: str, optional

    """

    calls = fetch_calls_op(
        lang=lang,
        start_date=start_date,
        end_date=end_date,
        call_quantity=call_quantity,
        start_date_offset=start_date_offset,
        end_date_offset=end_date_offset,
        template_id=template_id,
        reported=reported,
        client_id="",
        remove_empty_audios=False,
    )

    compliance_breach_report = identify_compliance_breaches_llm_op(
        s3_file_path=calls.output
    )

    push_to_postgres = push_compliance_report_to_postgres_op(
        s3_file_path=compliance_breach_report.output
    )

    with kfp.dsl.Condition(notify != "", "notify").after(push_to_postgres):
        notification_text = f" Tried generating report for {call_quantity} calls. Among these {push_to_postgres.output} had compliance breaches"
        code_block = f"aws s3 cp {compliance_breach_report.output} ."

        task_no_cache = slack_notification_op(
            notification_text,
            cc=notify,
            channel=channel,
            code_block=code_block,
            thread_id=slack_thread,
        )
        task_no_cache.execution_options.caching_strategy.max_cache_staleness = (
            "P0D"  # disables caching
        )


__all__ = ["publish_compliance_breaches"]
