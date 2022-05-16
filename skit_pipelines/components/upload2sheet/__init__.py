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
    import json
    from skit_pipelines.components.upload2sheet.utils import prepare_crr_df
    
    
    scopes = ["https://spreadsheets.google.com/feeds", 'https://www.googleapis.com/auth/spreadsheets',
        "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]
    
    json_dict = json.loads(os.getenv("GOOGLE_SHEETS_CREDENTIALS"), strict=False)
    json_dict["private_key"] = json_dict["private_key"].encode('utf-8').decode('unicode_escape')    
    
    credentials = ServiceAccountCredentials.from_json_keyfile_dict(
        json_dict, scopes=scopes
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
    
upload2sheet_op = kfp.components.create_component_from_func(
    upload2sheet, base_image=pipeline_constants.BASE_IMAGE
)
