from typing import List, Tuple

import kfp
from kfp.components import InputPath, OutputPath

from skit_pipelines import constants as pipeline_constants


def tag_calls(
    *, input_file: str, job_id: int, token: InputPath(str), url: str = None, output_json: OutputPath(str)
):

    import time
    import os
    import json
    
    from loguru import logger
    from skit_labels import utils
    from skit_labels.cli import upload_dataset

    from skit_pipelines import constants as pipeline_constants

    utils.configure_logger(7)

    url = pipeline_constants.CONSOLE_API_URL if url is None else url
    
    if os.path.isfile(input_file):
        with open(input_file, "r") as f:
            input_file = f.read(input_file)
            
    with open(token, "r") as reader:
        token = reader.read()
    start = time.time()
    errors, df_size = upload_dataset(input_file, url, token, job_id)
    # write to json
    with open(output_json, "w") as writer:
        json.dump(
            {"errors": errors, "df_size": df_size},
            writer, indent=4
        )
    logger.info(f"Uploaded in {time.time() - start:.2f} seconds to {job_id=}")
    logger.info(f"{df_size=} rows in the dataset")


tag_calls_op = kfp.components.create_component_from_func(
    tag_calls, base_image=pipeline_constants.BASE_IMAGE
)
