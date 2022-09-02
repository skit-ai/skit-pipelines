from typing import Optional

import kfp

from skit_pipelines import constants as pipeline_constants
from skit_pipelines.types.tag_calls import TaggingResponseType


def tag_calls(
    input_file: str,
    token: str = "",
    job_ids: str = "",
    project_id: Optional[str] = None,
    org_id: Optional[str] = None
) -> TaggingResponseType:
    from loguru import logger
    from skit_labels import utils

    from skit_pipelines.components.tag_calls.labelstudio import upload2labelstudio
    from skit_pipelines.components.tag_calls.tog import upload2tog
    from skit_pipelines.types.tag_calls import TaggingResponse
    from skit_pipelines.utils.normalize import comma_sep_str

    utils.configure_logger(7)
    error_string = ""
    df_size_string = ""
    errors = []
    df_sizes = []
    org_id = int(org_id) if org_id else org_id
    
    job_ids = comma_sep_str(job_ids)
    if not job_ids and not project_id:
        raise ValueError("Either job_ids or project_id must be provided")

    if not project_id and org_id:
        if org_id == 120:
            job_ids = None
            project_id = 105

        if org_id == 146:
            job_ids = None
            project_id = 99

        if org_id == 147:
            job_ids = None
            project_id = 99

        if org_id == 34:
            job_ids = None
            project_id = 109

        # LabelStudio is not prepared for these
        # if org_id == 2:
        #     job_ids = None
        #     project_id = 110
        # if org_id == 4:
        #     job_ids = None
        #     project_id = 111

    if job_ids:
        errors, df_sizes = upload2tog(input_file, token, job_ids)

    if project_id:
        error, df_size = upload2labelstudio(input_file, project_id)
        errors.append(error)
        df_sizes.append(df_size)

    if errors:
        error_string = "\n".join(errors)
    df_size_string = ", ".join(map(str, df_sizes))

    response = TaggingResponse(error_string, df_size_string)

    if not response.df_sizes:
        raise ValueError(f"Nothing was uploaded.")

    logger.info(f"{response.df_sizes} rows in the dataset")
    logger.info(f"{response.errors=}")

    return response


tag_calls_op = kfp.components.create_component_from_func(
    tag_calls, base_image=pipeline_constants.BASE_IMAGE
)
