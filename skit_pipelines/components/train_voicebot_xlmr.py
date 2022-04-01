import kfp
from kfp.components import InputPath
from skit_pipelines import constants as pipeline_constants


def train_xlmr_voicebot(
    data_path: InputPath,
    utterance_column: str,
    label_column: str,
    model_type: str = "xlmroberta",
    model_name: str = "xlm-roberta-base",
):
    import pandas as pd
    from simpletransformers.classification import (
        ClassificationArgs,
        ClassificationModel,
    )
    from sklearn import preprocessing
    from skit_pipelines import constants as pipeline_constants

    label_column = pipeline_constants.VOICE_BOT_XLMR_LABEL_COL
    train_df = pd.read_csv(data_path)
    labelencoder = preprocessing.LabelEncoder()
    encoder = labelencoder.fit(train_df[label_column])
    model_args = ClassificationArgs(num_train_epochs=1)

    train_df[:, label_column] = encoder.transform(train_df[label_column])
    train_df.rename(
        columns={utterance_column: pipeline_constants.TEXT, label_column: pipeline_constants.LABELS},
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
