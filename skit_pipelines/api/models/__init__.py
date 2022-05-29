import skit_pipelines.api.models.errors as errors
from skit_pipelines.api.models.custom_models import ParseRunResponse
from skit_pipelines.api.models.requests import (
    BaseRequestSchema,
    FetchCallSchema,
    StorageOptions,
    TagCallSchema,
    TrainModelSchema,
    generate_schema,
    get_all_pipelines_fn,
)
from skit_pipelines.api.models.responses import (
    customResponse,
    statusWiseResponse,
    successfulCreationResponse,
)

RequestSchemas = {
    pipeline_name: generate_schema(pipeline_name, pipeline_fn)
    for pipeline_name, pipeline_fn in get_all_pipelines_fn().items()
}
