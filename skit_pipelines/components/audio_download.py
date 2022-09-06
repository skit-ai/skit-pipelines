import kfp
import os

from skit_pipelines import constants as pipeline_constants

def pull_audio(
    audio_url: str,
    output: str,
) -> None:
    os.system("./johnny -input {audio_url} -output {output}/")

pull_audio_op = kfp.components.create_component_from_func(
    pull_audio, base_image = pipeline_constants.BASE_IMAGE
)