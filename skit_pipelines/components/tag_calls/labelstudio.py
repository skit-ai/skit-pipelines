import tempfile

from skit_labels import constants as labels_constants
from skit_labels.cli import upload_dataset

from skit_pipelines import constants as pipeline_constants
from skit_pipelines.components.download_from_s3 import download_csv_from_s3
from skit_pipelines.types.tag_calls import TaggingResponse


def upload2labelstudio(input_file: str, project_id: str, data_label: str):
    _, save_path = tempfile.mkstemp(suffix=".csv")
    download_csv_from_s3(storage_path=input_file, output_path=save_path)
    error, df_size = upload_dataset(
        save_path,
        pipeline_constants.LABELSTUDIO_SVC,
        pipeline_constants.LABELSTUDIO_TOKEN,
        project_id,
        labels_constants.SOURCE__LABELSTUDIO,
        data_label,
    )
    return str(error), df_size
