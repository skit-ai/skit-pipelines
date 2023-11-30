from typing import Optional

import kfp

from skit_pipelines import constants as pipeline_constants
from skit_pipelines.types.tag_calls import TaggingResponseType


def tag_calls(
    input_file: str,
    data_label: str = "",
    project_id: Optional[str] = None,
    call_project_id: Optional[str] = None,
) -> TaggingResponseType:
    import argparse

    from loguru import logger
    from skit_labels import utils
    from skit_labels.cli import is_valid_data_label
    from skit_labels.constants import VALID_DATA_LABELS

    from skit_pipelines import constants as pipeline_constants
    from skit_pipelines.components.tag_calls.labelstudio import upload2labelstudio
    from skit_pipelines.types.tag_calls import TaggingResponse
    from skit_pipelines.utils.normalize import comma_sep_str

    utils.configure_logger(7)
    error_string = ""
    errors, df_sizes = [], []

    data_label = data_label or pipeline_constants.DATA_LABEL_DEFAULT
    try:
        is_valid_data_label(data_label)
    except argparse.ArgumentTypeError as e:
        raise ValueError(
            f"Recieved an invalid data_label. Please pass one of [{', '.join(VALID_DATA_LABELS)}] as data_label"
        )

    print(f"{project_id=}")
    print(f"{call_project_id=}")

    if project_id:
        project_ids = comma_sep_str(project_id)
        logger.debug(f"{project_ids=}")
        error, df_size = upload2labelstudio(input_file, project_ids, data_label)
        errors.append(error)
        df_sizes.append(df_size)

    if call_project_id:
        call_project_ids = comma_sep_str(call_project_id)
        logger.debug(f"{call_project_ids=}")
        error, df_size = upload2labelstudio(input_file, call_project_ids, data_label)
        errors.append(error)
        df_sizes.append(df_size)

    if errors:
        error_string = "\n".join(errors)
    df_size_string = ", ".join(map(str, df_sizes))

    response = TaggingResponse(error_string, df_size_string)

    if not response.df_sizes:
        logger.warning(f"No calls were uploaded for tagging. Please check your provided parameters")

    logger.info(f"{response.df_sizes} rows in the dataset")
    logger.info(f"{response.errors=}")

    return response


tag_calls_op = kfp.components.create_component_from_func(
    tag_calls, base_image=pipeline_constants.BASE_IMAGE
)
