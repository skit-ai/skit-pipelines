import kfp

from skit_pipelines import constants as pipeline_constants

def merge_transcription_csv(
    sql_file: str,
    output_csv: str,
) -> str:
    import sqlite3
    import pandas as pd
    import json

    cnx = sqlite3.connect(f'{sql_file}')
    df = pd.read_sql_query('SELECT * FROM AsrResults', cnx)
    df["asr_predictions"] = df["asr_predictions"].apply(json.loads)
    
    output_csv.outputs["alternatives"] = df["asr_predicitons"]
    return output_csv
    
merge_transcription_csv_op = kfp.components.create_component_from_func(
    merge_transcription_csv, base_image = pipeline_constants.BASE_IMAGE
)