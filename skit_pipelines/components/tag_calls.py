from typing import Any, Dict, List

import kfp
from kfp.components import InputPath, OutputPath

from skit_pipelines import constants as pipeline_constants


def tag_calls(
    *,
    input_file: str,
    job_ids: str,
    token: InputPath(str),
    url: str = None,
    output_json: OutputPath(str),
) -> Dict[str, Any]:

    import json
    import os
    import time

    from loguru import logger
    from skit_labels import utils
    from skit_labels.cli import upload_dataset

    from skit_pipelines import constants as pipeline_constants

    utils.configure_logger(7)

    url = pipeline_constants.CONSOLE_API_URL if url is None else url
    job_ids = job_ids.replace(" ", "").split(",")

    if os.path.isfile(input_file):
        with open(input_file, "r") as f:
            input_file = f.read()

    with open(token, "r") as reader:
        token = reader.read()

    all_errors, df_sizes = [], []
    for job_id in job_ids:
        start = time.time()

        errors, df_size = upload_dataset(input_file, url, token, int(job_id))
        all_errors.append(errors)
        df_sizes.append(df_size)

        logger.info(f"Uploaded in {time.time() - start:.2f} seconds to {job_id=}")
        logger.info(f"{df_size=} rows in the dataset")
        logger.info(f"{errors=}")

    output_dict = {"errors": all_errors, "df_sizes": df_sizes}
    with open(output_json, "w") as writer:
        json.dump(output_dict, writer, indent=4)
    return output_dict


tag_calls_op = kfp.components.create_component_from_func(
    tag_calls, base_image=pipeline_constants.BASE_IMAGE
)
