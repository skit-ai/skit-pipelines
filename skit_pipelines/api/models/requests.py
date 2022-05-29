import inspect
from typing import Optional

from pydantic import BaseModel, create_model, validator

import skit_pipelines.constants as const
from skit_pipelines import pipelines
from skit_pipelines.utils.normalize import to_camel_case


def get_all_pipelines_fn():
    return {
        pipeline_name: pipeline_fn
        for pipeline_name, pipeline_fn in pipelines.__dict__.items()
        if not pipeline_name.startswith("__") and callable(pipeline_fn)
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


class FetchCallSchema(BaseRequestSchema):
    """
    Fetch Calls schema
    """

    webhook_uri: str | None = None
    client_id: int
    start_date: str
    lang: str
    end_date: str | None = ""
    call_quantity: int = 200
    call_type: str = "inbound"
    ignore_callers: str | None = ""
    reported: str | None = ""
    use_case: str | None = ""
    flow_name: str | None = ""
    min_duration: str | None = ""
    asr_provider: str | None = ""
    notify: bool | None = False


class TagCallSchema(BaseRequestSchema):
    """
    Tag Calls Schema
    """

    webhook_uri: str | None = None
    org_id: str
    job_id: int
    s3_path: str
    notify: str | None = False


class TrainModelSchema(BaseRequestSchema):
    """
    Train Models Schema
    """

    webhook_uri: str | None = None
    dataset_path: str
    model_path: str
    storage_options: StorageOptions
    classifier_type: str = "xlmr"
    org_id: str = ""
    use_state: bool = False
    model_type: str = "xlmroberta"
    model_name: str = "xlm-roberta-base"
    num_train_epochs: int = 10
    use_early_stopping: bool = False
    early_stopping_patience: int = 3
    early_stopping_delta: float = 0.0
    max_seq_length: int = 128
    learning_rate: float = 4e-5
