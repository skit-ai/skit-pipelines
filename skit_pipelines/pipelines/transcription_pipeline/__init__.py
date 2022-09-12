import kfp
import pandas as pd
from skit_pipelines import constants as pipeline_constants

from skit_pipelines.components import (
    audio_transcription_op,
    download_audio_wavs_op,
    download_csv_from_s3_op,
    download_file_from_s3_op,
    overlay_transcription_csv_op,
    slack_notification_op,
    upload2s3_op,
)

BUCKET = pipeline_constants.BUCKET

@kfp.dsl.pipeline(
    name="Transcription Pipeline",
    description="Transcribe the audio data using the mentioned ASR models",
)
def transcription_pipeline(
    *,
    data_s3_path: str,
    config_s3_path: str,
    audio_sample_rate: str="8k",
    audio_download_workers: int=30,
    transcription_concurrency: int=8,
    notify: str = "",
    channel: str = "",
    slack_thread: str = "",
):

    """
    A pipeline to transcribe the audio files using different ASRs
    .. _p_transcripe_audio:

    :param data_s3_path: S3 path of the data in CSV
    :type: str
    :param config_s3_path: The config yaml to be used by blaze. Refer to (https://github.com/skit-ai/blaze#config).
    :type: str
    """
    # Download CSV files with audio
    original_data_op = download_csv_from_s3_op(storage_path = data_s3_path)
    original_data_op.execution_options.caching_strategy.max_cache_staleness = (
        "P0D"  # disables caching
    )
    config_data_op = download_file_from_s3_op(storage_path = config_s3_path)
    config_data_op.execution_options.caching_strategy.max_cache_staleness = (
        "P0D"  # disables caching
    )
    # Download audio files from CSV
    audio_wavs_op = download_audio_wavs_op(original_data_op.outputs["output"], audio_sample_rate, audio_download_workers)

    # Transcribing
    transcribed_sqlite_op = audio_transcription_op(audio_wavs_op.outputs["output"], config_data_op.outputs["output"], concurrency=transcription_concurrency)
    
    # overlay the original csv (original_data_op) with the new transcriptions (transcribed_sqlite_op)
    overlayed_data_op = overlay_transcription_csv_op(transcribed_sqlite_op.outputs["output"], original_data_op.outputs["output"])

    # Returning S3 path
    audio_s3_path = upload2s3_op(
        path_on_disk = overlayed_data_op.outputs["output"],
        bucket = BUCKET,
        ext = ".csv"
    )

    with kfp.dsl.Condition(notify != "", name="slack_notify").after(
            audio_s3_path
        ) as audio_check:
            notification_text = f"Here's the CSV after transcription."
            code_block = f"aws s3 cp {audio_s3_path.output} ."
            audio_notif = slack_notification_op(
                notification_text,
                channel=channel,
                cc=notify,
                code_block=code_block,
                thread_id=slack_thread,
            )
            audio_notif.execution_options.caching_strategy.max_cache_staleness = (
                "P0D"  # disables caching
            )

__all__ = ["transcription_pipeline"]