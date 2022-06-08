from skit_labels.cli import upload_dataset
from skit_labels import constants as labels_constants
from skit_pipelines import constants as pipeline_constants
from skit_pipelines.components.tag_calls.base import Response


def upload2labelstudio(input_file: str, project_id: str, response: Response):
    errors, df_size = upload_dataset(
        input_file,
        pipeline_constants.LABELSTUDIO_SVC,
        pipeline_constants.LABELSTUDIO_TOKEN,
        project_id,
        labels_constants.SOURCE__LABELSTUDIO,
    )
    if errors:
        response.errors.extend(errors)
    response.df_sizes.append(df_size)
    return response
