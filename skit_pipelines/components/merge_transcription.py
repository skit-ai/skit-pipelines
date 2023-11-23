import kfp
from kfp.components import InputPath, OutputPath

from skit_pipelines import constants as pipeline_constants


def overlay_transcription_csv(
    sqlite_path: InputPath(str),
    original_csv_path: InputPath(str),
    output_path: OutputPath(str),
) -> None:

    import json
    import sqlite3

    import pandas as pd
    from loguru import logger

    from skit_pipelines.utils import convert_audiourl_to_filename

    cnx = sqlite3.connect(f"{sqlite_path}")
    df_sqlite = pd.read_sql_query("SELECT * FROM AsrResults", cnx)
    df_sqlite["filename"] = df_sqlite["filename"].apply(convert_audiourl_to_filename)

    df_sqlite["alternatives"] = (
        df_sqlite["asr_predictions"]
        .apply(json.loads)
        .apply(json.dumps, ensure_ascii=False)
    )
    logger.debug("blaze's ouptut sqlite dataframe:")
    logger.debug(df_sqlite.head())

    df_original = pd.read_csv(original_csv_path, index_col=False)

    # this doesn't help much apart from doing an inner join, implying the actual audio filename on s3 could be in .flac etc
    df_original["filename"] = df_original.audio_url.apply(convert_audiourl_to_filename)

    df = df_original.merge(df_sqlite, on="filename", how="inner", suffixes=(None, "_sqlite"))
    logger.debug("joined df has columns:")
    logger.debug(df.info())
    logger.debug(f"{df.shape[0] = }")

    if "alternatives_sqlite" in df.columns:
        # if both df_sqlite and df_original had column "alternatives", we want to keep the one from df_sqlite
        df["alternatives"] = df["alternatives_sqlite"]
        del df["alternatives_sqlite"]
    df.to_csv(output_path, index=False)


overlay_transcription_csv_op = kfp.components.create_component_from_func(
    overlay_transcription_csv, base_image=pipeline_constants.BASE_IMAGE
)


# if __name__ == "__main__":
#     overlay_transcription_csv("./results.dg.sqlite", "lohith_newly_signed.csv", "./dump.csv")
#     overlay_transcription_csv("./results.sharath.sqlite", "sharat.csv", "./dump2.csv")