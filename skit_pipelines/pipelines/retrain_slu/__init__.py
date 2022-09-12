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
    repo_branch: str,
    job_ids: str = "",
    dataset_path: str = "",
    labelstudio_project_ids: str = "",
    job_start_date: str = "",
    job_end_date: str = "",
    remove_intents: str = "",
    use_previous_dataset: bool = True,
    org_id: str = "",
    epochs: int = 10,
    train_split_percent: int = 85,
    stratify: bool = False,
    notify: str = "",
    channel: str = "",
    slack_thread: str = "",
):

    tagged_s3_data_op = download_csv_from_s3_op(
        storage_path=dataset_path
    )
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
    
    notification_text = f"{repo_name} SLU has been retrained. New version - {retrained_op.output}"
    with kfp.dsl.Condition(notify != "", "notify").after(retrained_op):
        code_block = f"aws s3 cp {retrained_op.output} ."
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