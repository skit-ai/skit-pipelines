import kfp
from kfp.components import InputPath, OutputPath

from skit_pipelines import constants as pipeline_constants


def get_preds_voicebot_xlmr(
    data_path: InputPath(str),
    model_path: InputPath(str),
    output_path: OutputPath(str),
    utterance_column: str,
    input_true_label_column: str,
    output_pred_label_column: str,
    model_type: str = "xlmroberta",
    # max_seq_length: int = 128,
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

    pred_df = pd.read_csv(data_path)

    labelencoder = pickle.load(open(os.path.join(model_path,"labelencoder.pkl"),"rb"))

    model = ClassificationModel('xlmroberta',model_path)

    pred_df[pipeline_constants.LABELS] = encoder.transform(pred_df[true_label_column])
    pred_df.rename(
        columns={
            utterance_column: pipeline_constants.TEXT,
        },
        inplace=True,
    )

    result, model_outputs, wrong_predictions = model.eval_model(pred_df)
    pred_df[pred_label_column] = labelencoder.inverse_transform(model_outputs)
    pred_df.to_csv(output_path)



get_preds_voicebot_xlmr_op = kfp.components.create_component_from_func(
    get_preds_voicebot_xlmr, base_image=pipeline_constants.BASE_IMAGE
)
