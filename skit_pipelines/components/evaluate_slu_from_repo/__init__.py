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
        compare_branch: str,
        branch: str,
        remove_intents: str = "",
        validate_setup: bool = False,
        customization_repo_name: str = "",
        customization_repo_branch: str = "",
        core_slu_repo_name: str = "",
        core_slu_repo_branch: str = "",
        comparison_classification_report_path: OutputPath(str),
        comparison_confusion_matrix_path: OutputPath(str)
) -> str:
    import os
    import tempfile

    import git
    from loguru import logger

    from skit_pipelines import constants as pipeline_constants
    from skit_pipelines.components.utils import (execute_cli)
    from skit_pipelines.utils.normalize import comma_sep_str
    from skit_pipelines.components.utils_slu import setup_repo, setup_project_config_repo, data_handler, testing, compare_data

    remove_intents = comma_sep_str(remove_intents)
    compare = True if compare_branch else False

    # Setup project config repo
    project_config_local_path = setup_project_config_repo(repo_name, branch)
    repo = git.Repo(".")
    repo.config_writer().set_value("user", "name", pipeline_constants.GITLAB_USER).release()
    repo.config_writer().set_value("user", "email", pipeline_constants.GITLAB_USER_EMAIL).release()

    # Setup utility services
    setup_repo(
        customization_repo_name,
        customization_repo_branch,
        run_dir="custom_slu",
        run_cmd="task serve",
        runtime_env_var=f"PROJECT_DATA_PATH={os.path.join(project_config_local_path, '..')}",
        python_version="3.10",
    )
    logger.info("customization repo setup successfully")

    setup_repo(
        core_slu_repo_name, core_slu_repo_branch, python_version="3.10",
    )
    logger.info("core slu repo setup successfully")

    # Get data from s3 and tagged
    tagged_df = data_handler(annotated_job_data_path, s3_data_path)
    
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
        execute_cli(f"cp {validate_path} {comparison_classification_report_path}")
        execute_cli(f"cp {validate_path} {comparison_confusion_matrix_path}")
        return ""

    # Testing
    final_test_dataset_path = ""
    if os.path.exists(tagged_data_path):
        final_test_dataset_path = tagged_data_path

    classification_report_path, confusion_matrix_path = testing(repo_name, project_config_local_path, final_test_dataset_path, remove_intents, 
                                                                intent_alias_path, core_slu_repo_name, comparison_classification_report_path, 
                                                                comparison_confusion_matrix_path)
        
    compare_data(repo_name, final_test_dataset_path, 
                 project_config_local_path, core_slu_repo_name, 
                 classification_report_path,
                 comparison_classification_report_path, 
                 confusion_matrix_path, 
                 comparison_confusion_matrix_path,
                 compare_branch)
    
    return ""


evalution_slu_from_repo_op = kfp.components.create_component_from_func(
    evaluate_slu_from_repo, base_image=pipeline_constants.BASE_IMAGE
)