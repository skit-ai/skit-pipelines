from typing import Optional, Tuple

import kfp
from kfp.components import OutputPath
from skit_pipelines import constants as pipeline_constants


def fetch_tagged_data_label_store(
    output_path: OutputPath(str),
    start_date: str,
    flow_id: str,
    end_date: Optional[str] = None,
    limit: int = 200,
):

    import os
    import tempfile
    import time
    import json
    import pytz
    import numpy as np
    import pandas as pd
    from loguru import logger
    from datetime import date, datetime, timedelta

    from sqlalchemy import create_engine
    from skit_calls import constants as const
    from skit_calls import utils
    from skit_calls.data.model import get_call_url, get_url as get_audio_url
    from skit_pipelines import constants as pipeline_constants
    from skit_calls.cli import to_datetime, validate_date_ranges

    def get_query(query_file_name):
        with open(query_file_name) as handle:
            return handle.read()

    def process_date_filters(
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        start_date_offset: int = 0,
        end_date_offset: int = 0,
        start_time_offset: int = 0,
        end_time_offset: int = 0,
    ) -> Tuple[datetime, datetime]:
        today = date.today()

        if not start_date:
            start_date = datetime.combine(today, datetime.min.time())
            start_date = start_date + timedelta(
                days=start_date_offset, hours=start_time_offset
            )
        if not end_date:
            end_date = datetime.combine(today, datetime.max.time())
            end_date = end_date + timedelta(days=end_date_offset, hours=end_time_offset)
        else:
            end_date = end_date + timedelta(hours=23, minutes=59, seconds=59)

        return start_date, end_date

    def extract_iet_annotations(row):
        annotation_result = row["annotation_result"]

        if isinstance(annotation_result, str):
            annotation_result = json.loads(annotation_result)

        if not annotation_result:
            return row

        ls_entities = []
        for item in annotation_result:
            if item["from_name"] == "tag":
                choices = item["value"]["choices"]
                row["tag"] = choices[0]
                row["intent_tag"] = choices
            elif item["from_name"] == "ls_entities":
                ls_entities.append(item["value"])
            elif item["from_name"] == "ls_transcription":
                row["transcription_tag"] = item["value"]["text"][0]

        if ls_entities:
            row["entity_tag"] = ls_entities

        return row

    def unpack_annotation_result(df):
        df["tag"] = np.nan
        df["intent_tag"] = np.nan
        df["entity_tag"] = np.nan
        df["transcription_tag"] = np.nan
        df = df.apply(extract_iet_annotations, axis=1)
        return df

    def process_call_context(row):
        def create_audio_url_col(row):
            row["audio_url"] = get_audio_url(
                row["audio_base_path"],
                row["audio_path"],
                row["call_uuid"],
                pipeline_constants.AUDIO_URL_DOMAIN,
            )
            return row

        def unpack_prediction_col(row):
            prediction = row["prediction"]

            if isinstance(prediction, str):
                prediction = json.loads(prediction)

            if not prediction:
                return row

            predicted_intent = prediction["intents"][0]
            row["slots"] = predicted_intent["slots"]
            row["intent"] = predicted_intent["name"]
            row["intent_score"] = predicted_intent["score"]
            row["entities"] = prediction["entities"]
            row["original_intent"] = prediction.get("original_intent", None)
            return row

        def create_call_url_col(row):
            if row["call_url"]:
                return row
            row["call_url"] = get_call_url(
                os.environ[const.CDN_RECORDINGS_BASE_PATH],
                row.get("call_url_id"),
                const.WAV_FILE,
            )
            return row

        row = unpack_prediction_col(row)
        row = create_audio_url_col(row)
        row = create_call_url_col(row)
        return row

    def unpack_call_context_columns(df):
        df["slots"] = "[]"
        df["intent"] = np.nan
        df["intent_score"] = np.nan
        df["entities"] = "[]"
        df["original_intent"] = None
        df["audio_url"] = ""
        df["call_url"] = ""
        df = df.apply(process_call_context, axis=1)
        return df

    def get_engine(
        host: Optional[str] = os.environ[const.DB_HOST],
        port: Optional[str] = os.environ[const.DB_PORT],
        user: Optional[str] = os.environ[const.DB_USER],
        password: Optional[str] = os.environ[const.DB_PASSWORD],
        db_name: Optional[str] = os.environ[const.DB_NAME],
    ):
        return create_engine(f"postgresql://{user}:{password}@{host}:{port}/{db_name}")

    def download_data(
        db_name, query_file_name, params, output_file_name, processing_fn=None
    ):
        header = True
        with get_engine(db_name=db_name).connect().execution_options(
            stream_results=True
        ) as conn:
            for chunk in pd.read_sql_query(
                get_query(query_file_name), conn, params=params, chunksize=1000
            ):
                if processing_fn:
                    chunk = processing_fn(chunk)
                chunk.to_csv(output_file_name, header=header, index=False, mode="a")
                header = False

    utils.configure_logger(7)
    start_date = to_datetime(start_date)
    end_date = to_datetime(end_date)
    start_date, end_date = process_date_filters(
        start_date,
        end_date,
    )
    validate_date_ranges(start_date, end_date)
    start_date = start_date.replace(tzinfo=pytz.UTC).isoformat(timespec="microseconds")
    end_date = end_date.replace(tzinfo=pytz.UTC).isoformat(timespec="microseconds")

    ann_params = {
        "flow_id": flow_id,
        "limit": limit,
        "start": start_date,
        "end": end_date,
    }
    _, annotations_file_path = tempfile.mkstemp(suffix=const.CSV_FILE)
    start = time.time()
    download_data(
        pipeline_constants.LABEL_STUDIO_DB_NAME,
        pipeline_constants.GET_ANNOTATIONS_LABEL_STORE,
        ann_params,
        annotations_file_path,
        unpack_annotation_result,
    )
    logger.info(f"Finished fetching annotations in {time.time() - start:.2f} seconds")
    df_ann = pd.read_csv(annotations_file_path)

    conversation_uuids = tuple(df_ann["conversation_uuid"].tolist())
    call_uuids = tuple(df_ann["call_uuid"].tolist())
    params = {"conversation_uuids": conversation_uuids, "call_uuids": call_uuids}
    _, call_context_file_path = tempfile.mkstemp(suffix=const.CSV_FILE)
    start = time.time()
    download_data(
        pipeline_constants.WAREHOUSE_DB_NAME,
        pipeline_constants.GET_CALL_CONTEXT_LABEL_STORE,
        params,
        call_context_file_path,
        unpack_call_context_columns,
    )
    logger.info(f"Finished fetching call context in {time.time() - start:.2f} seconds")
    df_call_context = pd.read_csv(call_context_file_path)

    df_call_context = df_call_context.drop(["audio_base_path", "audio_path"], axis=1)
    df_ann = df_ann.drop(["call_uuid", "reftime"], axis=1)
    df_merged = pd.merge(df_ann, df_call_context, on="conversation_uuid")
    df_merged.to_csv(output_path, index=False)


fetch_tagged_data_label_store_op = kfp.components.create_component_from_func(
    fetch_tagged_data_label_store, base_image=pipeline_constants.BASE_IMAGE
)
