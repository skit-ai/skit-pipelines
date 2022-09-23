import kfp
from kfp.components import InputPath, OutputPath

from skit_pipelines import constants as pipeline_constants


def download_audio_wavs(
    audio_data_path: InputPath(str),
    audio_sample_rate: str,
    audio_download_workers: int,
    output_path: OutputPath(str),
) -> None:
    import os

    os.system(
        f"./johnny -input {audio_data_path} -output {output_path} -rate {audio_sample_rate} -workers {audio_download_workers}"
    )


download_audio_wavs_op = kfp.components.create_component_from_func(
    download_audio_wavs, base_image=pipeline_constants.BASE_IMAGE
)
