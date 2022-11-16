import kfp

from skit_pipelines import constants as pipeline_constants
from skit_pipelines.components import (
    fetch_tagged_data_label_store_op,
    upload2s3_op,
    slack_notification_op,
)


@kfp.dsl.pipeline(
    name="Fetch and push for calls to gogole sheets pipeline",
    description="fetches calls from production db with respective arguments and uploads calls to google sheets for Call tagging",
)
def fetch_tagged_data_from_labelstore(
    flow_id: str,
    start_date: str = "",
    end_date: str = "",
    limit: int = 200,
    notify: str = "",
    channel: str = "",
    slack_thread: str = "",
):
    tagged_df = fetch_tagged_data_label_store_op(
        flow_id=flow_id, start_date=start_date, end_date=end_date, limit=limit
    )

    tagged_df.execution_options.caching_strategy.max_cache_staleness = (
        "P0D"  # disables caching
    )

    s3_upload = upload2s3_op(
        path_on_disk=tagged_df.outputs["output"],
        reference=f"{flow_id}-{start_date}-{end_date}",
        file_type=f"annotations-with-call-context",
        bucket=pipeline_constants.BUCKET,
        ext=".csv",
    )

    s3_upload.execution_options.caching_strategy.max_cache_staleness = (
        "P0D"  # disables caching
    )

    notification_text = (
        f"Here is your data for {flow_id=} and date_range: {start_date=}, {end_date=}."
    )
    code_block = f"aws s3 cp {s3_upload.output} ."
    with kfp.dsl.Condition(notify != "", "notify").after(s3_upload) as check1:
        task_no_cache = slack_notification_op(
            notification_text,
            code_block=code_block,
            cc=notify,
            channel=channel,
            thread_id=slack_thread,
        )
        task_no_cache.execution_options.caching_strategy.max_cache_staleness = (
            "P0D"  # disables caching
        )


__all__ = ["run_fetch_iet_tagged_data"]
