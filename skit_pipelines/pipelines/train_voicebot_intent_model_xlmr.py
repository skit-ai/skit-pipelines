import kfp
import json

from skit_pipelines import constants as pipeline_constants
from skit_pipelines.components import (
    create_features_op,
    create_true_intent_labels_op,
    create_utterances_op,
    download_from_s3_op,
    train_voicebot_xlmr_op,
    upload2s3_op,
)


UTTERANCES = pipeline_constants.UTTERANCES
INTENT_Y = pipeline_constants.INTENT_Y
BUCKET = pipeline_constants.BUCKET


@kfp.dsl.pipeline(
    name="XLMR Voicebot Training Pipeline",
    description="Trains an XLM Roberta model on given dataset.",
)
def train_voicebot_intent_model_xlmr(*,
    s3_path: str = "",
    dataset_path: str = "",
    model_path: str,
    storage_options: str = "",
    org_id: str = "",
    classifier_type: str = "xlmr",
    use_state: bool = False,
    model_type: str = "xlmroberta",
    model_name: str = "xlm-roberta-base",
    num_train_epochs: int = 10,
    use_early_stopping: bool = False,
    early_stopping_patience: int = 3,
    early_stopping_delta: float = 0,
    max_seq_length: int = 128,
    learning_rate: float = 4e-5,
):
    with kfp.dsl.Condition(s3_path != "", "s3_path_check") as check1:
        tagged_data_op = download_from_s3_op(storage_path=s3_path)
    
    with kfp.dsl.Condition(dataset_path != "", "dataset_path_check") as check2:
        tagged_data_op = download_from_s3_op(storage_path=dataset_path, storage_options=storage_options)

    # preprocess the file

    # Create true label column
    preprocess_data_op = create_utterances_op(tagged_data_op.outputs["output"]).after(check1, check2)

    # Create utterance column
    preprocess_data_op = create_true_intent_labels_op(
        preprocess_data_op.outputs["output"]
    )

    #TODO: Create train and test splits - keep only valid utterances

    # Normalize utterance column
    preprocess_data_op = create_features_op(
        preprocess_data_op.outputs["output"], use_state
    )

    train_op = train_voicebot_xlmr_op(
        preprocess_data_op.outputs["output"],
        utterance_column=UTTERANCES,
        label_column=INTENT_Y,
        model_type=model_type,
        model_name=model_name,
        num_train_epochs=num_train_epochs,
        use_early_stopping=use_early_stopping,
        early_stopping_patience=early_stopping_patience,
        early_stopping_delta=early_stopping_delta,
        max_seq_length=max_seq_length,
        learning_rate=learning_rate,
    )
    # produce test set metrics.
    train_op.set_gpu_limit(1)
    upload = upload2s3_op(
        train_op.outputs["model"],
        org_id,
        "intent_classifier_xlmr",
        BUCKET,
        output_path=model_path,
        storage_options=storage_options
    )
    upload.execution_options.caching_strategy.max_cache_staleness = (
        "P0D"  # disables caching
    )