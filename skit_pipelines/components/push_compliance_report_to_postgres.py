import kfp

from skit_pipelines import constants as pipeline_constants


def push_compliance_report_to_postgres(
    s3_file_path: str,
) -> int:
    import tempfile

    import pandas as pd
    import psycopg2

    from skit_pipelines import constants as pipeline_constants
    from skit_pipelines.components.download_from_s3 import download_csv_from_s3

    CREATE_TABLE_QUERY = """CREATE TABLE IF NOT EXISTS compliance_breaches 
    (
        id SERIAL PRIMARY KEY, 
        call_uuid CHAR(255) NOT NULL, 
        audio_url CHAR(511),
        call_url CHAR(511), 
        flow_uuid CHAR(255),
        client_uuid CHAR(255),
        reftime TIMESTAMP,
        is_breach BOOLEAN NOT NULL,
        compliance_output CHAR(5000) NOT NULL,
        tokens_consumed INT NOT NULL,
        call_information CHAR(10000)
    );"""

    INSERT_COMPLIANCE_RESULT_QUERY = """INSERT INTO compliance_breaches 
    (
        call_uuid,
        audio_url,
        call_url,
        flow_uuid,
        client_uuid,
        reftime,
        is_breach,
        compliance_output,
        tokens_consumed,
        call_information
    )
    VALUES
    (
        %(call_uuid)s,
        %(audio_url)s,
        %(call_url)s,
        %(flow_uuid)s,
        %(client_uuid)s,
        %(reftime)s,
        %(is_breach)s,
        %(compliance_output)s,
        %(tokens_consumed)s,
        %(call_information)s
    )
    """

    fd_download, downloaded_file_path = tempfile.mkstemp(suffix=".csv")
    download_csv_from_s3(storage_path=s3_file_path, output_path=downloaded_file_path)
    df_breaches = pd.read_csv(downloaded_file_path)

    conn = psycopg2.connect(
        dbname=pipeline_constants.ML_METRICS_DB_NAME,
        user=pipeline_constants.ML_METRICS_DB_USER,
        password=pipeline_constants.ML_METRICS_DB_PASSWORD,
        host=pipeline_constants.ML_METRICS_DB_HOST,
        port=pipeline_constants.ML_METRICS_DB_PORT,
    )
    cur = conn.cursor()
    cur.execute(CREATE_TABLE_QUERY)
    conn.commit()

    breach_counter = 0
    for _, row in df_breaches.iterrows():
        try:
            query_parameters = {
                "call_uuid": row["call_uuid"],
                "audio_url": row["audio_url"],
                "call_url": row["call_url"],
                "flow_uuid": row["flow_uuid"],
                "client_uuid": row["client_uuid"],
                "reftime": row["reftime"],
                "is_breach": row["is_breach"],
                "compliance_output": row["compliance_output"],
                "tokens_consumed": row["tokens_consumed"],
                "call_information": row["call_information"]
            }

            cur.execute(INSERT_COMPLIANCE_RESULT_QUERY, query_parameters)

            if row["is_breach"]:
                breach_counter += 1
        except Exception as e:
            print("Couldn't write compliance response report for call uuid " + row["call_uuid"] +
                  " because: " + str(e))

    conn.commit()
    cur.close()
    conn.close()
    return breach_counter


push_compliance_report_to_postgres_op = kfp.components.create_component_from_func(
    push_compliance_report_to_postgres, base_image=pipeline_constants.BASE_IMAGE
)
