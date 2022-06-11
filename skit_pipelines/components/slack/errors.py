import traceback
from functools import wraps

from loguru import logger

from skit_pipelines.components.slack.notification import slack_notification


def errors_on_slack(fn):
    @wraps(fn)
    def slack_notification(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            channel = kwargs.get("slack_config", {}).get("channel")
            cc = kwargs.get("slack_config", {}).get("notify")
            thread_id = kwargs.get("slack_config", {}).get("thread_id")

            if channel and cc:
                slack_notification(
                    str(e),
                    code_block=traceback.format_exc(),
                    channel=channel,
                    cc=cc,
                    thread_id=thread_id,
                )
            raise e
