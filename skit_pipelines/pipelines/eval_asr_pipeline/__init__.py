import kfp

from skit_pipelines import constants as pipeline_constants
from skit_pipelines.components import (
    create_true_transcript_labels_op,
    create_utterances_op,
    download_csv_from_s3_op,
    gen_asr_metrics_op,
    process_true_transcript_labels_op,
    slack_notification_op,
    upload2s3_op,
)

UTTERANCES = pipeline_constants.UTTERANCES
TRANSCRIPT_Y = pipeline_constants.TRANSCRIPT_Y
BUCKET = pipeline_constants.BUCKET
INTENT = pipeline_constants.INTENT


@kfp.dsl.pipeline(
    name="ASR Transcription vs Transcription tags Eval Pipeline",
    description="Produces asr metrics for the transcriptions present against transcription tags.",
)
def eval_asr_pipeline(
    *,
    s3_path_data: str,
    org_id: str,
    notify: str = "",
    channel: str = "",
    true_label_column: str = "transcript_y",
    pred_label_column: str = "utterances",
    slack_thread: str = "",
):
    """
    Evaluates ASR transcriptions using transcription tags.

    .. _p_eval_asr_pipeline:

    Example payload to invoke this pipeline via slack integrations:

        @charon run eval_asr_pipeline

        .. code-block:: python

            {
                "s3_path_data": "s3://bucket-name/data/",
                "org_id": "org"
            }

    :param s3_path_data: S3 path to a tagged dataset (.csv).
    :type s3_path_data: str
    :param org_id: reference path to save the metrics.
    :type org_id: str
    :param channel: The slack channel to send the notification, defaults to ""
    :type channel: str, optional
    :param slack_thread: The slack thread to send the notification, defaults to ""
    :type slack_thread: str, optional
    """
    tagged_data_op = download_csv_from_s3_op(storage_path=s3_path_data)

    # Create true label column
    preprocess_data_op = create_utterances_op(tagged_data_op.outputs["output"]).after(
        tagged_data_op
    )

    # Create utterance column
    preprocess_step_2_data_op = create_true_transcript_labels_op(
        preprocess_data_op.outputs["output"], true_label_column
    ).after(preprocess_data_op)

    preprocess_step_3_data_op = process_true_transcript_labels_op(
        preprocess_step_2_data_op.outputs["output"],
        true_label_column,
    ).after(preprocess_step_2_data_op)

    asr_metrics_op = gen_asr_metrics_op(
        preprocess_step_3_data_op.outputs["output"],
        true_label_column=true_label_column,
        pred_label_column=pred_label_column,
    )

    # produce test set metrics.
    upload_metrics = upload2s3_op(
        path_on_disk=asr_metrics_op.outputs["output"],
        reference=org_id,
        file_type="asr-metrics",
        bucket=BUCKET,
        ext="",
        upload_as_directory=True,
    )
    upload_metrics.execution_options.caching_strategy.max_cache_staleness = (
        "P0D"  # disables caching
    )

    with kfp.dsl.Condition(notify != "", "notify").after(upload_metrics) as asr_check:
        notification_text = f"Here are the ASR eval results."
        code_block = f"aws s3 cp {upload_metrics.output} ."
        asr_notif = slack_notification_op(
            notification_text,
            channel=channel,
            cc=notify,
            code_block=code_block,
            thread_id=slack_thread,
        )
        asr_notif.execution_options.caching_strategy.max_cache_staleness = (
            "P0D"  # disables caching
        )


__all__ = ["eval_asr_pipeline"]
