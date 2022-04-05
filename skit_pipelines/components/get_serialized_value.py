from typing import Any

import kfp
from kfp.components import InputPath

from skit_pipelines import constants as pipeline_constants


def get_value(
    req_value: str, input_file: InputPath(str)
) -> Any:

    import os
    import json    
    from loguru import logger
    
    serialized_obj = {}
    if os.path.isfile(input_file):
        with open(input_file, "r") as j_read:
            serialized_obj = json.load(j_read)
    
    logger.info(f"{serialized_obj=}")
    return serialized_obj.get(req_value)

get_value_op = kfp.components.create_component_from_func(
    get_value, base_image=pipeline_constants.BASE_IMAGE
)
