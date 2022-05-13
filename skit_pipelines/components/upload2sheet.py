import kfp
from kfp.components import InputPath

from skit_pipelines import constants as pipeline_constants

def upload2sheet(
    untagged_records_path_on_disk: InputPath(str),
    org_id: str = "",
    sheet_id = "",
    language_code = "",
    num_rows: int = 1000,
    given_comma_seperated_columns: str = ""
) -> str:
    
    from loguru import logger
    import os
    from datetime import date, timedelta
    import gspread
    from oauth2client.service_account import ServiceAccountCredentials
    
    scope = ["https://spreadsheets.google.com/feeds", 'https://www.googleapis.com/auth/spreadsheets',
        "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]
    credentials = ServiceAccountCredentials.from_json_keyfile_name(
       os.getenv("GOOGLE_CLIENT_SECRET_PATH", "secrets/google_client_secret.json") , scope
    )
    client = gspread.authorize(credentials)
    
    df_crr = prepare_crr_df(untagged_records_path_on_disk, org_id, given_comma_seperated_columns)

    spreadsheet = client.open_by_key(sheet_id)
    yesterday = date.today() - timedelta(days=1)
    worksheet_title = f"{language_code}-{yesterday.strftime('%Y-%m-%d')}"
    num_cols = min(1, len(given_comma_seperated_columns.split(",")))
    worksheet = spreadsheet.add_worksheet(title=worksheet_title, rows=num_rows, cols=num_cols)
    worksheet.update([df_crr.columns.values.tolist()] + df_crr.values.tolist())
    logger.debug(f"Uploaded {untagged_records_path_on_disk} to google sheet {sheet_id}")
    

def prepare_crr_df(untagged_records_path_on_disk, org_id, given_comma_seperated_columns):
    import pandas as pd
    
    df = pd.read_csv(untagged_records_path_on_disk)
    uuids = df.call_uuid.unique()
    console_links = [
        f"https://console.vernacular.ai/{org_id}/call-report/#/call?uuid={i}"
        for i in uuids
    ]
    
    df_crr = pd.DataFrame()
    columns = ["call_url"]
    
    if given_comma_seperated_columns:
        columns = given_comma_seperated_columns.split(",")
        if "call_url" not in columns:
            columns.insert(0, "call_url")
        
    df_crr.columns = columns
    df_crr["call_url"] = console_links

    return df_crr

upload2sheet_op = kfp.components.create_component_from_func(
    upload2sheet, base_image=pipeline_constants.BASE_IMAGE
)
