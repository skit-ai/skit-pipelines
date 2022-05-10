from typing import Union

import kfp
from kfp.components import InputPath, OutputPath

from skit_pipelines import constants as pipeline_constants


def extract_tgz_archive(
    tgz_path: InputPath(str),
    output_path: OutputPath(str),
):
    import tarfile

    from loguru import logger

    logger.debug(f"Extracting .tgz archive {tgz_path}.")
    tar = tarfile.open(tgz_path)
    tar.extractall(path=output_path)
    tar.close()
    logger.debug(f"Extracted successfully.")


extract_tgz_op = kfp.components.create_component_from_func(
    extract_tgz_archive, base_image=pipeline_constants.BASE_IMAGE
)
