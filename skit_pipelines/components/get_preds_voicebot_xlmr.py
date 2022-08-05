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
    max_seq_length: int = 128,
    confidence_threshold: float = 0.1,
):

    import os
    import pickle
    import tarfile
    import tempfile

    import numpy as np
    import pandas as pd
    from loguru import logger
    from simpletransformers.classification import (
        ClassificationArgs,
        ClassificationModel,
    )
    from sklearn.preprocessing import LabelEncoder

    df = pd.read_csv(data_path)
    temp_model_path = tempfile.mkdtemp()

    logger.debug(
        f"Extracting .tgz archive {model_path} to output_path {temp_model_path}."
    )
    tar = tarfile.open(model_path)
    tar.extractall(path=temp_model_path)
    tar.close()
    logger.debug(f"Extracted successfully.")

    model_path = os.path.join(temp_model_path, "data")

    encoder: LabelEncoder = pickle.load(
        open(os.path.join(model_path, "labelencoder.pkl"), "rb")
    )
    model_args = ClassificationArgs(
        output_dir=None,
        reprocess_input_data=True,
        use_multiprocessing_for_evaluation=False,
        use_multiprocessing=False,
        eval_batch_size=20,
        thread_count=1,
        silent=False,
    )

    model = ClassificationModel("xlmroberta", model_path, args=model_args)

    logger.debug(f"starting predict on {df.shape[0]} rows:")
    logger.debug(df[utterance_column].iloc[:5])
    df["text"] = df.utterances
    df["labels"] = encoder.transform(df.intent_y)
    logger.debug(df.columns)

    _, preds, err = model.eval_model(df, output_dir="/tmp")
    encoded_labels = np.argmax(preds, axis=1)
    df["intent_x"] = encoder.inverse_transform(encoded_labels)

    logger.debug(f"completed predict on {df.shape[0]} rows.")

    df.to_csv(
        output_path,
    )


get_preds_voicebot_xlmr_op = kfp.components.create_component_from_func(
    get_preds_voicebot_xlmr, base_image=pipeline_constants.BASE_IMAGE
)
