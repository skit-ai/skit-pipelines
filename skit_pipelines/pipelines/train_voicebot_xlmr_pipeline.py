import kfp

from skit_pipelines import constants as pipeline_constants
from skit_pipelines.components import (
    fetch_tagged_dataset_op,
    download_from_s3_op,
    train_xlmr_voicebot_op,
    create_features_op,
    create_utterances_op,
    create_true_intent_labels_op
)


UTTERANCES = pipeline_constants.UTTERANCES
INTENT_Y = pipeline_constants.INTENT_Y


@kfp.dsl.pipeline(
    name="Fetch Tagged Dataset Pipeline",
    description="fetches tagged dataset from tog with respective arguments",
)
def run_fetch_tagged_dataset(
    job_id: int,
    task_type: str,
    timezone: str,
    start_date: str,
    end_date: str,
    s3_path: str,
    use_state: bool = True,
    model_type: str = "xlmroberta",
    model_name: str = "xlm-roberta-base",
):
    df = download_from_s3_op(s3_path)

    # preprocess the file

    # Create true label column
    df = create_utterances_op(df.outputs["output"])

    # Create utterance column
    df = create_utterances_op(df.outputs["output"])

    # Create train and test splits

    # Normalize utterance column
    df = create_features_op(df.outputs["output"], use_state)
 
    # train model
    train_xlmr_voicebot_op(
        df.outputs["output"],
        utterance_column=UTTERANCES,
        label_column=INTENT_Y,
        model_type=model_type,
        model_name=model_name
    )
    # produce test set metrics.
