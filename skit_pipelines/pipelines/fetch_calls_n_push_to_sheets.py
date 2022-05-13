import kfp

from skit_pipelines.components import (
    fetch_calls_op,
    download_from_s3_op,
    upload2sheet_op
)

@kfp.dsl.pipeline(
    name="Fetch and push for calls to gogole sheets pipeline",
    description="fetches calls from production db with respective arguments and uploads calls to google sheets for CRR tagging",
)
def run_fetch_n_tag_calls(
    client_id: int,
    org_id: str,
    start_date: str,
    lang: str,
    end_date: str,
    ignore_callers: str,
    reported: str,
    use_case: str,
    flow_name: str,
    min_duration: str,
    asr_provider: str,
    call_quantity: int = 200,
    call_type: str = "INBOUND",
    sheet_id: str = "",
    sheet_column_names = "",
):
    untagged_records_s3_path = fetch_calls_op(
        client_id=client_id,
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
    
    untagged_records_s3_path.execution_options.caching_strategy.max_cache_staleness = (
        "P0D" # disables caching
    )
    
    untagged_records_op = download_from_s3_op(storage_path=untagged_records_s3_path.outputs["output"])
    
    upload = upload2sheet_op(
        untagged_records_op.outputs["output"],
        org_id=org_id,
        sheet_id=sheet_id,
        language_code=lang,
        num_rows=call_quantity,
        given_comma_seperated_columns=sheet_column_names
    )
    
    upload.execution_options.caching_strategy.max_cache_staleness = (
        "P0D" # disables caching
    )
    
