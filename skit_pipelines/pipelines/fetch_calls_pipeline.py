from typing import Optional

import kfp

from skit_pipelines import constants as pipeline_constants
from skit_pipelines.components import fetch_calls_op, upload2s3_op


@kfp.dsl.pipeline(
    name="Fetch Calls Pipeline",
    description="fetches calls from production db with respective arguments",
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
        asr_provider=asr_provider,
    )
    upload2s3_op(
        org_id,
        "untagged",
        pipeline_constants.BUCKET,
        ext=".csv",
        path_on_disk=calls.output,
    )
