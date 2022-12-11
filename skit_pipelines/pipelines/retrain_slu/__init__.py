import kfp

from skit_pipelines import constants as pipeline_constants
from skit_pipelines.components import (
    create_mr_op,
    download_csv_from_s3_op,
    download_repo_op,
    download_yaml_op,
    fetch_tagged_dataset_op,
    retrain_slu_from_repo_op,
    slack_notification_op,
    upload2s3_op,
    file_contents_to_markdown_op,
)

UTTERANCES = pipeline_constants.UTTERANCES
INTENT_Y = pipeline_constants.INTENT_Y
BUCKET = pipeline_constants.BUCKET
CSV_FILE = pipeline_constants.CSV_FILE
CPU_NODE_LABEL = pipeline_constants.CPU_NODE_LABEL
GPU_NODE_LABEL = pipeline_constants.GPU_NODE_LABEL
NODESELECTOR_LABEL = pipeline_constants.POD_NODE_SELECTOR_LABEL


@kfp.dsl.pipeline(
    name="SLU retraining Pipeline",
    description="Retrains an existing SLU model.",
)
def retrain_slu(
    *,
    repo_name: str,
    repo_branch: str = "master",
    job_ids: str = "",
    dataset_path: str = "",
    labelstudio_project_ids: str = "",
    job_start_date: str = "",
    job_end_date: str = "",
    remove_intents: str = "",
    alias_yaml_path: str = "",
    initial_training: bool = False,
    use_previous_dataset: bool = True,
    epochs: int = 10,
    train_split_percent: int = 85,
    stratify: bool = False,
    target_mr_branch: str = "sandbox",
    notify: str = "",
    channel: str = "",
    slack_thread: str = "",
):

    """
    A pipeline to retrain an existing SLU model.

    .. _p_retrain_slu:

    Example payload to invoke via slack integrations:

    A minimal example:

        @charon run retrain_slu

        .. code-block:: python

            {
                "repo_name": "slu_repo_name",
                "labelstudio_project_ids": "10,13"
            }


    A full available parameters example:

        @charon run retrain_slu

        .. code-block:: python

            {
                "repo_name": "slu_repo_name",
                "repo_branch": "master",
                "dataset_path": "s3://bucket-name/path1/to1/data1.csv,s3://bucket-name/path2/to2/data2.csv",
                "job_ids": "4011,4012",
                "labelstudio_project_ids": "10,13",
                "job_start_date": "2022-08-01",
                "job_end_date": "2022-09-19",
                "remove_intents": "_confirm_,_oos_,audio_speech_unclear,ood",
                "alias_yaml_path": "intents/oppo/alias.yaml",
                "use_previous_dataset": True,
                "train_split_percent": 85,
                "stratify": False,
                "epochs": 10,
            }


    Training an SLU for first time example:

        @charon run retrain_slu

        .. code-block:: python

            {
                "repo_name": "slu_repo_name",
                "repo_branch": "master",
                "labelstudio_project_ids": "10,13",
                "initial_training": True
            }


    :param repo_name: SLU repository name under /vernacularai/ai/clients org in gitlab.
    :type repo_name: str

    :param repo_branch: The branch name in the SLU repository one wants to use, defaults to master.
    :type repo_name: str, optional

    :param dataset_path: The S3 URI or the S3 key for the tagged dataset (can be multiple - comma separated).
    :type dataset_path: str, optional

    :param job_ids: The job ids as per tog. Optional if labestudio_project_ids is provided.
    :type job_ids: str

    :param labelstudio_project_ids: The labelstudio project id (this is a number) since this is optional, defaults to "".
    :type labelstudio_project_ids: str

    :param epochs: Number of epchs to train the model, defaults to 10
    :type epochs: int, optional

    :param job_start_date: The start date range (YYYY-MM-DD) to filter tagged data.
    :type job_start_date: str, optional

    :param job_end_date: The end date range (YYYY-MM-DD) to filter tagged data
    :type job_end_date: str, optional

    :param remove_intents: Comma separated list of intents to remove from dataset while training.
    :type remove_intents: str, optional

    :param alias_yaml_path: eevee's intent_report alias.yaml, refer docs `here <https://skit-ai.github.io/eevee/metrics/intents.html#aliasing>`_ . Upload your yaml to eevee-yamls repository `here <https://github.com/skit-ai/eevee-yamls>`_ & pass the relative path of the yaml from base of the repository.
    :type alias_yaml_path: str, optional

    :param initial_training: Set to true only if you're training a model for the first time, defaults to False.
    :type initial_training: bool, optional

    :param use_previous_dataset: Before retraining combines new dataset with last dataset the model was trained on, defaults to True.
    :type use_previous_dataset: bool, optional

    :param train_split_percent: Percentage of new data one should train the model on, defaults to 85.
    :type train_split_percent: int, optional

    :param stratify: For stratified splitting of dataset into train and test set, defaults to False.
    :type stratify: bool, optional

    :param notify: Whether to send a slack notification, defaults to ""
    :type notify: str, optional

    :param channel: The slack channel to send the notification, defaults to ""
    :type channel: str, optional

    :param slack_thread: The slack thread to send the notification, defaults to ""
    :type slack_thread: str, optional

    """

    tagged_s3_data_op = download_csv_from_s3_op(storage_path=dataset_path)
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

    downloaded_repo_op = download_repo_op(
        git_host_name=pipeline_constants.GITLAB,
        repo_name=repo_name,
        project_path=pipeline_constants.GITLAB_SLU_PROJECT_PATH,
    )
    downloaded_repo_op.execution_options.caching_strategy.max_cache_staleness = (
        "P0D"  # disables caching
    )

    downloaded_alias_yaml_op = download_yaml_op(
        git_host_name=pipeline_constants.GITHUB,
        yaml_path=alias_yaml_path,
    )

    retrained_op = retrain_slu_from_repo_op(
        tagged_s3_data_op.outputs["output"],
        tagged_job_data_op.outputs["output"],
        downloaded_repo_op.outputs["repo"],
        downloaded_alias_yaml_op.outputs["output"],
        bucket=BUCKET,
        repo_name=repo_name,
        branch=repo_branch,
        remove_intents=remove_intents,
        use_previous_dataset=use_previous_dataset,
        train_split_percent=train_split_percent,
        stratify=stratify,
        epochs=epochs,
        initial_training=initial_training,
        job_ids=job_ids,
        labelstudio_project_ids=labelstudio_project_ids,
        s3_paths=dataset_path,
    )
    retrained_op.set_gpu_limit(1).add_node_selector_constraint(
        label_name=NODESELECTOR_LABEL, value=GPU_NODE_LABEL
    )

    # upload test set metrics.
    upload_cf = upload2s3_op(
        path_on_disk=retrained_op.outputs["output_classification_report"],
        reference=repo_name,
        file_type="test_classification_report",
        bucket=BUCKET,
        ext=CSV_FILE,
    )

    upload_cm = upload2s3_op(
        path_on_disk=retrained_op.outputs["output_confusion_matrix"],
        reference=repo_name,
        file_type="test_confusion_matrix",
        bucket=BUCKET,
        ext=CSV_FILE,
    )
    upload_cm.execution_options.caching_strategy.max_cache_staleness = (
        "P0D"  # disables caching
    )

    classification_report_markdown_op = file_contents_to_markdown_op(
        ext=CSV_FILE,
        path_on_disk=retrained_op.outputs['output_classification_report'],
        file_title="## Classification Report",
    )
    
    confusion_matrix_markdown_op = file_contents_to_markdown_op(
        ext=CSV_FILE,
        path_on_disk=retrained_op.outputs['output_confusion_matrix'],
        file_title="## Confusion Matrix",
    )

    mr_response_op = create_mr_op(
        git_host_name=pipeline_constants.GITLAB,
        repo_name=repo_name,
        project_path=pipeline_constants.GITLAB_SLU_PROJECT_PATH,
        target_branch=target_mr_branch,
        source_branch=retrained_op.outputs["output"],
        mr_title="Auto retrained changes",
        description=f"{classification_report_markdown_op.output}{confusion_matrix_markdown_op.output}"
    )

    with kfp.dsl.Condition(notify != "", "notify").after(retrained_op, mr_response_op):
        notification_text = f"Finished training {repo_name} SLU, please review <{mr_response_op.output}|this MR>"
        task_no_cache = slack_notification_op(
            notification_text,
            channel=channel,
            cc=notify,
            thread_id=slack_thread,
        )
        task_no_cache.execution_options.caching_strategy.max_cache_staleness = (
            "P0D"  # disables caching
        )

    with kfp.dsl.Condition(notify != "", name="slack_notify").after(
        upload_cf, upload_cm
    ):
        notification_text = f"Here's the IRR report."
        code_block = f"aws s3 cp {upload_cf.output} ."
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
        code_block = f"aws s3 cp {upload_cm.output} ."
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


__all__ = ["retrain_slu"]
