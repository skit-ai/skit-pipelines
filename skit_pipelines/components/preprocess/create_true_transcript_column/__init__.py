import kfp
from kfp.components import InputPath, OutputPath

from skit_pipelines import constants as pipeline_constants


def create_true_transcript_labels(
    data_path: InputPath(str), output_path: OutputPath(str)
):
    import pandas as pd
    from loguru import logger

    from skit_pipelines import constants as pipeline_constants
    from skit_pipelines.components.preprocess.create_true_transcript_column.utils import (
        pick_text_from_tag,
    )

    TRANSCRIPT_Y = pipeline_constants.TRANSCRIPT_Y

    train_df = pd.read_csv(data_path)
    train_df[TRANSCRIPT_Y] = train_df.tag.apply(pick_text_from_tag)
    logger.debug(f"created new column: ({TRANSCRIPT_Y})")
    logger.debug(train_df[TRANSCRIPT_Y][:10])

    train_df.to_csv(output_path, index=False)


create_true_transcript_labels_op = kfp.components.create_component_from_func(
    create_true_transcript_labels, base_image=pipeline_constants.BASE_IMAGE
)
