import os
from typing import Optional

import kfp
from kfp.components import OutputPath

from skit_pipelines import constants as pipeline_constants


def fetch_calls(
    *,
    org_id: int,
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
    output_string: OutputPath(str),
):
    import time
    from datetime import datetime

    from loguru import logger
    from skit_calls import calls
    from skit_calls import constants as const
    from skit_calls import utils
    from skit_calls.cli import process_date_filters, to_datetime, validate_date_ranges

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
        on_disk=False,
    )
    logger.info(f"Finished in {time.time() - start:.2f} seconds")
    maybe_df.to_csv(output_string, index=False)


fetch_calls_op = kfp.components.create_component_from_func(
    fetch_calls, base_image=pipeline_constants.BASE_IMAGE
)
