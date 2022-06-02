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
    import os
    import pickle
    from collections.abc import Iterable

    import pandas as pd
    from loguru import logger

    setattr(collections, "Iterable", Iterable)
    # ----------------------------------------------
    import shutil
    import tarfile

    from simpletransformers.classification import (
        ClassificationArgs,
        ClassificationModel,
    )
    from sklearn import preprocessing
    from tqdm import trange

    from skit_pipelines import constants as pipeline_constants

    pred_df = pd.read_csv(data_path)

    logger.debug(f"Extracting .tgz archive {model_path} to output_path {output_path}.")
    tar = tarfile.open(model_path)
    tar.extractall(path=output_path)
    tar.close()
    logger.debug(f"Extracted successfully.")

    model_path = os.path.join(output_path, "data")

    encoder = pickle.load(open(os.path.join(model_path, "labelencoder.pkl"), "rb"))

    model = ClassificationModel("xlmroberta", model_path)

    # model_path is no longer required, remove it from inside of output_path. also remove the output_path as we will write the output csv to it
    shutil.rmtree(output_path)

    logger.debug(f"starting predict on {pred_df.shape[0]} rows:")
    logger.debug(pred_df[utterance_column].iloc[:5])

    utterances_l = pred_df[utterance_column].tolist()
    predictions_l = []
    batch_size = 16
    for i in range(0, len(utterances_l), batch_size):
        batch = utterances_l[i : i + batch_size]
        predictions, _ = model.predict(batch)
        predictions_l.extend(predictions)

    logger.debug(f"completed predict on {pred_df.shape[0]} rows.")

    pred_df[output_pred_label_column] = encoder.inverse_transform(predictions_l)
    pred_df.to_csv(output_path)


get_preds_voicebot_xlmr_op = kfp.components.create_component_from_func(
    get_preds_voicebot_xlmr, base_image=pipeline_constants.BASE_IMAGE
)
