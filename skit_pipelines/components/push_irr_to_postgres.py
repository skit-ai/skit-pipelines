import kfp
from kfp.components import InputPath

from skit_pipelines import constants as pipeline_constants


def push_irr_to_postgres(
    eevee_intent_df_path: InputPath(str),
    extracted_pkl_path: InputPath(str),
    slu_project_name: str,
    timezone: str = "Asia/Kolkata",
):

    import json
    import pickle
    import traceback
    from datetime import datetime

    import pandas as pd
    import psycopg2
    import pytz
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

        with open(extracted_pkl_path, "rb") as fp:
            collected_info = pickle.load(fp)

        metrics = {}
        metrics["overall"] = irr_metrics_df

        # TODO:
        # grouping & aliasing breakdown
        # layers breakdown

        for category, report_df in metrics.items():

            logger.debug(category)
            precision = report_df.loc["weighted avg"]["precision"]
            recall = report_df.loc["weighted avg"]["recall"]
            f1 = report_df.loc["weighted avg"]["f1-score"]
            support = int(report_df.loc["weighted avg"]["support"])

            logger.debug(report_df.loc["weighted avg"])

            pytz_tz = pytz.timezone(timezone)
            created_at = datetime.now(tz=pytz_tz)

            dataset_job_id = int(collected_info["dataset_job_id"])

            report_df_dict = report_df.to_dict("index")
            report_df_dict["accuracy"]["support"] = report_df_dict["weighted avg"][
                "support"
            ]
            report_df_dict["accuracy"]["precision"] = None
            report_df_dict["accuracy"]["recall"] = None

            query_parameters = {
                "slu_name": slu_project_name,
                "dataset_job_id": dataset_job_id,
                "language": collected_info["language"],
                "metric_name": f"{category}-intents",
                "n_calls": collected_info["n_calls"],
                "n_turns": collected_info["n_turns"],
                "precision": precision,
                "recall": recall,
                "f1": f1,
                "support": support,
                "created_at": created_at,
                "calls_from_date": collected_info["calls_from_date"],
                "calls_to_date": collected_info["calls_to_date"],
                "tagged_from_date": collected_info["tagged_from_date"],
                "tagged_to_date": collected_info["tagged_to_date"],
                "reference_url": f"{pipeline_constants.REFERENCE_URL}{dataset_job_id}",
                "raw": json.dumps(report_df_dict),
            }

            cur.execute(
                pipeline_constants.ML_INTENT_METRICS_INSERT_SQL_QUERY, query_parameters
            )
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
#         "saved_dictionary.pkl",
#         slu_project_name,
#     )
