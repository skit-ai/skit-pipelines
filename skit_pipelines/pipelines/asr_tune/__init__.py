import os

import kfp

from skit_pipelines import constants as pipeline_constants
from skit_pipelines.components import (
    asr_tune_op,
    download_from_s3_op,
    slack_notification_op,
)

UTTERANCES = pipeline_constants.UTTERANCES
INTENT_Y = pipeline_constants.INTENT_Y
BUCKET = pipeline_constants.BUCKET
INTENT = pipeline_constants.INTENT


@kfp.dsl.pipeline(
    name="XLMR Voicebot Eval Pipeline",
    description="Produces intent metrics for an XLM Roberta model on given dataset.",
)
def asr_tune(
    *,
    lang: str,
    base_model_path: str,
    target_model_path: str,
    corpus_path: str,
    domain_bias: float,
    augment_wordlist_path: str,
    remove_wordlist_path: str,
    notify: str = "",
    channel: str = "",
    slack_thread: str = "",
):
    """
    TODO: Docstring.
    """
    corpus_op = download_from_s3_op(storage_path=corpus_path)
    augment_wordlist_op = download_from_s3_op(storage_path=augment_wordlist_path)
    remove_wordlist_op = download_from_s3_op(storage_path=remove_wordlist_path)

    tune_op = asr_tune_op(lang=lang, base_model_path=base_model_path, target_model_path=target_model_path, corpus_path=corpus_op.outputs["output"], domain_bias=domain_bias, augment_wordlist_path=augment_wordlist_op.outputs["output"], remove_wordlist_path=remove_wordlist_op.outputs["output"])

    with kfp.dsl.Condition(notify != "", "notify").after(tune_op) as tune_check:
        notification_text = f"The ASR Tuning pipeline is completed."
        tune_notif = slack_notification_op(
            notification_text, channel=channel, cc=notify, thread_id=slack_thread
        )
        tune_notif.execution_options.caching_strategy.max_cache_staleness = (
            "P0D"  # disables caching
        )


__all__ = ["asr_tune"]
