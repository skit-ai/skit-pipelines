import os
import pandas as pd
import git
import tempfile
from skit_pipelines.components.download_repo import download_repo
from skit_pipelines.components.retrain_slu_from_repo.comparision_report_generator import comparison_classification_report, comparison_confusion_report
from skit_pipelines.components.utils import alias_dataset, evaluate, filter_dataset, pick_1st_tag, create_dataset_path, execute_cli
from skit_pipelines import constants as pipeline_constants
from loguru import logger


def setup_project_config_repo(repo_name, branch):
    """
    Setup project config repo.
    """
    project_config_local_path = os.path.join(tempfile.mkdtemp(), repo_name)
    download_repo(
        git_host_name=pipeline_constants.GITLAB,
        repo_name=repo_name,
        project_path=pipeline_constants.GITLAB_SLU_PROJECT_CONFIG_PATH,
        repo_path=project_config_local_path,
    )
    logger.info(f"Cloned repo contents {project_config_local_path} - {os.listdir(project_config_local_path)}")

    os.chdir(project_config_local_path)
    repo = git.Repo(".")
    repo.config_writer().set_value("user", "name", pipeline_constants.GITLAB_USER).release()
    repo.config_writer().set_value("user", "email", pipeline_constants.GITLAB_USER_EMAIL).release()

    repo.git.checkout(branch)

    return project_config_local_path


def setup_repo(repo_name, repo_branch, run_dir=None, run_cmd=None, runtime_env_var=None):
    """
    Download a SLU repo and install all necessary dependencies (using conda) as found in its dockerfile.
    """
    repo_local_path = tempfile.mkdtemp()
    download_repo(
        git_host_name=pipeline_constants.GITLAB,
        repo_name=repo_name,
        project_path=pipeline_constants.GITLAB_SLU_PROJECT_PATH,
        repo_path=repo_local_path,
    )
    os.chdir(repo_local_path)
    repo = git.Repo(".")
    repo.config_writer().set_value("user", "name", pipeline_constants.GITLAB_USER).release()
    repo.config_writer().set_value("user", "email", pipeline_constants.GITLAB_USER_EMAIL).release()

    try:
        repo.git.checkout(repo_branch)
        execute_cli(f"conda create -n {repo_name} -m python=3.8 -y")
        os.system(". /conda/etc/profile.d/conda.sh")
        execute_cli(
                f"conda run -n {repo_name} "
                + "pip install poetry==$(grep POETRY_VER Dockerfile | awk -F= '{print $2}')",
                split=False,
            )
        execute_cli(f"conda run -n {repo_name} poetry install").check_returncode()
        if run_dir:
            os.chdir(run_dir)
        if run_cmd:
            command = f"{runtime_env_var if runtime_env_var else ''} conda run -n {repo_name} {run_cmd} &"
            logger.info(f"running command {command}")
            execute_cli(command, split=False)
        execute_cli("ps aux | grep task", split=False)

        return repo_local_path

    except Exception as exc:
        raise exc


def prepare_data(tagged_data_path, core_slu_repo_name, project_config_local_path, repo_name, custom_test_dataset_present, use_previous_dataset, train_split_percent, stratify):
    """
    Prepare training and testing datasets.
    """

    old_train_path = create_dataset_path(
        pipeline_constants.OLD_DATA, pipeline_constants.TRAIN
    )
    old_test_path = create_dataset_path(
        pipeline_constants.OLD_DATA, pipeline_constants.TEST
    )

    new_train_path = create_dataset_path(
        pipeline_constants.DATA, pipeline_constants.TRAIN
    )
    new_test_path = create_dataset_path(
        pipeline_constants.DATA, pipeline_constants.TEST
    )

    if custom_test_dataset_present:
        train_split_percent = 100

    if train_split_percent < 100:
        # split into train and test
        logger.info(
            f"conda run -n {core_slu_repo_name} slu split-data "
            f"--train-size {train_split_percent / 100}{' --stratify' if stratify else ''}"
            f" --file {tagged_data_path} --project_config_path {project_config_local_path} --project {repo_name}"
        )
        execute_cli(
            f"conda run -n {core_slu_repo_name} slu split-data "
            f"--train-size {train_split_percent / 100}{' --stratify' if stratify else ''}"
            f" --file {tagged_data_path} --project_config_path {project_config_local_path} --project {repo_name}"
        )
        if use_previous_dataset:
            # combine with older train set
            execute_cli(
                f"conda run -n {core_slu_repo_name} slu combine-data --out {new_train_path} {old_train_path} {new_train_path}"
            )
            if os.path.exists(old_test_path):
                # combine with older test set
                execute_cli(
                    f"conda run -n {core_slu_repo_name} slu combine-data --out {new_test_path} {old_test_path} {new_test_path}"
                )

    else:
        # don't split dataset - use all as train set
        if use_previous_dataset:
            # combine with older train dataset
            execute_cli(
                f"conda run -n {core_slu_repo_name} slu combine-data --out {new_train_path} {old_train_path} {tagged_data_path}"
            )
        else:
            # copy new dataset to new path
            execute_cli(f"cp {tagged_data_path} {new_train_path}")
        # copy old test dataset to new path
        execute_cli(
            f"cp {old_test_path} {new_test_path}"
        )  # if custom_test_dataset is present, new_test_path won't be used.
    return new_train_path, new_test_path


