from typing import List

from skit_labels import constants as labels_constants
from skit_labels.cli import upload_dataset

from skit_pipelines import constants as pipeline_constants


def upload2tog(input_file: str, token: str, job_ids: List[str]):
    url = pipeline_constants.CONSOLE_API_URL
    errors = []
    df_sizes = []
    for job_id in job_ids:
        errors, df_size = upload_dataset(
            input_file, url, token, job_id, labels_constants.SOURCE__DB
        )
        if errors:
            errors.extend(errors)
        df_sizes.append(df_size)
    return errors, df_sizes
