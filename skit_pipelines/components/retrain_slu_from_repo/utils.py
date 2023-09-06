import glob
import json
import os
import subprocess
import tempfile
from typing import List

import git
import pandas as pd
import yaml
from loguru import logger

from skit_pipelines import constants as pipeline_constants
from skit_pipelines.components.download_repo import download_repo

execute_cli = lambda cmd, split=True: subprocess.run(
    cmd.split() if split else cmd, shell=not split
)

create_dataset_path = lambda data_type, dataset_type: os.path.join(
    data_type,
    "classification/datasets",
    dataset_type + pipeline_constants.CSV_FILE,
)


def pick_1st_tag(tag: str):
    try:
        tag = json.loads(tag)

        # if tag was applied json twice while serializing
        if isinstance(tag, str):
            tag = json.loads(tag)

        if isinstance(tag, list):
            tag = tag[0]
        elif isinstance(tag, dict):
            return tag["choices"][0]
        return tag
    except json.JSONDecodeError:
        logger.warning(
            "Couldn't obtain necessary value from tag for "
        )
        return tag


def filter_dataset(
        dataset_path: str,
        remove_intents_list: List[str],
        intent_col: str = pipeline_constants.TAG,
) -> None:
    logger.info(f"filtering: {dataset_path=}\nwhile {remove_intents_list=}")
    dataset = pd.read_csv(dataset_path)
    dataset[~dataset[intent_col].isin(remove_intents_list)].to_csv(
        dataset_path, index=False
    )


def alias_dataset(
        dataset_path: str,
        alias_yaml_path: str,
        intent_col: str = pipeline_constants.TAG,
) -> None:
    reverse_alias_config = {}
    with open(alias_yaml_path, "r") as yaml_file:
        alias_config = yaml.safe_load(yaml_file)
    for map_to, map_from_values in alias_config.items():
        for map_from in map_from_values:
            reverse_alias_config[map_from] = map_to
    logger.info(f"aliasing: {dataset_path=} with config={reverse_alias_config}")
    dataset = pd.read_csv(dataset_path)
    dataset.replace({intent_col: reverse_alias_config}).to_csv(
        dataset_path, index=False
    )


def _get_metrics_path(metric_type: str, data_type: str = pipeline_constants.DATA):
    metrics_dir = os.path.join(data_type, "classification/metrics")
    latest_date_dir = max(glob.glob(metrics_dir + "/*"), key=os.path.getctime)
    latest_metrics_dir = max(
        glob.glob(latest_date_dir + "/*"), key=os.path.getctime
    )
    return os.path.join(
        latest_metrics_dir,
        metric_type + pipeline_constants.CSV_FILE,
    )


def _preprocess_test_dataset(test_df, test_dataset_path):
    if "intent" not in test_df:  # TODO: remove on phase 2 cicd release
        if "raw.intent" in test_df:
            test_df.rename(columns={"raw.intent": "intent"}).to_csv(
                test_dataset_path, index=False
            )
        else:
            test_df["intent"] = ""
            test_df.to_csv(test_dataset_path, index=False)


def evaluate(
        test_dataset_path,
        kfp_volume_classification_report_path,
        kfp_volume_confusion_matrix_path,
        project_config_local_path,
        core_slu_repo_name,
        repo_name
):
    """To evaluate a model on a test set."""
    test_df = pd.read_csv(test_dataset_path)
    _preprocess_test_dataset(test_df, test_dataset_path)
    execute_cli(
        f"PROJECT_DATA_PATH={os.path.join(project_config_local_path, '..')} "
        f"conda run --no-capture-output -n {core_slu_repo_name} "
        f"slu test --project {repo_name} --file {test_dataset_path}",
        # when custom_test_s3_data_path is passed, --file option would be redundant
        split=False,
    ).check_returncode()

    dataset_classification_report_path = _get_metrics_path(
        pipeline_constants.CLASSIFICATION_REPORT
    )
    execute_cli(
        f"cp {dataset_classification_report_path} {kfp_volume_classification_report_path}"
    )

    dataset_confusion_matrix_path = _get_metrics_path(
        pipeline_constants.FULL_CONFUSION_MATRIX
    )
    execute_cli(f"cp {dataset_confusion_matrix_path} {kfp_volume_confusion_matrix_path}")

    return dataset_classification_report_path, dataset_confusion_matrix_path


def setup_utility_repo(
        repo_name, repo_branch, run_dir=None, run_cmd=None, runtime_env_var=None
):
    repo_local_path = tempfile.mkdtemp()
    download_repo(
        git_host_name=pipeline_constants.GITLAB,
        repo_name=repo_name,
        project_path=pipeline_constants.GITLAB_SLU_PROJECT_PATH,
        repo_path=repo_local_path,
    )
    os.chdir(repo_local_path)
    repo = git.Repo(".")
    repo.config_writer().set_value(
        "user", "name", pipeline_constants.GITLAB_USER
    ).release()
    repo.config_writer().set_value(
        "user", "email", pipeline_constants.GITLAB_USER_EMAIL
    ).release()

    try:
        repo.git.checkout(repo_branch)
        execute_cli(
            f"conda create -n {repo_name} -m python=3.8 -y",
        )
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
