from typing import Optional

import kfp
from kfp.components import OutputPath

from skit_pipelines import constants as pipeline_constants


def fetch_calls(
    *,
    client_id: int,
    start_date: str,
    lang: str,
    end_date: Optional[str] = None,
    call_quantity: int = 200,
    call_type: Optional[str] = None,
    ignore_callers: Optional[str] = None,
    reported: bool = False,
    use_case: Optional[str] = None,
    flow_name: Optional[str] = None,
    min_duration: Optional[str] = None,
    asr_provider: Optional[str] = None,
    states: Optional[str] = None,
) -> str:
    import tempfile
    import time
    from datetime import datetime, timedelta

    from loguru import logger
    from skit_calls import calls
    from skit_calls import constants as const
    from skit_calls import utils
    from skit_calls.cli import process_date_filters, to_datetime, validate_date_ranges

    from skit_pipelines import constants as pipeline_constants
    from skit_pipelines.components import upload2s3
    from skit_pipelines.utils.normalize import comma_sep_str

    utils.configure_logger(7)
    start_date = to_datetime(start_date)
    end_date = to_datetime(end_date)

    start_date, end_date = process_date_filters(start_date, end_date)
    validate_date_ranges(start_date, end_date)

    if not call_quantity:
        call_quantity = const.DEFAULT_CALL_QUANTITY
    if not call_type:
        call_type = const.INBOUND
    if not ignore_callers:
        ignore_callers = const.DEFAULT_IGNORE_CALLERS_LIST

    start = time.time()
    states = comma_sep_str(states) if states else states

    maybe_df = calls.sample(
        client_id,
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
        states=states or None,
        on_disk=False,
    )
    logger.info(f"Finished in {time.time() - start:.2f} seconds")
    _, file_path = tempfile.mkstemp(suffix=const.CSV_FILE)
    maybe_df.to_csv(file_path, index=False)

    s3_path = upload2s3(
        file_path,
        reference=f"{client_id}-{start_date}-{end_date}",
        file_type=f"{lang}-untagged",
        bucket=pipeline_constants.BUCKET,
        ext=".csv",
    )
    return s3_path


fetch_calls_op = kfp.components.create_component_from_func(
    fetch_calls, base_image=pipeline_constants.BASE_IMAGE
)
