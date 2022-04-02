from typing import Optional

import kfp
from kfp.components import OutputPath

from skit_pipelines import constants as pipeline_constants


def fetch_tagged_dataset(
    output_path: OutputPath(str),
    job_id: int,
    task_type: str = "conversation",
    timezone: str = "Asia/Kolkata",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
):
    import time

    import pandas as pd
    import pytz
    from loguru import logger
    from skit_labels import constants as const
    from skit_labels import utils
    from skit_labels.commands import download_dataset_from_db

    from skit_pipelines import constants as pipeline_constants

    utils.configure_logger(7)

    host = pipeline_constants.DB_HOST
    port = pipeline_constants.DB_PORT
    password = pipeline_constants.DB_PASSWORD
    user = pipeline_constants.DB_USER

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
    df = pd.read_csv(df_path)
    df.to_csv(output_path, index=False)


fetch_tagged_dataset_op = kfp.components.create_component_from_func(
    fetch_tagged_dataset, base_image=pipeline_constants.BASE_IMAGE
)
