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
    s3_path: str,
    data_label: str,
    job_ids: str = "",
    labelstudio_project_id: str = "",
    notify: str = "",
    channel: str = "",
    slack_thread: str = "",
):
    """
    A pipeline to upload a dataset for annotation.

    .. _p_tag_calls:

    Example payload to invoke via slack integrations:

        @charon run tag_calls

        .. code-block:: python

            {
                "org_id": 23,
                "job_ids": "1,2,3",
                "s3_path": "s3://bucket/path/to/file.csv"
            }

    To use labelstudio:

        @charon run tag_calls

        .. code-block:: python

            {
                "org_id": 23,
                "labelstudio_project_id": "41",
                "s3_path": "s3://bucket/path/to/file.csv"
            }

    :param org_id: The organization id as per api-gateway.
    :type org_id: str

    :param job_ids: The job ids as per tog. Optional if labestudio project id is provided.
    :type job_ids: str

    :param labelstudio_project_id: The labelstudio project id (this is a number) since this is optional, defaults to "".
    :type labelstudio_project_id: str

    :param s3_path: The s3 path to the dataset.
    :type s3_path: str

    :param data_label: A label to identify the source of a datapoint
    :type data_label: str

    :param notify: A comma separated list of slack ids: "@apples, @orange.fruit" etc, defaults to ""
    :type notify: str, optional

    :param channel: The slack channel to send the notification, defaults to ""
    :type channel: str, optional

    :param slack_thread: The slack thread to send the notification, defaults to ""
    :type slack_thread: float, optional
    """
    auth_token = org_auth_token_op(org_id)
    auth_token.execution_options.caching_strategy.max_cache_staleness = (
        "P0D"  # disables caching
    )
    tag_calls_output = tag_calls_op(
        input_file=s3_path,
        job_ids=job_ids,
        project_id=labelstudio_project_id,
        token=auth_token.output,
        org_id=org_id,
        data_label=data_label,
    )

    with kfp.dsl.Condition(notify != "", "notify").after(tag_calls_output) as check1:
        df_sizes = tag_calls_output.outputs["df_sizes"]
        errors = tag_calls_output.outputs["errors"]
        notification_text = f"Uploaded {s3_path} ({df_sizes}, {org_id=}) for tagging to {job_ids=}.\nErrors: {errors}"
        code_block = f"aws s3 cp {s3_path} ."

        task_no_cache = slack_notification_op(
            notification_text,
            cc=notify,
            channel=channel,
            code_block=code_block,
            thread_id=slack_thread,
        )
        task_no_cache.execution_options.caching_strategy.max_cache_staleness = (
            "P0D"  # disables caching
        )


__all__ = ["tag_calls"]
