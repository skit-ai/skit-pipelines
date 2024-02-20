from typing import Optional

import kfp

from skit_pipelines.components import (
    invalidate_situations_in_db_op,
    slack_notification_op
)


@kfp.dsl.pipeline(
    name="Invalidate situations",
    description="""Sets conversations as invalid, thereby preventing it from being used for training""",
)
def invalidate_llm_situations_in_db(
    situation_id_list: str = "",
    notify: str = "",
    channel: str = "",
    slack_thread: str = "",
):
    """
    A pipeline to discard situations by setting flag is_valid to False for situations that are no longer needed

    .. invalidate_llm_situations_in_db:

    Example payload to invoke via slack integrations:

    @charon run invalidate_llm_situations_in_db

    .. code-block:: python

        {
            "situation_id_list": "1, 3, 5"
        }
    
    :param situation_id_list: A comma separated list of situation ids from the situation_scenario_mapper table: "1, 2" etc, defaults to ""
    :type situation_id_list: str 
    :param notify: A comma separated list of slack ids: "@apples, @orange.fruit" etc, defaults to ""
    :type notify: str, optional
    :param channel: The slack channel to send the notification, defaults to ""
    :type channel: str, optional
    :param slack_thread: The slack thread to send the notification, defaults to ""
    :type slack_thread: str, optional

    """

    update_situation_validity = invalidate_situations_in_db_op(
        situation_id=situation_id_list
    )

    with kfp.dsl.Condition(notify != "", "notify").after(update_situation_validity):
        notification_text = f"is_valid has been set to False for the situations : {situation_id_list}"

        task_no_cache = slack_notification_op(
            notification_text,
            cc=notify,
            channel=channel,
            thread_id=slack_thread,
        )
        task_no_cache.execution_options.caching_strategy.max_cache_staleness = (
            "P0D"  # disables caching
        )


__all__ = ["invalidate_llm_situations_in_db"]
