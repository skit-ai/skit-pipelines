import tempfile

from loguru import logger
from skit_labels import constants as labels_constants
from skit_labels.cli import upload_dataset

from skit_pipelines import constants as pipeline_constants
from skit_pipelines.components.download_from_s3 import download_csv_from_s3
from skit_pipelines.types.tag_calls import TaggingResponse


def upload2labelstudio(input_file: str, project_ids: list, data_label: str):
    _, save_path = tempfile.mkstemp(suffix=".csv")
    download_csv_from_s3(storage_path=input_file, output_path=save_path)
    errors, df_sizes = [], []
    for project_id in project_ids:
        logger.info(f"{project_id=}")
        error, df_size = upload_dataset(
            save_path,
            pipeline_constants.LABELSTUDIO_SVC,
            pipeline_constants.LABELSTUDIO_TOKEN,
            project_id,
            labels_constants.SOURCE__LABELSTUDIO,
            data_label,
        )
        if error:
            errors.extend(error)
        df_sizes.append(df_size)
    return str(errors), df_sizes
