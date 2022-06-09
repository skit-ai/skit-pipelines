from typing import Any, Dict, Optional

import kfp
from kfp.components import InputPath, OutputPath

from skit_pipelines import constants as pipeline_constants


def tag_calls(
    *,
    input_file: str,
    job_ids: str = "",
    project_id: Optional[str] = None,
    token: InputPath(str),
    url: str = None,
    output_json: OutputPath(str),
) -> Dict[str, Any]:

    import json
    import traceback

    import pandas as pd
    from loguru import logger
    from skit_labels import utils
    from skit_pipelines.utils.normalize import comma_sep_str
    from skit_pipelines.components.tag_calls.tog import upload2tog
    from skit_pipelines.components.tag_calls.labelstudio import upload2labelstudio
    from skit_pipelines.components.tag_calls.base import Response

    utils.configure_logger(7)
    response = Response([], [])

    try:
        job_ids = comma_sep_str(job_ids)
        if job_ids:
            response = upload2tog(input_file, token, job_ids, response)

        if project_id:
            response = upload2labelstudio(input_file, project_id, response)

        if response.errors:
            logger.error(response.errors)
        logger.info(f"{response.df_sizes} rows in the dataset")
        logger.info(f"{response.errors=}")

    except pd.errors.EmptyDataError:
        logger.error("empty dataframe")
    except Exception as e:
        logger.error(e)
        logger.error(traceback.format_exc())

    with open(output_json, "w") as f:
        json.dump(response._asdict(), f, indent=4)
    return response._asdict()


tag_calls_op = kfp.components.create_component_from_func(
    tag_calls, base_image=pipeline_constants.BASE_IMAGE
)
