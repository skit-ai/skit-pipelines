import kfp
from kfp.components import InputPath, OutputPath

from skit_pipelines import constants as pipeline_constants


def create_intent_labels(
    data_path: InputPath(str), 
    output_path: OutputPath(str),
    tog_job_id = None,
    labelstudio_project_id = None
    ):
    import pandas as pd
    from loguru import logger

    from skit_pipelines import constants as pipeline_constants
    from skit_pipelines.components.preprocess.create_true_intent_column.utils import (
        pick_1st_tag,
    )

    INTENT_Y = pipeline_constants.INTENT_Y

    train_df = pd.read_csv(data_path)

    # preprocessing step needs to be skipped for labelstudio
    # didn't do the `if tog_job_id:` to have backward compatability
    # with tanmay's `eval_xlmr_pipeline`
    if labelstudio_project_id:
        pass
    else:
        train_df[INTENT_Y] = train_df.tag.apply(pick_1st_tag)
        logger.debug(train_df.intent_y[:10])
    
    train_df.to_csv(output_path, index=False)


create_true_intent_labels_op = kfp.components.create_component_from_func(
    create_intent_labels, base_image=pipeline_constants.BASE_IMAGE
)
