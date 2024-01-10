from typing import Optional

import kfp
from kfp.components import OutputPath

from skit_pipelines import constants as pipeline_constants


def fetch_tagged_dataset(
    output_path: OutputPath(str),
    job_id: Optional[str] = None,
    project_id: Optional[str] = None,
    task_type: str = "conversation",
    timezone: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    start_date_offset: Optional[int] = None,
    end_date_offset: Optional[int] = None,
    empty_possible: bool = False,
):
    import time

    import pandas as pd
    import pytz
    from loguru import logger
    from skit_calls.cli import process_date_filters
    from skit_labels import constants as const
    from skit_labels import utils
    from skit_labels.commands import download_dataset_from_db

    from skit_pipelines import constants as pipeline_constants
    from skit_pipelines.utils.normalize import comma_sep_str

    utils.configure_logger(7)
    if not timezone:
        timezone = pipeline_constants.TIMEZONE

    if not task_type:
        task_type = const.TASK_TYPE__CONVERSATION

    start = time.time()
    df_paths = []

    if start_date_offset or end_date_offset:
        start_date, end_date = process_date_filters(
            start_date_offset=start_date_offset,
            end_date_offset=end_date_offset,
        )

    if job_id or project_id:
        job_ids = comma_sep_str(job_id or project_id)  # tog or labelstudio
        for job_id in job_ids:
            df_path, _ = download_dataset_from_db(
                job_id=int(job_id),
                task_type=task_type or None,
                timezone=pytz.timezone(timezone) if timezone else None,
                start_date=start_date or None,
                end_date=end_date or None,
                host=pipeline_constants.DB_HOST,
                port=pipeline_constants.DB_PORT,
                password=pipeline_constants.DB_PASSWORD,
                user=pipeline_constants.DB_USER,
                db=const.LABELSTUIO_DB if project_id else "tog",
            )
            df_paths.append(df_path)

    else:
        if not empty_possible:
            raise ValueError("Either job_id or project_id must be provided")
        else:
            pd.DataFrame().to_csv(output_path, index=False)
            return

    logger.info(f"Finished in {time.time() - start:.2f} seconds")
    df = pd.concat([pd.read_csv(df_path) for df_path in df_paths])
    df.to_csv(output_path, index=False)


fetch_tagged_dataset_op = kfp.components.create_component_from_func(
    fetch_tagged_dataset, base_image=pipeline_constants.BASE_IMAGE
)
