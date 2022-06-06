from typing import Any, Dict, Optional

import kfp
from kfp.components import InputPath, OutputPath

from skit_pipelines import constants as pipeline_constants


def tag_calls(
    *,
    input_file: str,
    job_ids: str,
    project_id: Optional[str] = None,
    token: InputPath(str),
    url: str = None,
    output_json: OutputPath(str),
) -> Dict[str, Any]:

    import json
    import os
    import time
    import pandas as pd

    from loguru import logger
    from skit_labels import utils
    from skit_labels.cli import upload_dataset
    from skit_labels import constants as labels_constants

    from skit_pipelines import constants as pipeline_constants

    utils.configure_logger(7)

    all_errors, df_sizes = ["no errors"], [0,0,0]
    output_dict = {"errors": all_errors, "df_sizes": df_sizes}
    input_file = input_file.lstrip("<").rstrip(">")
    try:
        url = pipeline_constants.CONSOLE_API_URL if url is None else url
        job_ids = job_ids.replace(" ", "").split(',')

        output_dict["all_errors"], output_dict["df_sizes"] = [], []
        for job_id in job_ids:
            start = time.time()

            errors, df_size = upload_dataset(input_file, url, token, int(job_id), labels_constants.SOURCE__DB)
            output_dict["all_errors"].append(errors)
            output_dict["df_sizes"].append(df_size)

            logger.info(f"Uploaded in {time.time() - start:.2f} seconds to {job_id=}")
            logger.info(f"{df_size=} rows in the dataset")
            logger.info(f"{errors=}")

        if project_id:
            errors, df_size = upload_dataset(input_file, url, token, int(project_id), labels_constants.SOURCE__LABELSTUDIO)
    except pd.errors.EmptyDataError:
        logger.error("empty dataframe")
    except Exception as e:
        logger.error(e)
        output_dict["all_errors"] = [e]

    with open(output_json, "w") as writer:
        json.dump(output_dict, writer, indent=4)
    return output_dict


tag_calls_op = kfp.components.create_component_from_func(
    tag_calls, base_image=pipeline_constants.BASE_IMAGE
)
