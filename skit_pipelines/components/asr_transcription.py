import kfp

from skit_pipelines import constants as pipeline_constants

def transcription_audio(
    audio_path: str,
    config_path: str,
) -> None:
    import os
    os.system("poetry run blaze {audio_path} {config_path}")

transcription_audio_op = kfp.components.create_component_from_func(
    transcription_audio, base_image = pipeline_constants.BASE_IMAGE
)