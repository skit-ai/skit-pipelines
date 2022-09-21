import kfp
from kfp.components import InputPath, OutputPath

from skit_pipelines import constants as pipeline_constants


def create_intent_labels(
    data_path: InputPath(str), 
    output_path: OutputPath(str),
    ):
    import pandas as pd
    from loguru import logger

    from skit_pipelines import constants as pipeline_constants
    from skit_pipelines.components.preprocess.create_true_intent_column.utils import (
        pick_1st_tag,
    )

    INTENT_Y = pipeline_constants.INTENT_Y

    train_df = pd.read_csv(data_path)
    train_df[INTENT_Y] = train_df.tag.apply(pick_1st_tag)
    logger.debug(train_df.intent_y[:10])
    
    train_df.to_csv(output_path, index=False)


create_true_intent_labels_op = kfp.components.create_component_from_func(
    create_intent_labels, base_image=pipeline_constants.BASE_IMAGE
)


if __name__ == "__main__":

    create_intent_labels("87.csv", "bleh.csv")