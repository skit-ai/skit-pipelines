import kfp

from skit_pipelines import constants as pipeline_constants
from skit_pipelines.components import (
    download_csv_from_s3_op,
    download_repo_op,
    fetch_tagged_dataset_op,
    retrain_slu_from_repo_op,
    slack_notification_op,
)

UTTERANCES = pipeline_constants.UTTERANCES
INTENT_Y = pipeline_constants.INTENT_Y
BUCKET = pipeline_constants.BUCKET
CSV_FILE = pipeline_constants.CSV_FILE


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
    use_previous_dataset: bool = True,
    epochs: int = 10,
    train_split_percent: int = 85,
    stratify: bool = False,
    notify: str = "",
    channel: str = "",
    slack_thread: str = "",
):

    """
    A pipeline to retrain an existing SLU model.

    .. _p_retrain_slu:

    Example payload to invoke via slack integrations:

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
                "remove_intents": "_confirm_,_oos_,audio_speech_unclear,ood"
                "use_previous_dataset": True,
                "train_split_percent": 85,
                "stratify": False,
                "epochs": 10,
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

    retrained_op = retrain_slu_from_repo_op(
        tagged_s3_data_op.outputs["output"],
        tagged_job_data_op.outputs["output"],
        downloaded_repo_op.outputs["repo"],
        branch=repo_branch,
        remove_intents=remove_intents,
        use_previous_dataset=use_previous_dataset,
        train_split_percent=train_split_percent,
        stratify=stratify,
        epochs=epochs,
    )
    retrained_op.set_gpu_limit(1)

    # TODO use namedtuple and return more information
    # TODO return cicd pipeline url using gitlab api for manual trigger

    notification_text = (
        f"{repo_name} SLU has been retrained. New version - {retrained_op.output}"
    )
    with kfp.dsl.Condition(notify != "", "notify").after(retrained_op):
        task_no_cache = slack_notification_op(
            notification_text,
            channel=channel,
            cc=notify,
            # code_block=code_block,
            thread_id=slack_thread,
        )
        task_no_cache.execution_options.caching_strategy.max_cache_staleness = (
            "P0D"  # disables caching
        )


__all__ = ["retrain_slu"]
