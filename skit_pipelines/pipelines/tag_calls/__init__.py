import kfp

from skit_pipelines.components import (
    org_auth_token_op,
    read_json_key_op,
    slack_notification_op,
    tag_calls_op,
)


@kfp.dsl.pipeline(
    name="Tag Calls Pipeline",
    description="Uploads calls to database for tagging",
)
def tag_calls(
    org_id: str,
    job_ids: str,
    s3_path: str,
    notify: str = "",
    channel: str = "",
):
    """
    A pipeline to upload a dataset for annotation.

    .. _p_tag_calls:

    Example payload to invoke via slack integrations:

        @slackbot run tag_calls

        .. code-block:: json

            {
                "org_id": 23,
                "job_ids": "1,2,3",
                "s3_path": "s3://bucket/path/to/file.csv",
                "notify": "@person, @personwith.spacedname",
                "channel": "#some-public-channel"
            }

    :param org_id: The organization id as per api-gateway.
    :type org_id: str
    :param job_ids: Comma separated list of job ids.
    :type job_ids: str
    :param s3_path: The s3 path to the dataset.
    :type s3_path: str
    :param notify: A comma separated list of slack ids: "@apples, @orange.fruit" etc, defaults to ""
    :type notify: str, optional
    :param channel: The slack channel to send the notification, defaults to ""
    :type channel: str, optional
    """
    auth_token = org_auth_token_op(org_id)
    auth_token.execution_options.caching_strategy.max_cache_staleness = (
        "P0D"  # disables caching
    )
    tag_calls_output = tag_calls_op(
        input_file=s3_path,
        job_ids=job_ids,
        token=auth_token.output,
    )
    df_sizes = read_json_key_op("df_sizes", tag_calls_output.outputs["output_json"])
    df_sizes.display_name = "get-df-size"
    errors = read_json_key_op("errors", tag_calls_output.outputs["output_json"])
    errors.display_name = "get-any-errors"

    notification_text = f"Uploaded {s3_path} ({getattr(df_sizes, 'output')}, {org_id=}) for tagging to {job_ids=}.\nErrors: {getattr(errors, 'output')}"

    with kfp.dsl.Condition(notify != "", "notify").after(errors) as check1:
        task_no_cache = slack_notification_op(
            notification_text, "", cc=notify, channel=channel
        )
        task_no_cache.execution_options.caching_strategy.max_cache_staleness = (
            "P0D"  # disables caching
        )


__all__ = ["tag_calls"]
