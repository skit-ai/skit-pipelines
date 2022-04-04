import kfp

from skit_pipelines import constants as pipeline_constants
from skit_pipelines.components import (
    create_features_op,
    create_true_intent_labels_op,
    create_utterances_op,
    download_from_s3_op,
    fetch_tagged_dataset_op,
    train_xlmr_voicebot_op,
)

UTTERANCES = pipeline_constants.UTTERANCES
INTENT_Y = pipeline_constants.INTENT_Y


@kfp.dsl.pipeline(
    name="Fetch Tagged Dataset Pipeline",
    description="fetches tagged dataset from tog with respective arguments",
)
def run_fetch_tagged_dataset(
    s3_path: str,
    use_state: bool = True,
    model_type: str = "xlmroberta",
    model_name: str = "xlm-roberta-base",
):
    tagged_data_op = download_from_s3_op(s3_path)
    # preprocess the file

    # Create true label column
    preprocess_data_op = create_utterances_op(tagged_data_op.outputs["output"])

    # Create utterance column
    preprocess_data_op = create_true_intent_labels_op(preprocess_data_op.outputs["output"])

    # Create train and test splits

    # Normalize utterance column
    preprocess_data_op = create_features_op(preprocess_data_op.outputs["output"], use_state)

    train_op = train_xlmr_voicebot_op(
        preprocess_data_op.outputs["output"],
        utterance_column=UTTERANCES,
        label_column=INTENT_Y,
        model_type=model_type,
        model_name=model_name,
    )
    # produce test set metrics.
    train_op.set_gpu_limit(1)
