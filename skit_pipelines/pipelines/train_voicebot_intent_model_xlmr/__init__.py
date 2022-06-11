import kfp

from skit_pipelines import constants as pipeline_constants
from skit_pipelines.components import (
    create_features_op,
    create_true_intent_labels_op,
    create_utterances_op,
    download_from_s3_op,
    slack_notification_op,
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
def train_voicebot_intent_model_xlmr(
    *,
    dataset_path: str,
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
    notify: str = "",
    channel: str = "",
    slack_thread: float = 0,
):
    """
    A pipeline to train an XLMR model on given dataset.

    .. _p_train_voicebot_intent_model_xlmr:

    Example payload to invoke via slack integrations:

        @charon run train_voicebot_intent_model_xlmr

        .. code-block:: json

            {
                "model_path": "s3://bucket-name/model/",
                "dataset_path": "s3://bucket-name/path/to/data.csv",
                "org_id": "org",
                "use_state": false,
                "num_train_epochs": 10,
                "max_seq_length": 128,
                "learning_rate": 4e-5
            }

    We use the following payload to use via studio.

        @charon run train_voicebot_intent_model_xlmr

        .. code-block:: json

            {
                "model_path": "s3://bucket-name/model/",
                "dataset_path": "path/to/data.csv",
                "storage_options": "{\\"type\\": \\"s3\\", \\"bucket\\": \\"bucket-name\\"}",
                "org_id": "org",
                "classifier_type": "xlmr",
                "use_state": false,
                "num_train_epochs": 10,
                "max_seq_length": 128,
                "learning_rate": 4e-05,
                "notify": "@person, @personwith.spacedname",
                "channel": "#some-public-channel"
            }


    :param model_path: Save path for the trained model.
    :type model_path: str
    :param dataset_path: The S3 URI or the S3 key for the tagged dataset.
    :type dataset_path: str
    :param storage_options: A json string that specifies the bucket and key, defaults to ""
    :type storage_options: str, optional
    :param org_id: reference path to save the metrics.
    :type org_id: str, optional
    :param classifier_type: One of XLMR and MLP, defaults to "xlmr"
    :type classifier_type: str, optional
    :param use_state: Train the model using state as a feature, defaults to False
    :type use_state: bool, optional
    :param model_type: The BERT model type, defaults to "xlmroberta"
    :type model_type: str, optional
    :param model_name: The BERT model sub type, defaults to "xlm-roberta-base"
    :type model_name: str, optional
    :param num_train_epochs: Number of epchs to train the model, defaults to 10
    :type num_train_epochs: int, optional
    :param use_early_stopping: If the loss threshold is below an expected value, setting this to true will stop the training, defaults to False
    :type use_early_stopping: bool, optional
    :param early_stopping_patience: Number of iterations for which the loss must be less than expected value, defaults to 3
    :type early_stopping_patience: int, optional
    :param early_stopping_delta: The diff between expected and actual loss that triggers early stopping, defaults to 0
    :type early_stopping_delta: float, optional
    :param max_seq_length: Truncate an input after these many characters, defaults to 128
    :type max_seq_length: int, optional
    :param learning_rate: A multiplier to control weight updates, defaults to 4e-5
    :type learning_rate: float,
    :param notify: Whether to send a slack notification, defaults to ""
    :type notify: str, optional
    :param channel: The slack channel to send the notification, defaults to ""
    :type channel: str, optional
    :param slack_thread: The slack thread to send the notification, defaults to ""
    :type slack_thread: float, optional
    """
    tagged_data_op = download_from_s3_op(
        storage_path=dataset_path, storage_options=storage_options
    )

    # preprocess the file

    # Create true label column
    preprocess_data_op = create_utterances_op(tagged_data_op.outputs["output"])

    # Create utterance column
    preprocess_data_op = create_true_intent_labels_op(
        preprocess_data_op.outputs["output"]
    )

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
        path_on_disk=train_op.outputs["model"],
        reference=org_id,
        file_type="intent_classifier_xlmr",
        bucket=BUCKET,
        output_path=model_path,
        storage_options=storage_options,
    )
    upload.execution_options.caching_strategy.max_cache_staleness = (
        "P0D"  # disables caching
    )
    notification_text = f"An {model_type} model is trained. Download binaries:"
    with kfp.dsl.Condition(notify != "", "notify").after(upload) as check1:
        code_block = f"aws s3 cp {upload.output} ."
        task_no_cache = slack_notification_op(
            notification_text,
            channel=channel,
            cc=notify,
            code_block=code_block,
            thread_id=slack_thread,
        )
        task_no_cache.execution_options.caching_strategy.max_cache_staleness = (
            "P0D"  # disables caching
        )


__all__ = ["train_voicebot_intent_model_xlmr"]
