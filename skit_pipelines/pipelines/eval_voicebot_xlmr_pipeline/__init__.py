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
    true_label_column: str = "intent_y",
    pred_label_column: str = "raw.intent",
    slack_thread: str = "",
):
    """
    Evaluates an XLM Roberta model on given dataset.

    .. _p_eval_voicebot_xlmr_pipeline:

    Example payload to invoke this pipeline via slack integrations:

        @charon run eval_voicebot_xlmr_pipeline

        .. code-block:: python

            {
                "s3_path_data": "s3://bucket-name/data/",
                "s3_path_model": "s3://bucket-name/model/",
                "org_id": "org",
                "use_state": False
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
    :param slack_thread: The slack thread to send the notification, defaults to ""
    :type slack_thread: str, optional
    """
    tagged_data_op = download_from_s3_op(storage_path=s3_path_data)

    # Create true label column
    preprocess_data_op = create_utterances_op(tagged_data_op.outputs["output"]).after(
        tagged_data_op
    )

    # Create utterance column
    preprocess_data_op = create_true_intent_labels_op(
        preprocess_data_op.outputs["output"]
    )

    # Normalize utterance column
    preprocess_data_op = create_features_op(
        preprocess_data_op.outputs["output"], use_state=use_state, mode="test"
    )

    with kfp.dsl.Condition(s3_path_model != "", "model_present") as model_present:
        loaded_model_op = download_from_s3_op(storage_path=s3_path_model)
        # get predictions from the model
        pred_op = get_preds_voicebot_xlmr_op(
            preprocess_data_op.outputs["output"],
            loaded_model_op.outputs["output"],
            utterance_column=UTTERANCES,
            output_pred_label_column=INTENT,
        )
        pred_op.set_gpu_limit(1)
        with_model_irr_op = gen_irr_metrics_op(
            pred_op.outputs["output"],
            true_label_column=true_label_column,
            pred_label_column=pred_label_column,
        )
        with_model_confusion_matrix_op = gen_confusion_matrix_op(
            pred_op.outputs["output"],
            true_label_column=true_label_column,
            pred_label_column=pred_label_column,
        )

        # produce test set metrics.
        upload_irr = upload2s3_op(
            path_on_disk=with_model_irr_op.outputs["output"],
            reference=org_id,
            file_type="xlmr-irr-metrics",
            bucket=BUCKET,
            ext=".csv",
        )
        upload_irr.execution_options.caching_strategy.max_cache_staleness = (
            "P0D"  # disables caching
        )
        upload_cm = upload2s3_op(
            path_on_disk=with_model_confusion_matrix_op.outputs["output"],
            reference=org_id,
            file_type="xlmr-confusion-matrix",
            bucket=BUCKET,
            ext=".csv",
        )
        upload_cm.execution_options.caching_strategy.max_cache_staleness = (
            "P0D"  # disables caching
        )

        with kfp.dsl.Condition(notify != "", "notify").after(upload_irr) as irr_check:
            notification_text = f"Here's the IRR report."
            code_block = f"aws s3 cp {upload_irr.output} ."
            irr_notif = slack_notification_op(
                notification_text,
                channel=channel,
                cc=notify,
                code_block=code_block,
                thread_id=slack_thread,
            )
            irr_notif.execution_options.caching_strategy.max_cache_staleness = (
                "P0D"  # disables caching
            )

        with kfp.dsl.Condition(notify != "", "notify").after(upload_cm) as cm_check:
            notification_text = f"Here's the confusion matrix."
            code_block = f"aws s3 cp {upload_cm.output} ."
            cm_notif = slack_notification_op(
                notification_text,
                channel=channel,
                cc=notify,
                code_block=code_block,
                thread_id=slack_thread,
            )
            cm_notif.execution_options.caching_strategy.max_cache_staleness = (
                "P0D"  # disables caching
            )

    with kfp.dsl.Condition(s3_path_model == "", "model_missing") as model_missing:
        irr_op = gen_irr_metrics_op(
            preprocess_data_op.outputs["output"],
            true_label_column=true_label_column,
            pred_label_column=pred_label_column,
        )
        confusion_matrix_op = gen_confusion_matrix_op(
            preprocess_data_op.outputs["output"],
            true_label_column=true_label_column,
            pred_label_column=pred_label_column,
        )

        # produce test set metrics.
        upload_irr = upload2s3_op(
            path_on_disk=irr_op.outputs["output"],
            reference=org_id,
            file_type="xlmr-irr-metrics",
            bucket=BUCKET,
            ext=".csv",
        )
        upload_irr.execution_options.caching_strategy.max_cache_staleness = (
            "P0D"  # disables caching
        )
        upload_cm = upload2s3_op(
            path_on_disk=confusion_matrix_op.outputs["output"],
            reference=org_id,
            file_type="xlmr-confusion-matrix",
            bucket=BUCKET,
            ext=".csv",
        )
        upload_cm.execution_options.caching_strategy.max_cache_staleness = (
            "P0D"  # disables caching
        )

        with kfp.dsl.Condition(notify != "", "notify").after(upload_irr) as irr_check:
            notification_text = f"Here's the IRR report."
            code_block = f"aws s3 cp {upload_irr.output} ."
            irr_notif = slack_notification_op(
                notification_text,
                channel=channel,
                cc=notify,
                code_block=code_block,
                thread_id=slack_thread,
            )
            irr_notif.execution_options.caching_strategy.max_cache_staleness = (
                "P0D"  # disables caching
            )

        with kfp.dsl.Condition(notify != "", "notify").after(upload_cm) as cm_check:
            notification_text = f"Here's the confusion matrix."
            code_block = f"aws s3 cp {upload_cm.output} ."
            cm_notif = slack_notification_op(
                notification_text,
                channel=channel,
                cc=notify,
                code_block=code_block,
                thread_id=slack_thread,
            )
            cm_notif.execution_options.caching_strategy.max_cache_staleness = (
                "P0D"  # disables caching
            )


__all__ = ["eval_voicebot_xlmr_pipeline"]
