import kfp
from kfp.components import InputPath

from skit_pipelines import constants as pipeline_constants


def slack_notification(message: str, file_path: str, channel: str | None = None) -> None:
    """
    Send a message on any channel.
    """
    import traceback

    from loguru import logger
    from slack_sdk import WebClient
    from slack_sdk.errors import SlackApiError

    from skit_pipelines import constants as pipeline_constants

    if channel is None:
        channel = pipeline_constants.SLACK_CHANNEL

    try:
        client = WebClient(token=pipeline_constants.SLACK_TOKEN)
        client.chat_postMessage(channel=channel, text=message)
    except SlackApiError as error:
        logger.error(error)
        logger.error(traceback.format_exc())


slack_notification_op = kfp.components.create_component_from_func(
    slack_notification, base_image=pipeline_constants.BASE_IMAGE
)
