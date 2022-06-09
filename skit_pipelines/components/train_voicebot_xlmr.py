import kfp
from kfp.components import InputPath, OutputPath

from skit_pipelines import constants as pipeline_constants


def train_voicebot_xlmr(
    data_path: InputPath(str),
    model_path: OutputPath(str),
    label_column: str = "intent_y",
    utterance_column: str = "utterances",
    model_type: str = "xlmroberta",
    model_name: str = "xlm-roberta-base",
    num_train_epochs: int = 10,
    early_stopping_patience: int = 3,
    use_early_stopping: bool = False,
    early_stopping_delta: float = 0,
    max_seq_length: int = 128,
    learning_rate: float = 4e-5,
):
    """
    .. warning:: This component runs in a python 3.8 environment.

    :param data_path: Path to load training dataset.
    :type data_path: InputPath
    :param model_path: Path to save trained model.
    :type model_path: OutputPath
    :param label_column: Column where intents are present, defaults to "intent_y"
    :type label_column: str, optional
    :param utterance_column: Column where ASR utterances are present, defaults to "utterances"
    :type utterance_column: str, optional
    :param model_type: BERT model type, defaults to "xlmroberta"
    :type model_type: str, optional
    :param model_name: BERT model subtype, defaults to "xlm-roberta-base"
    :type model_name: str, optional
    :param num_train_epochs: Number of epochs to train on, defaults to 10
    :type num_train_epochs: int, optional
    :param early_stopping_patience: Consecutive number of times early stopping threshold should be met, defaults to 3
    :type early_stopping_patience: int, optional
    :param use_early_stopping: Use early stopping to stop training if loss delta is stagnant, defaults to False
    :type use_early_stopping: bool, optional
    :param early_stopping_delta: The difference between losses, defaults to 0
    :type early_stopping_delta: float, optional
    :param max_seq_length: Truncate input after these many characters, defaults to 128
    :type max_seq_length: int, optional
    :param learning_rate: Weight update parameter, defaults to 4e-5
    :type learning_rate: float, optional
    """
    import os
    import pickle

    import pandas as pd
    from loguru import logger
    from simpletransformers.classification import (
        ClassificationArgs,
        ClassificationModel,
    )
    from sklearn import preprocessing

    from skit_pipelines import constants as pipeline_constants

    train_df = pd.read_csv(data_path)
    labelencoder = preprocessing.LabelEncoder()
    labelencoder_file_path = os.path.join(model_path, "labelencoder.pkl")
    encoder = labelencoder.fit(train_df[label_column])
    model_args = ClassificationArgs(
        num_train_epochs=num_train_epochs,
        save_best_model=True,
        use_multiprocessing=False,
        max_seq_length=max_seq_length,
        output_dir=model_path,
        best_model_dir=f"{model_path}/best",
        overwrite_output_dir=True,
        save_eval_checkpoints=False,
        save_model_every_epoch=False,
        use_early_stopping=use_early_stopping,
        early_stopping_patience=early_stopping_patience,
        early_stopping_delta=early_stopping_delta,
        learning_rate=learning_rate,
    )

    train_df[pipeline_constants.LABELS] = encoder.transform(train_df[label_column])
    train_df.rename(
        columns={
            utterance_column: pipeline_constants.TEXT,
        },
        inplace=True,
    )
    model = ClassificationModel(
        model_type,
        model_name,
        num_labels=train_df[label_column].nunique(),
        args=model_args,
    )
    train_df = train_df[[pipeline_constants.TEXT, pipeline_constants.LABELS]]
    logger.debug(train_df.head())
    model.train_model(train_df)
    with open(labelencoder_file_path, "wb") as file:
        _ = pickle.dump(labelencoder, file)


train_voicebot_xlmr_op = kfp.components.create_component_from_func(
    train_voicebot_xlmr, base_image=pipeline_constants.CUDA_P38_IMAGE
)
