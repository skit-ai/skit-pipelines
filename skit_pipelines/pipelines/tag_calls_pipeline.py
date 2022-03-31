import kfp

from skit_pipelines import constants as pipeline_constants
from skit_pipelines.components import (
    org_auth_token_op,
    tag_calls_op,
)


@kfp.dsl.pipeline(
    name="Tag Calls Pipeline",
    description="Uploads calls to database for tagging",
)
def run_tag_calls(org_id: int, job_id: int, s3_path: str):
    auth_token = org_auth_token_op(org_id)
    tag_calls_op(
        input_file=s3_path,
        job_id=job_id,
        token=auth_token.output,
    )
