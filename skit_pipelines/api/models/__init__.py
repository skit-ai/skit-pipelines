from skit_pipelines.api.models.requests import (
    BaseRequestSchema, FetchCallSchema, TagCallSchema, TrainModelSchema
)
from skit_pipelines.api.models.responses import customResponse, statusWiseResponse, successfulCreationResponse
from skit_pipelines.api.models.custom_models import ParseRunResponse

import skit_pipelines.api.models.errors as errors

from typing import Union

ValidRequestSchemas = Union[
    FetchCallSchema,
    TagCallSchema,
    TrainModelSchema
]