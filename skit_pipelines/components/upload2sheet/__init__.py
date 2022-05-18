from typing import Dict, Any
import kfp
from kfp.components import InputPath, OutputPath

from skit_pipelines import constants as pipeline_constants

def upload2sheet(
    untagged_records_path_on_disk: InputPath(str),
    output_json: OutputPath(str),
    org_id: str = "",
    sheet_id = "",
    language_code = "",
) -> Dict[str, Any]:
    
    from loguru import logger
    import os
    from datetime import date
    import gspread
    from oauth2client.service_account import ServiceAccountCredentials
    import json
    import pandas as pd
    
    scopes = ["https://spreadsheets.google.com/feeds", 'https://www.googleapis.com/auth/spreadsheets',
        "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]
    json_dict = json.loads(os.getenv("GOOGLE_SHEETS_CREDENTIALS"), strict=False)
    json_dict["private_key"] = json_dict["private_key"].encode('utf-8').decode('unicode_escape')    
    credentials = ServiceAccountCredentials.from_json_keyfile_dict(
        json_dict, scopes=scopes
    )
    client = gspread.authorize(credentials)
    spreadsheet = client.open_by_key(sheet_id)
    
    
    target_worksheet_title = f"{language_code}-{date.today().strftime('%d-%m-%Y')}"
    source_worksheet_title = spreadsheet.worksheet("DD-MM-YYYY")
    duplicate_worksheet_request = {
        "duplicateSheet":{
            "sourceSheetId": source_worksheet_title.id,
            "newSheetName": target_worksheet_title
        }
    }
    
    main_analysis_worksheet = spreadsheet.worksheet("Main Analysis")
    main_analysis_worksheet_last_row = len(list(filter(None, main_analysis_worksheet.col_values(3))))
    main_analysis_worksheet_last_col = main_analysis_worksheet.col_count
    duplicate_rows_request = {
        "copyPaste": {
            "source": {
                "sheetId": main_analysis_worksheet.id,
                'startRowIndex': 2,
                'endRowIndex': 3,
                'startColumnIndex': 0,
                'endColumnIndex': main_analysis_worksheet_last_col
            },
            "destination": {
                "sheetId": main_analysis_worksheet.id,
                'startRowIndex': main_analysis_worksheet_last_row,
                'endRowIndex': int(main_analysis_worksheet_last_row + 1),
                'startColumnIndex': 0,
                'endColumnIndex': main_analysis_worksheet_last_col
            },
            "pasteType": "PASTE_FORMULA"
        }
    }
    
    request = {
        "requests": [
            duplicate_worksheet_request,
            duplicate_rows_request
        ]
    }
    
    response = spreadsheet.batch_update(body=request)
    
    main_analysis_worksheet.update_cell(main_analysis_worksheet_last_row+1, 1, target_worksheet_title)
    
    df = pd.read_csv(untagged_records_path_on_disk)
    unique_uuids = df.call_uuid.unique()
    console_links = [
        f"https://console.vernacular.ai/{org_id}/call-report/#/call?uuid={i}"
        for i in unique_uuids
    ]
    target_worksheet = spreadsheet.worksheet(target_worksheet_title)
    range_end_row_number = len(console_links)+3
    update_range = f"A3:A{range_end_row_number}"
    console_cell_values = [[console_link] for console_link in console_links]
    target_worksheet.update(update_range, console_cell_values)
    logger.debug(f"Uploaded {untagged_records_path_on_disk} to google sheet {sheet_id}")
    
    output_dict = {
        "num_calls_uploaded": len(console_links),
        "spread_sheet_url": f"https://docs.google.com/spreadsheets/d/{sheet_id}/edit#gid={target_worksheet.id}"
    }
    with open(output_json, "w") as writer:
        json.dump(output_dict, writer, indent=4)
    return output_dict
    
upload2sheet_op = kfp.components.create_component_from_func(
    upload2sheet, base_image=pipeline_constants.BASE_IMAGE
)
