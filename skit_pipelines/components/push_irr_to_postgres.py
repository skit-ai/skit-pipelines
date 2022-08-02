import kfp
from kfp.components import InputPath

from skit_pipelines import constants as pipeline_constants

def push_irr_to_postgres(
    eevee_intent_df_path: InputPath(str),
    dataset_job_id,
    language: str,
    slu_project_name: str,
):

    import os
    import traceback
    import pytz
    from datetime import datetime

    import pandas as pd
    import psycopg2
    from loguru import logger


    ML_METRICS_DB_NAME = os.environ["ML_METRICS_DB_NAME"]
    ML_METRICS_DB_HOST = os.environ["ML_METRICS_DB_HOST"]
    ML_METRICS_DB_PORT = os.environ["ML_METRICS_DB_PORT"]
    ML_METRICS_DB_USER = os.environ["ML_METRICS_DB_USER"]
    ML_METRICS_DB_PASSWORD = os.environ["ML_METRICS_DB_PASSWORD"]


    INSERT_SQL_QUERY = """
    INSERT INTO project_event 
    (name, reference_id, support, precision, recall, f1, 
        raw, is_deleted, is_complete, created_at, updated_at, 
        of_type, language, app_id, created_date)
    VALUES 
    (%(name)s, %(reference_id)s, %(support)s, %(precision)s, %(recall)s, %(f1)s, 
        %(raw)s, %(is_deleted)s, %(is_complete)s, %(created_at)s, %(updated_at)s, 
        %(of_type)s, %(language)s, %(app_id)s, %(created_date)s);
    """

    try:

        conn = psycopg2.connect(
            dbname=ML_METRICS_DB_NAME,
            user=ML_METRICS_DB_USER,
            password=ML_METRICS_DB_PASSWORD,
            host=ML_METRICS_DB_HOST,
            port=ML_METRICS_DB_PORT,
        )
        cur = conn.cursor()


        irr_metrics_df = pd.read_csv(eevee_intent_df_path, index_col=0)
    
        metrics = {}
        metrics["overall"] = irr_metrics_df

        # TODO:
        # grouping & aliasing breakdown
        # layers breakdown

        for category, report_df in metrics.items():
            logger.debug(category)
            logger.debug(report_df)
            precision = report_df.loc["weighted avg"]["precision"]
            recall = report_df.loc["weighted avg"]["recall"]
            f1 = report_df.loc["weighted avg"]["f1-score"]
            support = int(report_df.loc["weighted avg"]["support"])

            logger.debug(report_df.loc["weighted avg"])

            to_use_datetime = datetime.now(tz=pytz.timezone("Asia/Kolkata"))

            query_parameters = {
                "name": f"{category}-intents",
                "reference_id": dataset_job_id,
                "of_type": "metric",
                "support": support,
                "language": language,
                "tagged": 0,
                "precision": precision,
                "recall": recall,
                "f1": f1,
                "raw": report_df.to_json(),
                "app": slu_project_name,
                "is_complete": True,
                "is_deleted": False,
                "created_at": to_use_datetime,
                "updated_at": to_use_datetime,
                "app_id": 1, # dummy
                "created_date": to_use_datetime, # dunno what this is supposed to be, but can't be null   
            }

            cur.execute(INSERT_SQL_QUERY, query_parameters)
            conn.commit()


    except Exception as e:
        logger.exception(e)
        logger.exception(traceback.format_exception(e))
    finally:
        cur.close()
        conn.close()

push_irr_to_postgres_op = kfp.components.create_component_from_func(
    push_irr_to_postgres, base_image=pipeline_constants.BASE_IMAGE
)


if __name__ == "__main__":

    eevee_intent_df_path = "34.csv"
    dataset_job_id = 3091
    language = "en"
    slu_project_name = "indigo"
    
    a = push_irr_to_postgres(
        eevee_intent_df_path,
        dataset_job_id,
        language,
        slu_project_name
    )
