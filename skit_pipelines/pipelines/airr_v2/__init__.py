import kfp

from skit_pipelines import constants as pipeline_constants
from skit_pipelines.components import (
    fetch_tagged_dataset_op,
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
    name="XLMR Voicebot Eval IRR pipeline v2",
    description="Produces intent metrics given a .csv/tog-job, optionally takes in a model, can publish for MLWR too.",
)
def airr_v2_pipeline(
    org_id: str,
    job_id: str = "",
    s3_path_data: str = "",
    s3_path_model: str = "",
    labelstudio_project_id: str = "",
    start_date: str = "",
    end_date: str = "",
    timezone: str = "Asia/Kolkata",
    task_type: str = "conversation",
    use_state: bool = True,
    true_label_column: str = "intent_y",
    pred_label_column: str = "raw.intent",
    notify: str = "",
    channel: str = "",
    slack_thread: str = "",
):
    """
    valid pipeline_types:
        "from_csv",
        "from_csv_and_model",
        "from_tog",
        "from_tog_and_model",
        "mlwr",
    """

    with kfp.dsl.Condition(job_id != "", name="tog_job_id_provided") as tog_data:
        tog_data_op = fetch_tagged_dataset_op(
            job_id=job_id,
            project_id=labelstudio_project_id,
            task_type=task_type,
            timezone=timezone,
            start_date=start_date,
            end_date=end_date,
        )

        tog_data_op.execution_options.caching_strategy.max_cache_staleness = (
            "P0D"  # disables caching
        )

    with kfp.dsl.Condition(job_id == "", name="s3_csv_provided") as s3_csv:
        s3_csv_op = download_from_s3_op(storage_path=s3_path_data)

        s3_csv_op.execution_options.caching_strategy.max_cache_staleness = (
            "P0D"  # disables caching
        )


    # Create true label column
    preprocess_data_op = create_utterances_op(tog_data_op.outputs["output"] or s3_csv_op.outputs["output"]).after(
        tog_data or s3_csv
    )

    # Create utterance column
    preprocess_data_op = create_true_intent_labels_op(
        preprocess_data_op.outputs["output"]
    )

    # Normalize utterance column
    preprocess_data_op = create_features_op(
        preprocess_data_op.outputs["output"], use_state
    )



    with kfp.dsl.Condition(s3_path_model != "", name="s3_model_provided") as model_provided:
        loaded_model_op = download_from_s3_op(storage_path=s3_path_model)

        pred_op = get_preds_voicebot_xlmr_op(
            preprocess_data_op.outputs["output"],
            loaded_model_op.outputs["output"],
            utterance_column=UTTERANCES,
            output_pred_label_column=INTENT,
        )
        pred_op.set_gpu_limit(1)

        irr_op = gen_irr_metrics_op(
            pred_op.outputs["output"],
            true_label_column=true_label_column,
            pred_label_column=pred_label_column,
        )
        confusion_matrix_op = gen_confusion_matrix_op(
            pred_op.outputs["output"],
            true_label_column=true_label_column,
            pred_label_column=pred_label_column,
        )

    
    with kfp.dsl.Condition(s3_path_model == "", name="s3_model_not_provided") as model_not_provided:

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
    ).after(model_provided or model_not_provided)
    upload_irr.execution_options.caching_strategy.max_cache_staleness = (
        "P0D"  # disables caching
    )
    upload_cm = upload2s3_op(
        path_on_disk=confusion_matrix_op.outputs["output"],
        reference=org_id,
        file_type="xlmr-confusion-matrix",
        bucket=BUCKET,
        ext=".csv",
    ).after(model_provided or model_not_provided)
    upload_cm.execution_options.caching_strategy.max_cache_staleness = (
        "P0D"  # disables caching
    )


    
    with kfp.dsl.Condition(notify != "", name="slack_notify").after(upload_irr) as irr_check:
        notification_text = f"Here's the IRR report."
        code_block = f"aws s3 cp {upload_irr.output} ."
        irr_notif = slack_notification_op(
            notification_text, channel=channel, cc=notify, code_block=code_block, thread_id=slack_thread
        )
        irr_notif.execution_options.caching_strategy.max_cache_staleness = (
            "P0D"  # disables caching
        )

    with kfp.dsl.Condition(notify != "", name="slack_notify").after(upload_cm) as cm_check:
        notification_text = f"Here's the confusion matrix."
        code_block = f"aws s3 cp {upload_cm.output} ."
        cm_notif = slack_notification_op(
            notification_text, channel=channel, cc=notify, code_block=code_block, thread_id=slack_thread
        )
        cm_notif.execution_options.caching_strategy.max_cache_staleness = (
            "P0D"  # disables caching
        )

    # with kfp.dsl.Condition(pipeline_type == "mlwr"):
    #     pass

__all__ = ["airr_v2_pipeline"]
