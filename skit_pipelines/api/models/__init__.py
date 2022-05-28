from skit_pipelines.api.models.requests import (
    BaseRequestSchema, FetchCallSchema, TagCallSchema, TrainModelSchema, StorageOptions, get_all_pipelines_fn, generate_schema
)
from skit_pipelines.api.models.responses import customResponse, statusWiseResponse, successfulCreationResponse
from skit_pipelines.api.models.custom_models import ParseRunResponse

import skit_pipelines.api.models.errors as errors


RequestSchemas = {
    pipeline_name: generate_schema(pipeline_name, pipeline_fn)
    for pipeline_name, pipeline_fn in get_all_pipelines_fn().items()
}
