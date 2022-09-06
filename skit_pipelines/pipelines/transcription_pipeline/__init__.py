import csv
import json
import kfp
import sqlite3
import pandas as pd
from skit_pipelines import constants as pipeline_constants

from skit_pipelines.components import (
    download_from_s3_op,
    pull_audio_op,
    asr_transcription_op,
    upload2s3_op,
    merge_transcription_csv_op,
)

BUCKET = pipeline_constants.BUCKET

@kfp.dsl.pipeline(
    name="Transcription Pipeline",
    description="Transcribe the audio data using the mentioned ASR models",
)
def transcription_audio_pipeline(
    s3_path: str, 
    asr_model: str,
):

    """
    A pipeline to transcribe the audio files using different ASRs
    .. _p_transcripe_audio:

    :param s3_path: S3 path of the data in CSV
    :type: str
    :param asr_model: ASR model name
    :type: str
    """
    #Download CSV files with audio
    audio_data = download_from_s3_op(storage_path = s3_path, output_path = "")
    
    #Download audio files from CSV
    audio = pull_audio_op("", "output_folder")

    #Transcribing
    if (asr_model == "GASR"):
        #GASR
        asr_transcription_op("output_folder", "../../utils/resources_blaze/config_google.yaml")
    elif (asr_model == "VASR"):
        #VASR
        asr_transcription_op("output_folder", "../../utils/resources_blaze/config_kaldi.yaml")
    elif (asr_model == "AASR"):
        #Azure-ASR
        asr_transcription_op("output_folder", "../../utils/resources_blaze/config_azure.yaml")

    #merging the transcription file with ASR
    audio_csv = merge_transcription_csv_op("results.sqlite", audio_data)

    #Returning S3 path
    audio_s3_path = upload2s3_op(
        path_on_disk = audio_csv,
        bucket = BUCKET,
        ext = ".csv"
    )

__all__ = ["transcription_audio_pipeline"]




