from typing import Union
import kfp
from kfp.components import InputPath,OutputPath

from skit_pipelines import constants as pipeline_constants


def extract_tgz_archive(
    tgz_path: InputPath(str),
    output_path: OutputPath(str),
) -> str:
    import tarfile

    from loguru import logger

    tar = tarfile.open(tgz_path, "r:gz")
    tar.extractall(path=output_path)
    tar.close()

    logger.debug(f"Extracted .tgz archive {tgz_path} to {output_path}.")


extract_tgz_op = kfp.components.create_component_from_func(
    extract_tgz_archive, base_image=pipeline_constants.BASE_IMAGE
)
