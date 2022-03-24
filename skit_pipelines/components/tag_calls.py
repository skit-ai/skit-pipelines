import os
from typing import List

import kfp
from kfp.components import InputPath

from skit_pipelines import constants as pipeline_constants


def tag_calls(
    input_file: str, job_id: int, token: InputPath(str), url: str = None
) -> List:

    import time

    from loguru import logger
    from skit_labels import utils
    from skit_labels.cli import upload_dataset

    from skit_pipelines import constants as pipeline_constants

    utils.configure_logger(7)

    url = pipeline_constants.CONSOLE_API_URL if url is None else url
    with open(token, "r") as reader:
        token = reader.read()
    start = time.time()
    errors, df_size = upload_dataset(input_file, url, token, job_id)
    logger.info(f"Uploaded in {time.time() - start:.2f} seconds to {job_id=}")
    logger.info(f"{df_size=} rows in the dataset")
    return errors


tag_calls_op = kfp.components.create_component_from_func(
    tag_calls, base_image=pipeline_constants.BASE_IMAGE
)
