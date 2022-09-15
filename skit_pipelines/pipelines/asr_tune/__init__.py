import os

import kfp

from skit_pipelines import constants as pipeline_constants
from skit_pipelines.components import (
    asr_tune_op,
    download_directory_from_s3_op,
    download_file_from_s3_op,
    fetch_tagged_dataset_op,
    slack_notification_op,
    upload2s3_op,
)

BUCKET = pipeline_constants.BUCKET


@kfp.dsl.pipeline(
    name="ASR Language Model Tune Pipeline",
    description="Tunes LM on provided corpus using the val_corpus for validation.",
)
def asr_tune(
    *,
    lang: str,
    base_model_path: str,
    general_lm_path: str,
    target_model_path: str,
    corpus_path: str = "",
    val_corpus_path: str = "",
    corpus_tog_job_ids: str = "",
    val_corpus_tog_job_ids: str = "",
    augment_wordlist_path: str = "",
    remove_wordlist_path: str = "",
    storage_options: str = '{"type": "s3","bucket": "vernacular-asr-models"}',
    notify: str = "",
    channel: str = "",
    slack_thread: str = "",
):
    """
    TODO: Docstring.
    """
    augment_wordlist_op = download_file_from_s3_op(
        storage_path=augment_wordlist_path, empty_possible=True
    )
    remove_wordlist_op = download_file_from_s3_op(
        storage_path=remove_wordlist_path, empty_possible=True
    )

    # create a component that can make sure:
    # 1. target_model_path does not already exist.
    # 2. target_model_path is a valid s3 path.
    # TODO: check_s3_path_does_not_exist_op(target_model_path)

    base_model_op = download_directory_from_s3_op(storage_path=base_model_path)
    general_lm_op = download_file_from_s3_op(storage_path=general_lm_path)

    with kfp.dsl.Condition(corpus_path == "", "corpus_path"):
        corpus_tog_by_job_id = fetch_tagged_dataset_op(
            job_id=corpus_tog_job_ids,
        )
        val_corpus_tog_by_job_id = fetch_tagged_dataset_op(
            job_id=val_corpus_tog_job_ids,
        )
        tune_op = asr_tune_op(
            corpus_tog_by_job_id.outputs["output"],
            val_corpus_tog_by_job_id.outputs["output"],
            augment_wordlist_op.outputs["output"],
            remove_wordlist_op.outputs["output"],
            base_model_op.outputs["output"],
            general_lm_op.outputs["output"],
            lang=lang,
        ).set_ephemeral_storage_limit("20G")

    with kfp.dsl.Condition(corpus_tog_job_ids == "", "corpus_path"):
        corpus_op = download_file_from_s3_op(storage_path=corpus_path)
        val_corpus_op = download_file_from_s3_op(storage_path=val_corpus_path)
        tune_op = asr_tune_op(
            corpus_op.outputs["output"],
            val_corpus_op.outputs["output"],
            augment_wordlist_op.outputs["output"],
            remove_wordlist_op.outputs["output"],
            base_model_op.outputs["output"],
            general_lm_op.outputs["output"],
            lang=lang,
        ).set_ephemeral_storage_limit("20G")

    upload = upload2s3_op(
        path_on_disk=tune_op.outputs["output"],
        output_path=target_model_path,
        storage_options=storage_options,
        ext="",
        upload_as_directory=True,
    )
    upload.execution_options.caching_strategy.max_cache_staleness = (
        "P0D"  # disables caching
    )

    with kfp.dsl.Condition(notify != "", "notify").after(upload) as upload_check:
        notification_text = f"The ASR Tuning pipeline is completed."
        tune_notif = slack_notification_op(
            notification_text, channel=channel, cc=notify, thread_id=slack_thread
        )
        tune_notif.execution_options.caching_strategy.max_cache_staleness = (
            "P0D"  # disables caching
        )


__all__ = ["asr_tune"]
