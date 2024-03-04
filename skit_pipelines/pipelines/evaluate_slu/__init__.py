import kfp

from skit_pipelines import constants as pipeline_constants
from skit_pipelines.components import (
    download_csv_from_s3_op,
    download_yaml_op,
    fetch_tagged_dataset_op,
    evalution_slu_from_repo_op,
    slack_notification_op,
    upload2s3_op,
)

UTTERANCES = pipeline_constants.UTTERANCES
INTENT_Y = pipeline_constants.INTENT_Y
BUCKET = pipeline_constants.BUCKET
CSV_FILE = pipeline_constants.CSV_FILE
CPU_NODE_LABEL = pipeline_constants.CPU_NODE_LABEL
GPU_NODE_LABEL = pipeline_constants.GPU_NODE_LABEL
NODESELECTOR_LABEL = pipeline_constants.POD_NODE_SELECTOR_LABEL


@kfp.dsl.pipeline(
    name="SLU evaluating Pipeline",
    description="Evaluate an existing SLU model.",
)

def evaluate_slu(
    *,
    repo_name: str,
    repo_branch: str = "master",
    compare_branch: str = "master",
    job_ids: str = "",
    test_dataset_path: str = "",
    labelstudio_project_ids: str = "",
    job_start_date: str = "",
    job_end_date: str = "",
    remove_intents: str = "",
    alias_yaml_path: str = "",
    notify: str = "",
    channel: str = "",
    slack_thread: str = "",
    core_slu_repo_name: str = "core-slu-service",
    core_slu_repo_branch: str = "master",
    customization_repo_name: str = "customization",
    customization_repo_branch: str = "master",
):
    """
    A pipeline to evaluate an existing SLU model.

    .. _p_evaluate_slu:

    Example payload to invoke via slack integrations:

    A minimal example:

        @charon run evaluate_slu

        .. code-block:: python

            {
                "repo_name": "slu_repo_name",
                "labelstudio_project_ids": "10,13",
                "test_dataset_path":"s3://bucket/data.csv"
            }


    A full available parameters example:

        @charon run evaluate_slu

        .. code-block:: python

            {
                "repo_name": "slu_repo_name",
                "repo_branch": "master",
                "test_dataset_path": "s3://bucket-name/path1/to1/data1.csv,s3://bucket-name/path2/to2/data2.csv",
                "job_ids": "4011,4012",
                "labelstudio_project_ids": "10,13",
                "job_start_date": "2022-08-01",
                "job_end_date": "2022-09-19",
                "remove_intents": "_confirm_,_oos_,audio_speech_unclear,ood",
                "alias_yaml_path": "intents/oppo/alias.yaml"
            }


    :param repo_name: SLU repository name under /vernacularai/ai/clients org in gitlab.
    :type repo_name: str

    :param repo_branch: The branch name in the SLU repository one wants to use, defaults to master.
    :type repo_name: str, optional

    :param test_dataset_path: The S3 URI or the S3 key for the tagged dataset (can be multiple - comma separated).
    :type dataset_path: str, optional

    :param job_ids: The job ids as per tog. Optional if labestudio_project_ids is provided.
    :type job_ids: str

    :param labelstudio_project_ids: The labelstudio project id (this is a number) since this is optional, defaults to "".
    :type labelstudio_project_ids: str

    :param job_start_date: The start date range (YYYY-MM-DD) to filter tagged data.
    :type job_start_date: str, optional

    :param job_end_date: The end date range (YYYY-MM-DD) to filter tagged data
    :type job_end_date: str, optional

    :param remove_intents: Comma separated list of intents to remove from dataset while training.
    :type remove_intents: str, optional

    :param alias_yaml_path: eevee's intent_report alias.yaml, refer docs `here <https://skit-ai.github.io/eevee/metrics/intents.html#aliasing>`_ . Upload your yaml to eevee-yamls repository `here <https://github.com/skit-ai/eevee-yamls>`_ & pass the relative path of the yaml from base of the repository.
    :type alias_yaml_path: str, optional

    :param core_slu_repo_name: Name of repository for core slu service. Defaults to core-slu-service
    :type core_slu_repo_name: str, optional

    :param core_slu_repo_branch: Branch to check out for core slu repository. Defaults to master
    :type core_slu_repo_branch: str, optional

    :param customization_repo_name: Name of repository for customization service. Defaults to customization
    :type customization_repo_name: str, optional

    :param customization_repo_branch: Branch to check out for customization service repository. Defaults to master
    :type customization_repo_branch: str, optional

    :param notify: Whether to send a slack notification, defaults to ""
    :type notify: str, optional

    :param channel: The slack channel to send the notification, defaults to ""
    :type channel: str, optional

    :param slack_thread: The slack thread to send the notification, defaults to ""
    :type slack_thread: str, optional

    """

    tagged_s3_data_op = download_csv_from_s3_op(storage_path=test_dataset_path)
    tagged_s3_data_op.execution_options.caching_strategy.max_cache_staleness = (
        "P0D"  # disables caching
    )

    tagged_job_data_op = fetch_tagged_dataset_op(
        job_id=job_ids,
        project_id=labelstudio_project_ids,
        task_type="conversation",
        timezone="Asia/Kolkata",
        start_date=job_start_date,
        end_date=job_end_date,
        empty_possible=True,
    )
    tagged_job_data_op.execution_options.caching_strategy.max_cache_staleness = (
        "P0D"  # disables caching
    )

    downloaded_alias_yaml_op = download_yaml_op(
        git_host_name=pipeline_constants.GITLAB,
        yaml_path=alias_yaml_path,
    )

    validate_evaluation_setup_op = evalution_slu_from_repo_op(
        tagged_s3_data_op.outputs["output"],
        tagged_job_data_op.outputs["output"],
        downloaded_alias_yaml_op.outputs["output"],
        bucket=BUCKET,
        repo_name=repo_name,
        compare_branch=compare_branch,
        branch=repo_branch,
        remove_intents=remove_intents,
        validate_setup=True,
        customization_repo_name=customization_repo_name,
        customization_repo_branch=customization_repo_branch,
        core_slu_repo_name=core_slu_repo_name,
        core_slu_repo_branch=core_slu_repo_branch,
    ).set_ephemeral_storage_limit("20G")
    validate_evaluation_setup_op.display_name = "Validate Evaluation Setup"

    evaluate_op = evalution_slu_from_repo_op(
        tagged_s3_data_op.outputs["output"],
        tagged_job_data_op.outputs["output"],
        downloaded_alias_yaml_op.outputs["output"],
        bucket=BUCKET,
        repo_name=repo_name,
        compare_branch=compare_branch,
        branch=repo_branch,
        remove_intents=remove_intents,
        customization_repo_name=customization_repo_name,
        customization_repo_branch=customization_repo_branch,
        core_slu_repo_name=core_slu_repo_name,
        core_slu_repo_branch=core_slu_repo_branch,
    ).after(validate_evaluation_setup_op)
    evaluate_op.set_gpu_limit(1).add_node_selector_constraint(
        label_name=NODESELECTOR_LABEL, value=GPU_NODE_LABEL
    )

    comparison_upload_cf = upload2s3_op(
        path_on_disk=evaluate_op.outputs["comparison_classification_report"],
        reference=repo_name,
        file_type="comparison_classification_report",
        bucket=BUCKET,
        ext=CSV_FILE,
    )
    comparison_upload_cf.execution_options.caching_strategy.max_cache_staleness = (
        "P0D"  # disables caching
    )

    comparison_upload_cm = upload2s3_op(
        path_on_disk=evaluate_op.outputs["comparison_confusion_matrix"],
        reference=repo_name,
        file_type="comparison_confusion_matrix",
        bucket=BUCKET,
        ext=CSV_FILE,
    )

    with kfp.dsl.Condition(notify != "", name="slack_notify").after(
        comparison_upload_cf, comparison_upload_cm
    ):
        notification_text = f"Here's the IRR report."
        code_block = f"aws s3 cp {comparison_upload_cf.output} ."
        irr_notif = slack_notification_op(
            notification_text,
            channel=channel,
            cc=notify,
            code_block=code_block,
            thread_id=slack_thread,
        )
        irr_notif.execution_options.caching_strategy.max_cache_staleness = (
            "P0D"  # disables caching
        )

        notification_text = f"Here's the confusion matrix."
        code_block = f"aws s3 cp {comparison_upload_cm.output} ."
        cm_notif = slack_notification_op(
            notification_text,
            channel=channel,
            cc=notify,
            code_block=code_block,
            thread_id=slack_thread,
        )
        cm_notif.execution_options.caching_strategy.max_cache_staleness = (
            "P0D"  # disables caching
        )


__all__ = ["evaluate_slu"]
