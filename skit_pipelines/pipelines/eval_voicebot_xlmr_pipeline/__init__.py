import os

import kfp

from skit_pipelines import constants as pipeline_constants
from skit_pipelines.components import (
    create_features_op,
    create_true_intent_labels_op,
    create_utterances_op,
    download_from_s3_op,
    gen_confusion_matrix_op,
    gen_irr_metrics_op,
    get_preds_voicebot_xlmr_op,
    slack_notification_op,
    upload2s3_op,
)

UTTERANCES = pipeline_constants.UTTERANCES
INTENT_Y = pipeline_constants.INTENT_Y
BUCKET = pipeline_constants.BUCKET
INTENT = pipeline_constants.INTENT


@kfp.dsl.pipeline(
    name="XLMR Voicebot Eval Pipeline",
    description="Produces intent metrics for an XLM Roberta model on given dataset.",
)
def eval_voicebot_xlmr_pipeline(
    *,
    s3_path_data: str,
    org_id: str,
    use_state: bool = True,
    model_name: str = "xlm-roberta-base",
    s3_path_model: str = "",
    notify: str = "",
    channel: str = "",
):
    """
    Evaluates an XLM Roberta model on given dataset.

    .. _p_eval_voicebot_xlmr_pipeline:

    Example payload to invoke this pipeline via slack integrations:

        @charon run eval_voicebot_xlmr_pipeline

        .. code-block:: json

            {
                "s3_path_data": "s3://bucket-name/data/",
                "s3_path_model": "s3://bucket-name/model/",
                "org_id": "org",
                "use_state": false,
                "notify": "@person, @personwith.spacedname",
                "channel": "#some-public-channel"
            }

    :param s3_path_data: S3 path to a tagged dataset (.csv).
    :type s3_path_data: str
    :param s3_path_model: S3 path to a trained model. Optional.
    :type s3_path_model: str
    :param org_id: reference path to save the metrics.
    :type org_id: str
    :param use_state: Use the XLMR model with state encoding?, defaults to True
    :type use_state: bool, optional
    :param model_name: The flavour of the BERT model, defaults to "xlm-roberta-base"
    :type model_name: str, optional
    :param channel: The slack channel to send the notification, defaults to ""
    :type channel: str, optional
    """
    with kfp.dsl.Condition(s3_path_data != "", "s3_path_data_check") as check1:
        tagged_data_op = download_from_s3_op(storage_path=s3_path_data)

    with kfp.dsl.Condition(s3_path_model != "", "s3_path_model_check") as check2:
        loaded_model_op = download_from_s3_op(storage_path=s3_path_model)

    # Create true label column
    preprocess_data_op = create_utterances_op(tagged_data_op.outputs["output"]).after(
        check1
    )

    # Create utterance column
    preprocess_data_op = create_true_intent_labels_op(
        preprocess_data_op.outputs["output"]
    )

    # Normalize utterance column
    preprocess_data_op = create_features_op(
        preprocess_data_op.outputs["output"], use_state
    )

    # get predictions from the model
    # TODO: make s3_path_model optional, without which predictions already present in the csv to be used.
    pred_op = get_preds_voicebot_xlmr_op(
        preprocess_data_op.outputs["output"],
        loaded_model_op.outputs["output"],
        utterance_column=UTTERANCES,
        output_pred_label_column=INTENT,
    )

    pred_op.set_gpu_limit(1)

    irr_op = gen_irr_metrics_op(
        pred_op.outputs["output"],
        true_label_column=INTENT_Y,
        pred_label_column=INTENT,
    )

    # produce test set metrics.
    upload_irr = upload2s3_op(
        irr_op.outputs["output"], org_id, "xlmr-irr-metrics", BUCKET, ".txt"
    )
    upload_irr.execution_options.caching_strategy.max_cache_staleness = (
        "P0D"  # disables caching
    )

    with kfp.dsl.Condition(notify != "", "notify").after(upload_irr) as irr_check:
        notification_text = f"Here's the IRR report."
        irr_notif = slack_notification_op(
            notification_text, channel=channel, cc=notify, s3_path=upload_irr.output
        )
        irr_notif.execution_options.caching_strategy.max_cache_staleness = (
            "P0D"  # disables caching
        )

    confusion_matrix_op = gen_confusion_matrix_op(
        pred_op.outputs["output"],
        true_label_column=INTENT_Y,
        pred_label_column=INTENT,
    )

    upload_cm = upload2s3_op(
        confusion_matrix_op.outputs["output"],
        org_id,
        "xlmr-confusion-matrix",
        BUCKET,
        ".txt",
    )
    upload_cm.execution_options.caching_strategy.max_cache_staleness = (
        "P0D"  # disables caching
    )

    with kfp.dsl.Condition(notify != "", "notify").after(upload_cm) as cm_check:
        notification_text = f"Here's the confusion matrix."
        cm_notif = slack_notification_op(
            notification_text, channel=channel, cc=notify, s3_path=upload_irr.output
        )
        cm_notif.execution_options.caching_strategy.max_cache_staleness = (
            "P0D"  # disables caching
        )


__all__ = ["eval_voicebot_xlmr_pipeline"]
