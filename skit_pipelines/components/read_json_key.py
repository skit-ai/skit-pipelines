from typing import Any

import kfp
from kfp.components import InputPath

from skit_pipelines import constants as pipeline_constants


def read_json_key(req_value: str, input_file: InputPath(str)) -> Any:
    
    import json
    import os

    from loguru import logger

    serialized_obj = {}
    if os.path.isfile(input_file):
        with open(input_file, "r") as j_read:
            serialized_obj = json.load(j_read)

    logger.info(f"{serialized_obj=}")
    val = serialized_obj.get(req_value)
    logger.info(f"requested key: {req_value} = {val}")
    return val


read_json_key_op = kfp.components.create_component_from_func(
    read_json_key, base_image=pipeline_constants.BASE_IMAGE
)
