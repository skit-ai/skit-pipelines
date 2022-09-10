import skit_pipelines.api.models.errors as errors
from skit_pipelines.api.models.custom_models import ParseRunResponse
from skit_pipelines.api.models.requests import (
    BaseRequestSchema,
    StorageOptions,
    generate_schema,
    get_all_pipelines_fn,
    get_normalized_pipelines_fn_map,
    set_nodegroup_for_pipelines,
)
from skit_pipelines.api.models.auth_models import Token, TokenData, User, UserInDB
import skit_pipelines.api.auth as auth

from skit_pipelines.api.models.responses import (
    customResponse,
    statusWiseResponse,
    successfulCreationResponse,
)

RequestSchemas = {
    pipeline_name: generate_schema(pipeline_name, pipeline_fn)
    for pipeline_name, pipeline_fn in get_all_pipelines_fn().items()
}

PodNodeSelectorMap = {
    pipeline_name: set_nodegroup_for_pipelines(pipeline_fn)
    for pipeline_name, pipeline_fn in get_normalized_pipelines_fn_map().items()
}