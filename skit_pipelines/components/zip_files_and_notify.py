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
    file_name: str = "",
    notify: str = "",
    display_sample: bool = False
    ):
    """
    Zip a file or folder and upload the same on slack
    :param message: the slack message to be sent
    :param channel: the channel in which the message is to be sent
    :param thread_id: the thread to which the message must be added
    :param file_title: Title for the file
    :param file_name: name of the file
    :param notify: Whether to send a slack notification
    :param display_sample: Set it as true to display the value in the file
    """
    import os
    
    from loguru import logger
    from slack_sdk import WebClient
    from slack_sdk.errors import SlackApiError

    from skit_pipelines import constants as pipeline_constants

    import tempfile
    
    import zipfile
    
    import os
    import random
    from skit_pipelines.components.notification import slack_notification
    
    def get_random_file_content(folder_path):
        all_files = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
        all_files.remove('prompt_and_scenario_info.txt')
        random.shuffle(all_files)
        
        selected_file = all_files[0]
        file_path = os.path.join(folder_path, selected_file)
        with open(file_path, 'r') as file:
                file_content = file.read()
        
        return selected_file, file_content
    
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
    
    if display_sample:
        selected_file_name, file_content = get_random_file_content(path_on_disk)
        notification_text = f"Here is a sample for the generated_conversation from file : {selected_file_name}"
        slack_notification(
                message=notification_text,
                channel=channel,
                cc=notify,
                code_block=file_content,
                thread_id=thread_id,
            )

zip_file_and_notify_op = kfp.components.create_component_from_func(
    zip_file_and_notify, base_image=pipeline_constants.BASE_IMAGE
)