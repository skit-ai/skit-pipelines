from typing import Optional

import kfp
from kfp.components import OutputPath

from skit_pipelines import constants as pipeline_constants


def fetch_tagged_dataset(
    output_path: OutputPath(str),
    job_id: Optional[str] = None,
    project_id: Optional[str] = None,
    task_type: str = "conversation",
    timezone: str = "Asia/Kolkata",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    start_date_offset: Optional[int] = None,
    end_date_offset: Optional[int] = None,
):
    import asyncio
    import time

    import pandas as pd
    import pytz
    from loguru import logger
    from skit_calls.cli import process_date_filters
    from skit_labels import constants as const
    from skit_labels import utils
    from skit_labels.commands import (
        download_dataset_from_db,
        download_dataset_from_labelstudio,
    )

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

    if start_date_offset or end_date_offset:
        start_date, end_date = process_date_filters(
                start_date_offset=start_date_offset,
                end_date_offset=end_date_offset,
            )

    if job_id:
        df_path, _ = download_dataset_from_db(
            job_id=int(job_id),
            task_type=task_type or None,
            timezone=pytz.timezone(timezone) if timezone else None,
            start_date=start_date or None,
            end_date=end_date or None,
            host=host,
            port=port,
            password=password,
            user=user,
        )
    elif project_id:
        df_path, _ = asyncio.run(
            download_dataset_from_labelstudio(
                url=pipeline_constants.LABELSTUDIO_SVC,
                token=pipeline_constants.LABELSTUDIO_TOKEN,
                project_id=int(project_id),
            )
        )
    else:
        raise ValueError("Either job_id or project_id must be provided")

    logger.info(f"Finished in {time.time() - start:.2f} seconds")
    df = pd.read_csv(df_path)
    df.to_csv(output_path, index=False)


fetch_tagged_dataset_op = kfp.components.create_component_from_func(
    fetch_tagged_dataset, base_image=pipeline_constants.BASE_IMAGE
)
