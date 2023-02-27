from typing import Optional

import kfp
from kfp.components import InputPath, OutputPath

from skit_pipelines import constants as pipeline_constants


def modify_entity_dataset(
    data_path: InputPath(str),
    output_path: OutputPath(str),
    tog_job_id: Optional[str] = None,
    labelstudio_project_id: Optional[str] = None,
    timezone: str = "Asia/Kolkata",
):
    """
    Takes a entity dataset and,
    1) hits duckling service for inference on ground-truth
    2) modifies the predicted entity structure to be consistent
    """

    import pandas as pd
    from loguru import logger

    from skit_pipelines import constants as pipeline_constants
    from skit_pipelines.components import modify_entities

    df = pd.read_csv(data_path)

    logger.info(f"duckling running at: {pipeline_constants.DUCKLING_HOST}")

    if tog_job_id:
        ds_source = "tog"
    elif labelstudio_project_id:
        ds_source = "labelstudio"
    else:
        logger.error(f"unsupported data source")

    mod_df = modify_entities.modify_truth(df, ds_source, timezone)
    mod_df = modify_entities.modify_predictions(mod_df, ds_source)
    mod_df.to_csv(output_path, index=False)


modify_entity_dataset_op = kfp.components.create_component_from_func(
    modify_entity_dataset, base_image=pipeline_constants.BASE_IMAGE
)


if __name__ == "__main__":

    # modify_entity_dataset("4284.csv", "duck_4284.csv", tog_job_id=4284)
    # modify_entity_dataset("l2.csv", "duck_l2.csv", labelstudio_project_id=85)

    # modify_entity_dataset("lu2.csv", "duck_lu2.csv", labelstudio_project_id=85, timezone="America/New_York")

    modify_entity_dataset("amey_65.csv", "amey_65_duck.csv", labelstudio_project_id=65)