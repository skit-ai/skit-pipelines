import kfp
from kfp.components import InputPath, OutputPath

from skit_pipelines import constants as pipeline_constants


def create_true_transcript_labels(
    data_path: InputPath(str), true_label_column: str, output_path: OutputPath(str)
):
    import pandas as pd
    from loguru import logger

    from skit_pipelines import constants as pipeline_constants
    from skit_pipelines.components.preprocess.create_true_transcript_column.utils import (
        pick_text_from_tag,
    )

    train_df = pd.read_csv(data_path)
    train_df[true_label_column] = train_df.tag.apply(pick_text_from_tag)
    logger.debug(f"created new column: ({true_label_column})")
    logger.debug(train_df[true_label_column][:10])

    train_df.to_csv(output_path, index=False)


create_true_transcript_labels_op = kfp.components.create_component_from_func(
    create_true_transcript_labels, base_image=pipeline_constants.BASE_IMAGE
)
