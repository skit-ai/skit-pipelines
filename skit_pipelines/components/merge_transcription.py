import kfp
from kfp.components import InputPath, OutputPath

from skit_pipelines import constants as pipeline_constants


def overlay_transcription_csv(
    sqlite_path: InputPath(str),
    original_csv_path: InputPath(str),
    output_path: OutputPath(str),
) -> None:
    import json
    import os
    import sqlite3

    import pandas as pd
    from loguru import logger

    def convert_audiourl_to_filename(audiourl):
        fn = audiourl.rsplit("/", 1)[-1]
        if fn.endswith(".flac"):
            return fn[:-5] + ".wav"
        if fn.endswith(".mp3"):
            return fn[:-4] + ".wav"
        return fn

    cnx = sqlite3.connect(f"{sqlite_path}")
    df_sqlite = pd.read_sql_query("SELECT * FROM AsrResults", cnx)
    df_sqlite = df_sqlite.set_index("filename")
    df_sqlite["alternatives"] = (
        df_sqlite["asr_predictions"]
        .apply(json.loads)
        .apply(json.dumps, ensure_ascii=False)
    )

    df_original = pd.read_csv(original_csv_path, index_col=False)
    df_original["filename"] = df_original.audio_url.apply(convert_audiourl_to_filename)

    df = df_original.join(df_sqlite, on="filename", how="inner", rsuffix="_sqlite")
    logger.debug("joined df has columns:")
    logger.debug(df.info())

    if "alternatives_sqlite" in df.columns:
        # if both df_sqlite and df_original had column "alternatives", we want to keep the one from df_sqlite
        df["alternatives"] = df["alternatives_sqlite"]
        del df["alternatives_sqlite"]
    df.to_csv(output_path, index=False)


overlay_transcription_csv_op = kfp.components.create_component_from_func(
    overlay_transcription_csv, base_image=pipeline_constants.BASE_IMAGE
)
