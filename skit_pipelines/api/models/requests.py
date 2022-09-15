import inspect
from typing import Dict, Optional

from pydantic import BaseModel, create_model, validator

import skit_pipelines.constants as const
from skit_pipelines import pipelines
from skit_pipelines.utils.normalize import to_camel_case, to_snake_case


def get_all_pipelines_fn():
    return {
        pipeline_name: pipeline_fn
        for pipeline_name, pipeline_fn in pipelines.__dict__.items()
        if not pipeline_name.startswith("__") and callable(pipeline_fn)
    }


def set_nodegroup_for_pipelines(pipeline_fn):
    source_code = inspect.getsourcelines(pipeline_fn)
    for line in source_code[0]:
        if ".set_gpu_limit(" in line:
            return const.GPU_NODE_LABEL
    return const.CPU_NODE_LABEL


def get_normalized_pipelines_fn_map():
    return {
        to_snake_case(pipeline_name): pipeline_fn
        for pipeline_name, pipeline_fn in get_all_pipelines_fn().items()
    }


def generate_schema(pipeline_name, pipeline_fn):
    signature = inspect.signature(pipeline_fn)
    params = {
        param_name: (
            param.annotation,
            param.default if param.default is not inspect.Parameter.empty else ...,
        )
        for param_name, param in signature.parameters.items()
    }
    params = {"webhook_uri": (Optional[str], None), **params}
    return create_model(
        to_camel_case(pipeline_name), **params, __base__=BaseRequestSchema
    )


class BaseRequestSchema(BaseModel):
    @validator("*", pre=True)
    def transform_none(cls, value):
        return "" if value is None else value


class StorageOptions(BaseRequestSchema):
    type: str = "s3"
    bucket: str = const.BUCKET
