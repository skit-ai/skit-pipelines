import kfp
from kfp.components import InputPath, OutputPath

from skit_pipelines import constants as pipeline_constants


def evaluate_slu_from_repo(
        *,
        s3_data_path: InputPath(str),
        annotated_job_data_path: InputPath(str),
        intent_alias_path: InputPath(str),
        bucket: str,
        repo_name: str,
        branch: str,
        remove_intents: str = "",
        labelstudio_project_ids: str = "",
        s3_paths: str = "",
        validate_setup: bool = False,
        customization_repo_name: str = "",
        customization_repo_branch: str = "",
        core_slu_repo_name: str = "",
        core_slu_repo_branch: str = "",
        output_classification_report_path: OutputPath(str),
        output_confusion_matrix_path: OutputPath(str)
) -> str:
    import os
    import tempfile
    from datetime import datetime

    import git
    import pandas as pd
    from loguru import logger

    from skit_pipelines import constants as pipeline_constants
    from skit_pipelines.components.download_repo import download_repo
    from skit_pipelines.components.utils import (
        pick_1st_tag, filter_dataset, alias_dataset, evaluate, create_dataset_path, execute_cli
    )
    from skit_pipelines.components.retrain_slu_from_repo.comparision_report_generator import \
        comparison_classification_report, comparison_confusion_report
    from skit_pipelines.utils.normalize import comma_sep_str
    from skit_pipelines.components.setup_repo import setup_utility_repo

    remove_intents = comma_sep_str(remove_intents)
    no_annotated_job = False

    # Setup project config repo
    project_config_local_path = os.path.join(tempfile.mkdtemp(), repo_name)
    download_repo(
        git_host_name=pipeline_constants.GITLAB,
        repo_name=repo_name,
        project_path=pipeline_constants.GITLAB_SLU_PROJECT_CONFIG_PATH,
        repo_path=project_config_local_path,
    )
    logger.info(
        f"Cloned repo contents {project_config_local_path} - {os.listdir(project_config_local_path)}"
    )

    os.chdir(project_config_local_path)
    repo = git.Repo(".")

    repo.config_writer().set_value(
        "user", "name", pipeline_constants.GITLAB_USER
    ).release()
    repo.config_writer().set_value(
        "user", "email", pipeline_constants.GITLAB_USER_EMAIL
    ).release()

    repo.git.checkout(branch)

    # Setup utility services
    setup_utility_repo(
        customization_repo_name,
        customization_repo_branch,
        run_dir="custom_slu",
        run_cmd="task serve",
        runtime_env_var=f"PROJECT_DATA_PATH={os.path.join(project_config_local_path, '..')}",
    )
    logger.info("customization repo setup successfully")

    setup_utility_repo(
        core_slu_repo_name, core_slu_repo_branch
    )
    logger.info("core slu repo setup successfully")

    try:
        tagged_df = pd.read_csv(annotated_job_data_path)
        tagged_df[pipeline_constants.TAG] = tagged_df[pipeline_constants.TAG].apply(
            pick_1st_tag
        )
    except pd.errors.EmptyDataError:
        logger.warning(
            "No data found in given annotated jobs, check if data is tagged or job_ids are missing!"
        )
        no_annotated_job = True
    try:
        s3_df = pd.read_csv(s3_data_path)
        s3_df[pipeline_constants.TAG] = s3_df[pipeline_constants.TAG].apply(
            pick_1st_tag
        )
        tagged_df = s3_df if no_annotated_job else pd.concat([tagged_df, s3_df])
    except pd.errors.EmptyDataError:
        logger.warning("No csv file from S3 found!")
        if no_annotated_job:
            raise ValueError(
                "Either data from job_ids or s3_path has to be available for retraining to continue."
            )
    
    # Change directory just to make sure
    os.chdir(project_config_local_path)

    _, tagged_data_path = tempfile.mkstemp(suffix=pipeline_constants.CSV_FILE)
    tagged_df.to_csv(tagged_data_path, index=False)

    repo.git.checkout(branch)

    if os.path.exists("data.dvc"):
        execute_cli("dvc pull data.dvc")
        # execute_cli(f"mv {pipeline_constants.DATA} {pipeline_constants.OLD_DATA}")
        execute_cli(
            f"conda run -n {core_slu_repo_name} slu setup-dirs --project_config_path {project_config_local_path}"
        )

    else:
        raise ValueError(
            "Discrepancy between setting and repo containing data.dvc"
        )

    if validate_setup:
        _, validate_path = tempfile.mkstemp(suffix=pipeline_constants.CSV_FILE)
        execute_cli(f"cp {validate_path} {output_classification_report_path}")
        execute_cli(f"cp {validate_path} {output_confusion_matrix_path}")
        return ""
    
    # alias and filter the new train set
    filter_dataset(tagged_data_path, remove_intents)
    alias_dataset(tagged_data_path, intent_alias_path)

    # Testing
    final_test_dataset_path = ""
    if os.path.exists(tagged_data_path):
        final_test_dataset_path = tagged_data_path


    # testing the model that was just trained
    classification_report_path, confusion_matrix_path = evaluate(
        final_test_dataset_path,
        project_config_local_path,
        core_slu_repo_name,
        repo_name
    )

    execute_cli(
        f"cp {classification_report_path} {output_classification_report_path}"
    )

    execute_cli(
         f"cp {confusion_matrix_path} {output_confusion_matrix_path}"
    )

    if os.path.exists(pipeline_constants.OLD_DATA):
        execute_cli(f"rm -Rf {pipeline_constants.OLD_DATA}")

    return ""


evalution_slu_from_repo_op = kfp.components.create_component_from_func(
    evaluate_slu_from_repo, base_image=pipeline_constants.BASE_IMAGE
)