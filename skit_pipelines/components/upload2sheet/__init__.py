from typing import Any, Dict

import kfp
from kfp.components import InputPath, OutputPath

from skit_pipelines import constants as pipeline_constants


def upload2sheet(
    untagged_records_path: str,
    output_json: OutputPath(str),
    org_id: str = "",
    sheet_id="",
    language_code="",
    flow_name="",
) -> Dict[str, Any]:

    import json
    import os
    from datetime import date

    import gspread
    import pandas as pd
    from loguru import logger
    from oauth2client.service_account import ServiceAccountCredentials

    today_str = date.today().strftime("%d-%m-%Y")
    output_dict = {
        "actual_num_calls_fetched": "0",
        "num_calls_uploaded": "0",
        "sheet_id": sheet_id,
        "spread_sheet_url": f"https://docs.google.com/spreadsheets/d/{sheet_id}/edit",
        "notification_text": f"No calls found for language: {language_code} for flow_name: {flow_name} on date: {today_str} to be uploaded to google sheets",
        "errors": ["no errors"],
    }

    try:
        df = pd.read_csv(untagged_records_path)
        unique_uuids = df.call_uuid.unique()
        console_links = [
            f"https://console.vernacular.ai/{org_id}/call-report/#/call?uuid={i}"
            for i in unique_uuids
        ]
        output_dict["actual_num_calls_fetched"] = len(console_links)

        scopes = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive.file",
            "https://www.googleapis.com/auth/drive",
        ]
        json_dict = json.loads(os.getenv("GOOGLE_SHEETS_CREDENTIALS"), strict=False)
        json_dict["private_key"] = (
            json_dict["private_key"].encode("utf-8").decode("unicode_escape")
        )
        credentials = ServiceAccountCredentials.from_json_keyfile_dict(
            json_dict, scopes=scopes
        )
        client = gspread.authorize(credentials)
        spreadsheet = client.open_by_key(sheet_id)

        target_worksheet_title = f"{language_code}-{today_str}"
        source_worksheet_title = spreadsheet.worksheet("DD-MM-YYYY")
        duplicate_worksheet_request = {
            "duplicateSheet": {
                "sourceSheetId": source_worksheet_title.id,
                "newSheetName": target_worksheet_title,
            }
        }

        main_analysis_worksheet = spreadsheet.worksheet("Main Analysis")
        main_analysis_worksheet_last_row = len(
            list(filter(None, main_analysis_worksheet.col_values(3)))
        )
        main_analysis_worksheet_last_col = main_analysis_worksheet.col_count
        duplicate_rows_request = {
            "copyPaste": {
                "source": {
                    "sheetId": main_analysis_worksheet.id,
                    "startRowIndex": 2,
                    "endRowIndex": 3,
                    "startColumnIndex": 0,
                    "endColumnIndex": main_analysis_worksheet_last_col,
                },
                "destination": {
                    "sheetId": main_analysis_worksheet.id,
                    "startRowIndex": main_analysis_worksheet_last_row,
                    "endRowIndex": int(main_analysis_worksheet_last_row + 1),
                    "startColumnIndex": 0,
                    "endColumnIndex": main_analysis_worksheet_last_col,
                },
                "pasteType": "PASTE_FORMULA",
            }
        }

        request = {"requests": [duplicate_worksheet_request, duplicate_rows_request]}

        response = spreadsheet.batch_update(body=request)
        main_analysis_worksheet.update_cell(
            main_analysis_worksheet_last_row + 1, 1, target_worksheet_title
        )

        target_worksheet = spreadsheet.worksheet(target_worksheet_title)
        range_end_row_number = len(console_links) + 3
        update_range = f"A3:A{range_end_row_number}"
        console_cell_values = [[console_link] for console_link in console_links]
        target_worksheet.update(update_range, console_cell_values)
        logger.debug(f"Uploaded {untagged_records_path} to google sheet {sheet_id}")

        output_dict["num_calls_uploaded"] = len(console_links)
        output_dict[
            "spread_sheet_url"
        ] = f"https://docs.google.com/spreadsheets/d/{sheet_id}/edit#gid={target_worksheet.id}"
        output_dict[
            "notification_text"
        ] = f"""Uploaded {output_dict["num_calls_uploaded"]} {language_code} language calls from flow_name: {flow_name} for date: {today_str} to {output_dict["spread_sheet_url"]} """

    except pd.errors.EmptyDataError:
        logger.error("empty dataframe")
    except Exception as e:
        output_dict["errors"] = [str(e)]
        logger.error(str(e))
        output_dict[
            "notification_text"
        ] = f"An error occured while trying to push {language_code} language calls to google sheets for flow_name: {flow_name} on date: {today_str}:"

    with open(output_json, "w") as writer:
        json.dump(output_dict, writer, indent=4)
    return output_dict


upload2sheet_op = kfp.components.create_component_from_func(
    upload2sheet, base_image=pipeline_constants.BASE_IMAGE
)