def data_handler(annotated_job_data_path, s3_data_path):
    no_annotated_job = False
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
    return tagged_df


def process_custom_test_dataset(custom_test_s3_data_path):
    custom_test_dataset_present = True
    custom_test_s3_df = None
    try:
        custom_test_s3_df = pd.read_csv(custom_test_s3_data_path)
        custom_test_s3_df[pipeline_constants.TAG] = custom_test_s3_df[
            pipeline_constants.TAG
        ].apply(pick_1st_tag)
    except pd.errors.EmptyDataError:
        logger.warning(
            "No custom test dataset from S3 found! While it is allowed to not pass a custom test dataset (holdout dataset),"
            "passing it is highly recommended"
        )
        custom_test_dataset_present = False

    return custom_test_dataset_present, custom_test_s3_df


def handle_dvc_and_data_paths(repo, project_config_local_path, bucket, repo_name, initial_training, core_slu_repo_name, use_previous_dataset):
    if not os.path.exists("data.dvc") and initial_training:
        execute_cli(
            f"conda run -n {core_slu_repo_name} slu setup-dirs --project_config_path {project_config_local_path}"
        )

        execute_cli("dvc init")
        execute_cli("dvc config core.no_scm true")
        execute_cli("dvc config core.hardlink_lock true")

        execute_cli(f"dvc add {pipeline_constants.DATA}")
        execute_cli(
            f"dvc remote add -d s3remote s3://{bucket}/clients/{repo_name}/"
        )
        repo.git.add([".dvc/config"])
        use_previous_dataset = False

    elif not initial_training and os.path.exists("data.dvc"):
        execute_cli("dvc pull data.dvc")
        execute_cli(f"mv {pipeline_constants.DATA} {pipeline_constants.OLD_DATA}")
        execute_cli(
            f"conda run -n {core_slu_repo_name} slu setup-dirs --project_config_path {project_config_local_path}"
        )

    else:
        raise ValueError(
            f"Discrepancy between setting {initial_training=} and repo containing data.dvc"
        )
    return use_previous_dataset


def testing(repo_name, project_config_local_path, final_test_dataset_path, remove_intents, intent_alias_path, core_slu_repo_name, 
            comparison_classification_report_path, comparison_confusion_matrix_path):
    
    # alias and filter the new test dataset
    filter_dataset(final_test_dataset_path, remove_intents)
    alias_dataset(final_test_dataset_path, intent_alias_path)

    # testing the model that was just trained
    classification_report_path, confusion_matrix_path = evaluate(
        final_test_dataset_path,
        project_config_local_path,
        core_slu_repo_name,
        repo_name
    )

    comparison_classification_report(classification_report_path, "", comparison_classification_report_path)
    comparison_confusion_report(confusion_matrix_path, "", comparison_confusion_matrix_path)
    return classification_report_path, confusion_matrix_path
    
    
def compare_data(repo_name, final_test_dataset_path, 
                 project_config_local_path, core_slu_repo_name, 
                 classification_report_path,
                 comparison_classification_report_path, 
                 confusion_matrix_path, 
                 comparison_confusion_matrix_path,
                 compare_branch="master"):
    

    if os.path.exists("data.dvc"):
        repo_url = pipeline_constants.GET_GITLAB_REPO_URL(
            repo_name=repo_name,
            project_path=pipeline_constants.GITLAB_SLU_PROJECT_CONFIG_PATH,
            user=pipeline_constants.GITLAB_USER,
            token=pipeline_constants.GITLAB_PRIVATE_TOKEN,
        )

        try:
            execute_cli(
                f"dvc get --rev {compare_branch} {repo_url} data -o prod_data"
            )
            execute_cli("rm -rf data/classification/models")
            execute_cli(
                "cp prod_data/classification/models/ data/classification/ -r"
            )

            prod_classification_report_path, prod_confusion_matrix_path = evaluate(
                final_test_dataset_path,
                project_config_local_path,
                core_slu_repo_name,
                repo_name
            )

            comparison_classification_report(classification_report_path, prod_classification_report_path,
                                            comparison_classification_report_path)
            comparison_confusion_report(confusion_matrix_path, prod_confusion_matrix_path,
                                        comparison_confusion_matrix_path)
        except Exception as e:
            prod_metrics_status_message = (
                f"Error extracting metrics from production model: {e}"
            )
            logger.error(prod_metrics_status_message)

    else:
        prod_metrics_status_message = "Skipping extracting metrics from Production model since this is initial training"
        logger.info(prod_metrics_status_message)

