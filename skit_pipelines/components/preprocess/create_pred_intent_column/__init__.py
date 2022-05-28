import kfp
from kfp.components import InputPath, OutputPath

from skit_pipelines import constants as pipeline_constants


def create_pred_intent_labels(data_path: InputPath(str), output_path: OutputPath(str)):
    import pandas as pd
    from loguru import logger

    from skit_pipelines import constants as pipeline_constants
    from skit_pipelines.components.preprocess.create_pred_intent_column.utils import (
        extract_prediction_from_data,
    )

    INTENT = pipeline_constants.INTENT

    train_df = pd.read_csv(data_path)
    train_df[INTENT] = train_df.data.apply(extract_prediction_from_data)
    logger.debug(train_df[INTENT][:10])
    logger.debug(f"successfully extracted {train_df[INTENT].isnull().sum()}/{train_df[INTENT].shape[0]} predicted intents from the data column.")

    train_df.to_csv(output_path, index=False)


create_pred_intent_labels_op = kfp.components.create_component_from_func(
    create_pred_intent_labels, base_image=pipeline_constants.BASE_IMAGE
)
