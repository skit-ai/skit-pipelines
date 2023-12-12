import os
import kfp
from kfp.components import InputPath, OutputPath
from skit_pipelines import constants as pipeline_constants


def zip_file_and_notify(
    path_on_disk: InputPath(str), 
    message: str,
    channel: str = "",
    thread_id: str = "",
    file_title: str = "",
    file_name: str = ""
    ):
    """
    Zip a file or folder and upload the same on slack
    :param message: the slack message to be sent
    :param channel: the channel in which the message is to be sent
    :param thread_id: the thread to which the message must be added
    :param file_title: Title for the file
    :param file_name: name of the file
    """
    import os
    
    from loguru import logger
    from slack_sdk import WebClient
    from slack_sdk.errors import SlackApiError

    from skit_pipelines import constants as pipeline_constants

    import tempfile
    
    import zipfile
    _, zip_path = tempfile.mkstemp(suffix=".zip")
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        if os.path.isfile(path_on_disk):
            zipf.write(path_on_disk, os.path.basename(path_on_disk))
        elif os.path.isdir(path_on_disk):
            for root, _, files in os.walk(path_on_disk):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, path_on_disk)
                    zipf.write(file_path, arcname=arcname)
        else:
            raise ValueError(f"Invalid input path: {path_on_disk}")
        
    channel = channel or pipeline_constants.DEFAULT_CHANNEL
    
    try:
        client = WebClient(token=pipeline_constants.SLACK_TOKEN)
        client.files_upload(
        channels=channel,
        file=zip_path,
        filename=file_name,
        initial_comment=message,
        title=file_title,
        thread_ts=thread_id or None,
        filetype = 'zip'
        )
        
    except SlackApiError as error:
        logger.error(error)
        
zip_file_and_notify_op = kfp.components.create_component_from_func(
    zip_file_and_notify, base_image=pipeline_constants.BASE_IMAGE
)