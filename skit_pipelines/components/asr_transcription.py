import kfp
from kfp.components import InputPath, OutputPath

from skit_pipelines import constants as pipeline_constants


def audio_transcription(
    audios_dir_path: InputPath(str),
    config_path: InputPath(str),
    output_path: OutputPath(str),
    concurrency: int,
) -> None:
    import os

    from skit_pipelines import constants as pipeline_constants

    def exec_shell(cmd: str, tolerant: bool = False, print_command=True):
        import subprocess
        import sys

        if print_command:
            print(f"executing: {cmd}", file=sys.stdout)
        else:
            print("executing command with print_command as False")
        code = subprocess.call(
            cmd,
            shell=True,
            executable="/bin/bash",
            stdout=sys.stdout,
            stderr=sys.stderr,
        )
        if code:
            if not tolerant:
                raise Exception(f"command {cmd} failed with non-zero code: {code}")
            else:
                print(f"return code: {code}, but tolerant is set as {tolerant}")

    exec_shell(
        f"git clone https://{pipeline_constants.PERSONAL_ACCESS_TOKEN_GITHUB}@github.com/skit-ai/blaze.git",
        print_command=False,
    )

    exec_shell("conda create -n condaenv python=3.8")
    exec_shell("echo 'conda activate condaenv' >> ~/.bashrc")
    # exec_shell("conda install python=3.6")
    exec_shell("source ~/.bashrc && conda install -n condaenv git pip")

    exec_shell("source ~/.bashrc && pip install poetry")

    exec_shell(f"source ~/.bashrc && cd blaze && poetry install --no-dev")
    exec_shell(
        f"source ~/.bashrc && cd blaze && poetry run blaze {audios_dir_path} {config_path} {output_path} --concurrency={concurrency}"
    )


audio_transcription_op = kfp.components.create_component_from_func(
    audio_transcription, base_image=pipeline_constants.BASE_IMAGE
)
