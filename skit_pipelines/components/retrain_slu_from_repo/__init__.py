import kfp
from kfp.components import InputPath, OutputPath

from skit_pipelines import constants as pipeline_constants


def retrain_slu_from_repo(
        *,
        s3_data_path: InputPath(str),
        custom_test_s3_data_path: InputPath(str),
        annotated_job_data_path: InputPath(str),
        intent_alias_path: InputPath(str),
        bucket: str,
        repo_name: str,
        branch: str,
        remove_intents: str = "",
        use_previous_dataset: bool = True,
        train_split_percent: int = 85,
        stratify: bool = False,
        epochs: int = 10,
        initial_training: bool = False,
        labelstudio_project_ids: str = "",
        s3_paths: str = "",
        validate_setup: bool = False,
        customization_repo_name: str = "",
        customization_repo_branch: str = "",
        core_slu_repo_name: str = "",
        core_slu_repo_branch: str = "",
        comparison_classification_report_path: OutputPath(str),
        comparison_confusion_matrix_path: OutputPath(str),
) -> str:
    import os
    import tempfile
    from datetime import datetime

    import git
    import pandas as pd
    from loguru import logger

    from skit_pipelines import constants as pipeline_constants
    from skit_pipelines.components.utils import (
        filter_dataset, alias_dataset, execute_cli
    )
    from skit_pipelines.utils.normalize import comma_sep_str
    from skit_pipelines.components.utils_slu import setup_repo, setup_project_config_repo, data_handler, prepare_data, process_custom_test_dataset, handle_dvc_and_data_paths, testing, compare_data
    remove_intents = comma_sep_str(remove_intents)
    data_info = (
        f" {labelstudio_project_ids=}"
        if labelstudio_project_ids
        else "" + f" {s3_paths=}"
        if s3_paths
        else ""
    )

    # Setup project config repo
    project_config_local_path = setup_project_config_repo(repo_name, branch)
    repo = git.Repo(".")
    repo.config_writer().set_value("user", "name", pipeline_constants.GITLAB_USER).release()
    repo.config_writer().set_value("user", "email", pipeline_constants.GITLAB_USER_EMAIL).release()
    author = git.Actor(
        pipeline_constants.GITLAB_USER, pipeline_constants.GITLAB_USER_EMAIL
    )
    committer = git.Actor(
        pipeline_constants.GITLAB_USER, pipeline_constants.GITLAB_USER_EMAIL
    )

    # Setup customization repo
    setup_repo(
        customization_repo_name,
        customization_repo_branch,
        run_dir="custom_slu",
        run_cmd="task serve",
        runtime_env_var=f"PROJECT_DATA_PATH={os.path.join(project_config_local_path, '..')}",
        python_version="3.10",
    )
    logger.info("customization repo setup successfully")

    # Setup core slu repo
    setup_repo(
        core_slu_repo_name,
        core_slu_repo_branch,
        python_version="3.10",
    )
    logger.info("core slu repo setup successfully")

    new_branch = f"{datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}"

    # Get data from s3 and tagged
    tagged_df = data_handler(annotated_job_data_path, s3_data_path)

    custom_test_dataset_present, custom_test_s3_df = process_custom_test_dataset(custom_test_s3_data_path)

    # Change directory just to make sure
    os.chdir(project_config_local_path)

    _, tagged_data_path = tempfile.mkstemp(suffix=pipeline_constants.CSV_FILE)
    tagged_df.to_csv(tagged_data_path, index=False)

    if custom_test_dataset_present:
        _, custom_test_tagged_data_path = tempfile.mkstemp(
            suffix=pipeline_constants.CSV_FILE
        )
        custom_test_s3_df.to_csv(custom_test_tagged_data_path, index=False)
        logger.info(f"saved custom dataset to {custom_test_tagged_data_path}")

    repo.git.checkout(branch)
    # checkout to new branch
    repo.git.checkout("-b", new_branch)

    # Setup DVC and data path for new repo or pull dvc for old repo
    use_previous_dataset = handle_dvc_and_data_paths(repo, project_config_local_path, bucket, repo_name, initial_training, core_slu_repo_name, use_previous_dataset)
    
    # Create final test and train data set
    new_train_path, new_test_path = prepare_data(tagged_data_path, core_slu_repo_name, project_config_local_path, repo_name, custom_test_dataset_present, use_previous_dataset, train_split_percent, stratify)

    if validate_setup:
        if os.path.exists(pipeline_constants.OLD_DATA):
            execute_cli(f"rm -Rf {pipeline_constants.OLD_DATA}")
        _, validate_path = tempfile.mkstemp(suffix=pipeline_constants.CSV_FILE)
        execute_cli(f"cp {validate_path} {comparison_classification_report_path}")
        execute_cli(f"cp {validate_path} {comparison_confusion_matrix_path}")
        return ""

    # alias and filter the new train set
    alias_dataset(new_train_path, intent_alias_path)
    filter_dataset(new_train_path, remove_intents)

    # training begins
    execute_cli(
        f"PROJECT_DATA_PATH={os.path.join(project_config_local_path, '..')} conda "
        f"run --no-capture-output -n {core_slu_repo_name} slu train --project {repo_name}",
        split=False,
    ).check_returncode()

    if os.path.exists(pipeline_constants.OLD_DATA):
        execute_cli(f"rm -Rf {pipeline_constants.OLD_DATA}")

    # Testing
    final_test_dataset_path = ""
    if custom_test_dataset_present:
        final_test_dataset_path = custom_test_tagged_data_path
    elif os.path.exists(new_test_path):
        final_test_dataset_path = new_test_path

    classification_report_path, confusion_matrix_path = testing(repo_name, project_config_local_path, final_test_dataset_path, remove_intents, intent_alias_path, core_slu_repo_name, 
            comparison_classification_report_path, comparison_confusion_matrix_path)
    
    execute_cli("dvc add data")
    execute_cli("dvc push data")

    execute_cli(f"git status")
    repo.git.add(["data.dvc"])
    execute_cli(f"git status")
    
    compare_data(repo_name, final_test_dataset_path, 
                 project_config_local_path, core_slu_repo_name, 
                 classification_report_path,
                 comparison_classification_report_path, 
                 confusion_matrix_path, 
                 comparison_confusion_matrix_path)

    repo.index.commit(
        f"Trained XLMR model using {data_info}",
        author=author,
        committer=committer,
    )
    repo.git.push("origin", new_branch)
    return new_branch


retrain_slu_from_repo_op = kfp.components.create_component_from_func(
    retrain_slu_from_repo, base_image=pipeline_constants.BASE_IMAGE
)
