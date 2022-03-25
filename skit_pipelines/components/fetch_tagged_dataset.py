import os
from typing import Optional

import kfp
from kfp.components import InputPath

from skit_pipelines import constants as pipeline_constants


def fetch_tagged_dataset(
    job_id: str,
    task_type: Optional[str] = None,
    timezone: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    user: Optional[str] = None,
    password: Optional[str] = None,
    host: Optional[str] = None,
    port: Optional[int | str] = None,
) -> InputPath():
    import tempfile
    import time
    import pytz

    from loguru import logger
    from skit_labels import utils
    from skit_labels import constants as const
    from skit_pipelines import constants as pipeline_constants
    from skit_labels.commands import download_dataset_from_db

    utils.configure_logger(7)

    host = host or pipeline_constants.DB_HOST
    port = port or pipeline_constants.DB_PORT
    password = password or pipeline_constants.DB_PASSWORD
    user = user or pipeline_constants.DB_USER


    if not timezone:
        timezone = pytz.UTC

    if not task_type:
        task_type = const.TASK_TYPE__CONVERSATION

    start = time.time()

    df_path, _ = download_dataset_from_db(
        job_id=job_id,
        task_type=task_type or None,
        timezone=timezone or None,
        start_date=start_date or None,
        end_date=end_date or None,
        host=host,
        port=port,
        password=password,
        user=user,
        )
    

    logger.info(f"Finished in {time.time() - start:.2f} seconds")
    return df_path


fetch_tagged_dataset_op = kfp.components.create_component_from_func(
    fetch_tagged_dataset, base_image=pipeline_constants.BASE_IMAGE
)
