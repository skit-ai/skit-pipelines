import kfp
from kfp.components import InputPath

from skit_pipelines import constants as pipeline_constants


def push_eer_to_postgres(
    eevee_entity_metrics_path: InputPath(str),
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

        entity_metrics_df = pd.read_csv(eevee_entity_metrics_path, index_col="Entity")
        print(entity_metrics_df.head())

        with open(extracted_pkl_path, "rb") as fp:
            collected_info = pickle.load(fp)


        pytz_tz = pytz.timezone(timezone)
        created_at = datetime.now(tz=pytz_tz)
    

        for entity_type in entity_metrics_df.index:
            report_row = entity_metrics_df.loc[entity_type]
            logger.debug(entity_type)

            fpr = report_row.loc["FPR"]
            fnr = report_row.loc["FNR"]
            mmr = report_row.loc["Mismatch Rate"]
            support = int(report_row["Support"])
            negatives = int(report_row["Negatives"])

            dataset_job_id = int(collected_info["dataset_job_id"])
            report_row_dict = report_row.to_dict()

            query_parameters = {
                "slu_name": slu_project_name,
                "dataset_job_id": dataset_job_id,
                "language": collected_info["language"],
                "metric_name": f"{entity_type}-entity",
                "n_calls": collected_info["n_calls"],
                "n_turns": collected_info["n_turns"],
                "false_positive_rate": fpr,
                "false_negative_rate": fnr,
                "mismatch_rate": mmr,
                "support": support,
                "negatives": negatives,
                "created_at": created_at,
                "calls_from_date": collected_info["calls_from_date"],
                "calls_to_date": collected_info["calls_to_date"],
                "tagged_from_date": collected_info["tagged_from_date"],
                "tagged_to_date": collected_info["tagged_to_date"],
                "raw": json.dumps(report_row_dict),
            }

            logger.debug(query_parameters)

            cur.execute(
                pipeline_constants.ML_ENTITY_METRICS_INSERT_SQL_QUERY, query_parameters
            )
        
        # Make the changes to the database persistent 
        # after the for-loop
        conn.commit()

    except Exception as e:
        logger.exception(e)
        print(traceback.print_exc())

    finally:
        cur.close()
        conn.close()


push_eer_to_postgres_op = kfp.components.create_component_from_func(
    push_eer_to_postgres, base_image=pipeline_constants.BASE_IMAGE
)


if __name__ == "__main__":

    eevee_entity_metrics_path = "op.csv"
    collected_data_path = "collected_data.pkl"
    slu_project_name = "american_finance"

    a = push_eer_to_postgres(
        eevee_entity_metrics_path,
        collected_data_path,
        slu_project_name,
    )
