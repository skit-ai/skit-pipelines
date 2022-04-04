import kfp
from kfp.components import InputPath, OutputPath

from skit_pipelines import constants as pipeline_constants


def train_xlmr_voicebot(
    data_path: InputPath(str),
    model_path: OutputPath(str),
    utterance_column: str,
    label_column: str,
    model_type: str = "xlmroberta",
    model_name: str = "xlm-roberta-base",
    num_train_epochs: int = 1,
    use_early_stopping: bool = False,
    early_stopping_patience: int = 3,
    early_stopping_delta: float = 0,
    max_seq_length: int = 128
):
    # HACK: This code should go as soon as this issue is fixed:
    # https://github.com/ThilinaRajapakse/simpletransformers/issues/1386
    import collections
    from collections.abc import Iterable

    import pandas as pd

    setattr(collections, "Iterable", Iterable)
    # ----------------------------------------------
    from simpletransformers.classification import (
        ClassificationArgs,
        ClassificationModel,
    )
    from sklearn import preprocessing

    from skit_pipelines import constants as pipeline_constants

    train_df = pd.read_csv(data_path)
    labelencoder = preprocessing.LabelEncoder()
    encoder = labelencoder.fit(train_df[label_column])
    model_args = ClassificationArgs(
        num_train_epochs=num_train_epochs,
        save_best_model=True,
        use_multiprocessing=False,
        max_seq_length=max_seq_length,
        output_dir=model_path,
        best_model_dir=f"{model_path}/best",
        overwrite_output_dir=True,
        use_early_stopping=use_early_stopping,
        early_stopping_patience=early_stopping_patience,
        early_stopping_delta=early_stopping_delta,
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
    model.train_model(train_df)


train_xlmr_voicebot_op = kfp.components.create_component_from_func(
    train_xlmr_voicebot, base_image=pipeline_constants.BASE_IMAGE
)
