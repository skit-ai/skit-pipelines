from typing import Optional
import os
import kfp
import kfp.components as comp


BASE_IMAGE = os.environ["BASE_IMAGE"]


def upload2s3(org_id: str, file_type: str, path_on_disk: str):
    import os
    import boto3
    from datetime import datetime
    from loguru import logger

    s3_resource = boto3.client('s3')
    bucket = os.environ["BUCKET"]
    _, ext = os.path.splitext(os.path.basename(path_on_disk))
    upload_path = os.path.join(
        "project",
        str(org_id),
        datetime.now().strftime("%Y-%m-%d"),
        f"{datetime.now().strftime('%Y-%m-%d')}-{file_type}{ext}",
    )
    s3_resource.upload_file(path_on_disk, bucket, upload_path)
    logger.debug(f"Uploaded {path_on_disk} to {upload_path}")


def fetch_calls(
    org_id: str,
    start_date: str,
    lang: str,
    end_date: Optional[str] = None,
    call_quantity: int = 200,
    call_type: Optional[str] = None,
    ignore_callers: Optional[str] = None,
    reported: Optional[str] = None,
    use_case: Optional[str] = None,
    flow_name: Optional[str] = None,
    min_duration: Optional[str] = None,
    asr_provider: Optional[str] = None,
    on_disk: bool = False,
) -> str:
    import time
    import tempfile
    from datetime import datetime

    from loguru import logger
    from skit_calls import calls, utils, constants as const
    from skit_calls.cli import to_datetime, validate_date_ranges, process_date_filters

    utils.configure_logger(7)

    start_date = to_datetime(start_date)
    if end_date:
        end_date = to_datetime(end_date)
    else:
        end_date = datetime.now()

    validate_date_ranges(start_date, end_date)
    start_date, end_date = process_date_filters(start_date, end_date)

    if not call_quantity:
        call_quantity = const.DEFAULT_CALL_QUANTITY
    if not call_type:
        call_type = const.INBOUND
    if not ignore_callers:
        ignore_callers = const.DEFAULT_IGNORE_CALLERS_LIST
    
    start = time.time()
    maybe_df = calls.sample(
        org_id,
        start_date,
        end_date,
        lang,
        call_quantity=call_quantity,
        call_type=call_type or None,
        ignore_callers=ignore_callers,
        reported=reported or None,
        use_case=use_case or None,
        flow_name=flow_name or None,
        min_duration=min_duration or None,
        asr_provider=asr_provider or None,
        on_disk=on_disk or False,
    )
    logger.info(f"Finished in {time.time() - start:.2f} seconds")
    if on_disk:
        return maybe_df
    else:
        _, file_path = tempfile.mkstemp(suffix=const.CSV_FILE)
        maybe_df.to_csv(file_path, index=False)
        return file_path


fetch_calls_op = kfp.components.create_component_from_func(fetch_calls, base_image=BASE_IMAGE) 
upload2s3_op = kfp.components.create_component_from_func(upload2s3, base_image=BASE_IMAGE)


@kfp.dsl.pipeline(
    name='Fetch Calls Pipeline',
    description='fetches calls from production db with respective arguments'
)
def run_fetch_calls(
    org_id: str,
    start_date: str,
    lang: str,
    end_date: Optional[str],
    call_quantity: int,
    call_type: Optional[str],
    ignore_callers: Optional[str],
    reported: Optional[str],
    use_case: Optional[str],
    flow_name: Optional[str],
    min_duration: Optional[str],
    asr_provider: Optional[str],
):

    calls = fetch_calls_op(
        org_id=org_id,
        start_date=start_date,
        end_date=end_date,
        lang=lang,
        call_quantity=call_quantity,
        call_type=call_type,
        ignore_callers=ignore_callers,
        reported=reported,
        use_case=use_case,
        flow_name=flow_name,
        min_duration=min_duration,
        asr_provider=asr_provider
    )
    upload2s3_op(org_id=org_id, file_type="untagged", path_on_disk=calls.output)
