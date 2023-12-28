from loguru import logger
from skit_labels import constants as labels_constants
from skit_labels.cli import upload_dataset

from skit_pipelines import constants as pipeline_constants
from skit_pipelines.types.tag_calls import TaggingResponse
from skit_pipelines.components.upload_conv_to_labelstudio.utils import process_folder_and_save_csv

from skit_labels.cli import is_valid_data_label
from skit_labels.constants import VALID_DATA_LABELS

import argparse
from kfp.components import InputPath
from skit_pipelines.types.tag_calls import TaggingResponseType
import kfp
from typing import List, Dict


def upload_conv_to_label_studio(project_id: str,
                                conversations_dir: InputPath,
                                data_label: str,  
                                situations_id_info: List[Dict[str, str]]) -> TaggingResponseType:
    
    data_label = data_label or pipeline_constants.DATA_LABEL_DEFAULT
    error, df_size = [], []
    try:
        is_valid_data_label(data_label)
    except argparse.ArgumentTypeError as e:
        raise ValueError(
            f"Recieved an invalid data_label. Please pass one of [{', '.join(VALID_DATA_LABELS)}] as data_label"
                )
    
    csv_path  = process_folder_and_save_csv(conversations_dir, situations_id_info)
    error, df_size = upload_dataset(
            csv_path,
            pipeline_constants.LABELSTUDIO_SVC,
            pipeline_constants.LABELSTUDIO_TOKEN,
            project_id,
            labels_constants.SOURCE__LABELSTUDIO,
            data_label,
            tagging_type=labels_constants.CONVERSATION_TAGGING
        )

    response = TaggingResponse(str(error), str(df_size))

    if not response.df_size:
        logger.warning(f"No calls were uploaded for tagging. Please check your provided parameters")

    logger.info(f"{response.df_size} rows in the dataset")
    logger.info(f"{response.error=}")

    return response

upload_conv_to_label_studio_op = kfp.components.create_component_from_func(
    upload_conv_to_label_studio, base_image=pipeline_constants.BASE_IMAGE
)
