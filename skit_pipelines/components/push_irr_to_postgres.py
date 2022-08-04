import kfp
from kfp.components import InputPath

from skit_pipelines import constants as pipeline_constants

def push_irr_to_postgres(
    eevee_intent_df_path: InputPath(str),
    dataset_job_id,
    language: str,
    slu_project_name: str,
):

    import traceback
    import pytz
    from datetime import datetime

    import pandas as pd
    import psycopg2
    from loguru import logger

    from skit_pipelines import constants as pipeline_constants


    try:

        conn = psycopg2.connect(
            dbname=pipeline_constants.ML_METRICS_DB_NAME,
            user=pipeline_constants.ML_METRICS_DB_USER,
            password=pipeline_constants.ML_METRICS_DB_PASSWORD,
            host=pipeline_constants.ML_METRICS_DB_HOST,
            port=pipeline_constants.ML_METRICS_DB_PORT,
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
                "slu_name": slu_project_name,
                "dataset_job_id": dataset_job_id,
                "language": language,
                "metric_name": f"{category}-intents",
                "precision": precision,
                "recall": recall,
                "f1": f1,
                "support": support,
                "created_at": to_use_datetime,
                "reference_url": f"{pipeline_constants.REFERENCE_URL}{dataset_job_id}",
                "raw": report_df.to_json(),
            }

            cur.execute(pipeline_constants.ML_INTENT_METRICS_INSERT_SQL_QUERY, query_parameters)
            conn.commit()


    except Exception as e:
        logger.exception(e)
        print(traceback.print_exc())

    finally:
        cur.close()
        conn.close()

push_irr_to_postgres_op = kfp.components.create_component_from_func(
    push_irr_to_postgres, base_image=pipeline_constants.BASE_IMAGE
)


# if __name__ == "__main__":

#     eevee_intent_df_path = "34.csv"
#     dataset_job_id = 3091
#     language = "en"
#     slu_project_name = "indigo"
    
#     a = push_irr_to_postgres(
#         eevee_intent_df_path,
#         dataset_job_id,
#         language,
#         slu_project_name
#     )
