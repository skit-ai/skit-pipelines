from typing import List

from skit_labels.cli import upload_dataset
from skit_labels import constants as labels_constants
from skit_pipelines import constants as pipeline_constants
from skit_pipelines.components.tag_calls.base import Response


def upload2tog(input_file: str, token: str, job_ids: List[str], response: Response):
    url = pipeline_constants.CONSOLE_API_URL
    for job_id in job_ids:
        errors, df_size = upload_dataset(
            input_file, url, token, job_id, labels_constants.SOURCE__DB
        )
    if errors:
        response.errors.extend(errors)
        response.df_sizes.append(df_size)
    return response
