import kfp

from skit_pipelines import constants as pipeline_constants


def slack_notification(message: str, s3_path: str, channel: str | None = None) -> None:
    """
    Send a message on any channel.
    """
    import traceback

    from loguru import logger
    from slack_sdk import WebClient
    from slack_sdk.errors import SlackApiError

    from skit_pipelines import constants as pipeline_constants
    from skit_pipelines.utils import SlackBlockFactory

    channel = channel or pipeline_constants.DEFAULT_CHANNEL

    slack_message_blocks = SlackBlockFactory()\
        .text(message)\
        .text_block(message)\
        .code_block(f"aws s3 cp {s3_path}" if s3_path else None)\
        .build()

    try:
        client = WebClient(token=pipeline_constants.SLACK_TOKEN)
        client.chat_postMessage(channel=channel, **slack_message_blocks)
    except SlackApiError as error:
        logger.error(error)
        logger.error(traceback.format_exc())


slack_notification_op = kfp.components.create_component_from_func(
    slack_notification, base_image=pipeline_constants.BASE_IMAGE
)
