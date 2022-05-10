import kfp
from kfp.components import InputPath, OutputPath

from skit_pipelines import constants as pipeline_constants


def get_preds_voicebot_xlmr(
    data_path: InputPath(str),
    model_path: InputPath(str),
    output_path: OutputPath(str),
    utterance_column: str,
    output_pred_label_column: str,
    model_type: str = "xlmroberta",
    # max_seq_length: int = 128,
):

    # HACK: This code should go as soon as this issue is fixed:
    # https://github.com/ThilinaRajapakse/simpletransformers/issues/1386
    import collections
    from collections.abc import Iterable

    from loguru import logger

    import os
    import pandas as pd
    import pickle

    setattr(collections, "Iterable", Iterable)
    # ----------------------------------------------
    from simpletransformers.classification import (
        ClassificationArgs,
        ClassificationModel,
    )
    from sklearn import preprocessing

    from skit_pipelines import constants as pipeline_constants

    pred_df = pd.read_csv(data_path)

    model_path = os.path.join(model_path,"data")

    encoder = pickle.load(open(os.path.join(model_path,"labelencoder.pkl"),"rb"))

    model = ClassificationModel('xlmroberta',model_path)

    logger.debug(f"starting predict on {pred_df.shape[0]} rows.")
    predictions, raw_outputs = model.predict(pred_df[utterance_column].tolist(),multi_label=True)
    logger.debug(f"completed predict on {pred_df.shape[0]} rows.")

    pred_df[output_pred_label_column] = encoder.inverse_transform(predictions)
    pred_df.to_csv(output_path)



get_preds_voicebot_xlmr_op = kfp.components.create_component_from_func(
    get_preds_voicebot_xlmr, base_image=pipeline_constants.BASE_IMAGE
)
