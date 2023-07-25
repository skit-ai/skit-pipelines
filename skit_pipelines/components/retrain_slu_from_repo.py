import kfp
from kfp.components import InputPath, OutputPath

from skit_pipelines import constants as pipeline_constants


def retrain_slu_from_repo(
    *,
    s3_data_path: InputPath(str),
    annotated_job_data_path: InputPath(str),
    custom_s3_data_path: InputPath(str),
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
    job_ids: str = "",
    labelstudio_project_ids: str = "",
    s3_paths: str = "",
    validate_setup: bool = False,
    output_classification_report_path: OutputPath(str),
    output_confusion_matrix_path: OutputPath(str),
    customization_repo_name: str = "",
    customization_repo_branch: str = "",
    core_slu_repo_name: str = "",
    core_slu_repo_branch: str = "",
) -> str:
    import os
    import subprocess
    import tempfile
    from datetime import datetime
    from typing import Dict, List

    import git
    import pandas as pd
    import yaml
    from loguru import logger

    from skit_pipelines import constants as pipeline_constants
    from skit_pipelines.components.download_repo import download_repo
    from skit_pipelines.components.preprocess.create_true_intent_column.utils import (
        pick_1st_tag,
    )
    from skit_pipelines.utils.normalize import comma_sep_str

    execute_cli = lambda cmd, split=True: subprocess.run(
        cmd.split() if split else cmd, shell=not split
    )
    create_dataset_path = lambda data_type, dataset_type: os.path.join(
        data_type,
        "classification/datasets",
        dataset_type + pipeline_constants.CSV_FILE,
    )

    def get_metrics_path(metric_type: str, data_type: str = pipeline_constants.DATA):
        metrics_dir = os.path.join(data_type, "classification/metrics")
        metrics_dir_walk = os.walk(metrics_dir)
        return os.path.join(
            metrics_dir,
            next(metrics_dir_walk)[1][0],
            next(metrics_dir_walk)[1][0],
            metric_type + pipeline_constants.CSV_FILE,
        )

    remove_intents = comma_sep_str(remove_intents)
    no_annotated_job = False

    def filter_dataset(
        dataset_path: str,
        remove_intents: List[str],
        intent_col: str = pipeline_constants.TAG,
    ) -> None:
        logger.info(f"filtering: {dataset_path=}\nwhile {remove_intents=}")
        dataset = pd.read_csv(dataset_path)
        dataset[~dataset[intent_col].isin(remove_intents)].to_csv(
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

    # Setup project config repo
    project_config_local_path = os.path.join(tempfile.mkdtemp(), repo_name)
    download_repo(
        git_host_name=pipeline_constants.GITLAB,
        repo_name=repo_name,
        project_path="skit-ai/slu/project-configs",
        repo_path=project_config_local_path,
    )
    logger.info(
        f"Cloned repo contents {project_config_local_path} - {os.listdir(project_config_local_path)}"
    )

    os.chdir(project_config_local_path)
    repo = git.Repo(".")
    author = git.Actor(
        pipeline_constants.GITLAB_USER, pipeline_constants.GITLAB_USER_EMAIL
    )
    committer = git.Actor(
        pipeline_constants.GITLAB_USER, pipeline_constants.GITLAB_USER_EMAIL
    )
    repo.config_writer().set_value(
        "user", "name", pipeline_constants.GITLAB_USER
    ).release()
    repo.config_writer().set_value(
        "user", "email", pipeline_constants.GITLAB_USER_EMAIL
    ).release()

    repo.git.checkout(branch)

    # Setup utility services
    customization_repo_local_path = setup_utility_repo(
        customization_repo_name,
        customization_repo_branch,
        run_dir="custom_slu",
        run_cmd="task serve",
        runtime_env_var=f"PROJECT_DATA_PATH={os.path.join(project_config_local_path, '..')}",
    )
    logger.info("customization repo setup successfully")
    core_slu_repo_local_path = setup_utility_repo(
        core_slu_repo_name, core_slu_repo_branch
    )
    logger.info("core slu repo setup successfully")

    data_info = (
        f"{job_ids=}"
        if job_ids
        else "" + f" {labelstudio_project_ids=}"
        if labelstudio_project_ids
        else "" + f" {s3_paths=}"
        if s3_paths
        else ""
    )

    try:
        tagged_df = pd.read_csv(annotated_job_data_path)
        tagged_df[pipeline_constants.TAG] = tagged_df[pipeline_constants.TAG].apply(
            pick_1st_tag
        )
        custom_tagged_df = pd.DataFrame()
        custom_tagged_df = tagged_df.copy()
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
    custom = True
    try:
        custom_s3_df = pd.read_csv(custom_s3_data_path)
        custom_s3_df[pipeline_constants.TAG] = custom_s3_df[pipeline_constants.TAG].apply(
            pick_1st_tag
        )
        custom_tagged_df = custom_s3_df if no_annotated_job else pd.concat([custom_tagged_df, custom_s3_df])
    except pd.errors.EmptyDataError:
        logger.warning("No csv file from custom_s3 found!")
        if no_annotated_job:
            raise ValueError(
                "Either data from job_ids or custom_s3_path has to be available for retraining to continue."
            )   
        custom = False

    # Change directory just to make sure
    os.chdir(project_config_local_path)

    try:
        _, tagged_data_path = tempfile.mkstemp(suffix=pipeline_constants.CSV_FILE)
        tagged_df.to_csv(tagged_data_path, index=False)

        if custom:
            _, custom_s3_local_path = tempfile.mkstemp(suffix=pipeline_constants.CSV_FILE)
            custom_tagged_df.to_csv(custom_s3_local_path, index=False)

        repo.git.checkout(branch)
        new_branch = f"{datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}"
        # checkout to new branch
        repo.git.checkout("-b", new_branch)

        if not os.path.exists("data.dvc") and initial_training:
            execute_cli(
                f"conda run -n {core_slu_repo_name} slu setup-dirs --project_config_path {project_config_local_path}"
            )

            execute_cli("dvc init")
            execute_cli(f"dvc add {pipeline_constants.DATA}")
            execute_cli(
                f"dvc remote add -d s3remote s3://{bucket}/clients/{repo_name}/"
            )
            use_previous_dataset = False

        elif not initial_training and os.path.exists("data.dvc"):
            execute_cli("dvc pull data.dvc")
            execute_cli(f"mv {pipeline_constants.DATA} {pipeline_constants.OLD_DATA}")
            # TODO: fix this
            execute_cli(
                f"conda run -n {core_slu_repo_name} slu setup-dirs --project_config_path {project_config_local_path}"
            )

        else:
            raise ValueError(
                f"Discrepancy between setting {initial_training=} and repo containing data.dvc"
            )

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

        if custom:
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
            execute_cli(f"cp {old_test_path} {new_test_path}")

        else:
            if train_split_percent < 100:
                # split into train and test
                logger.info(
                    f"conda run -n {core_slu_repo_name} slu split-data "
                    f"--train-size {train_split_percent/100}{' --stratify' if stratify else ''}"
                    f" --file {tagged_data_path} --project_config_path {project_config_local_path} --project {repo_name}"
                )
                execute_cli(
                    f"conda run -n {core_slu_repo_name} slu split-data "
                    f"--train-size {train_split_percent/100}{' --stratify' if stratify else ''}"
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
                execute_cli(f"cp {old_test_path} {new_test_path}")

        # alias and filter on new train set
        alias_dataset(new_train_path, intent_alias_path)
        filter_dataset(new_train_path, remove_intents)

        # apply filter on new test dataset
        filter_dataset(new_test_path, remove_intents)
        alias_dataset(new_test_path, intent_alias_path)

        if validate_setup:
            if os.path.exists(pipeline_constants.OLD_DATA):
                execute_cli(f"rm -Rf {pipeline_constants.OLD_DATA}")
            _, validate_path = tempfile.mkstemp(suffix=pipeline_constants.CSV_FILE)
            execute_cli(f"cp {validate_path} {output_classification_report_path}")
            execute_cli(f"cp {validate_path} {output_confusion_matrix_path}")
            return ""

        # training begins
        execute_cli(
            f"PROJECT_DATA_PATH={os.path.join(project_config_local_path, '..')} conda "
            f"run --no-capture-output -n {core_slu_repo_name} slu train --project {repo_name}",
            split=False,
        ).check_returncode()
        if os.path.exists(new_test_path):
            test_df = pd.read_csv(new_test_path)
            if "intent" not in test_df:  # TODO: remove on phase 2 cicd release
                if "raw.intent" in test_df:
                    test_df.rename(columns={"raw.intent": "intent"}).to_csv(
                        new_test_path, index=False
                    )
                else:
                    test_df["intent"] = ""
                    test_df.to_csv(new_test_path, index=False)
            if custom:
                execute_cli(
                    f"PROJECT_DATA_PATH={os.path.join(project_config_local_path, '..')} "
                    f"conda run --no-capture-output -n {core_slu_repo_name} "
                    f"slu test --project {repo_name} --file {custom_s3_local_path}",
                    split=False,
                ).check_returncode()
            else:
                execute_cli(
                    f"PROJECT_DATA_PATH={os.path.join(project_config_local_path, '..')} "
                    f"conda run --no-capture-output -n {core_slu_repo_name} "
                    f"slu test --project {repo_name}",
                    split=False,
                ).check_returncode()
            if classification_report_path := get_metrics_path(
                pipeline_constants.CLASSIFICATION_REPORT
            ):
                execute_cli(
                    f"cp {classification_report_path} {output_classification_report_path}"
                )

            if confusion_matrix_path := get_metrics_path(
                pipeline_constants.FULL_CONFUSION_MATRIX
            ):
                execute_cli(
                    f"cp {confusion_matrix_path} {output_confusion_matrix_path}"
                )

        if os.path.exists(pipeline_constants.OLD_DATA):
            execute_cli(f"rm -Rf {pipeline_constants.OLD_DATA}")

        execute_cli("dvc add data")
        execute_cli("dvc push data")

        execute_cli(f"git status")
        repo.git.add(all=True)
        execute_cli(f"git status")

        repo.index.commit(
            f"Trained XLMR model using {data_info}",
            author=author,
            committer=committer,
        )
        repo.git.push("origin", new_branch)

    except git.GitCommandError as e:
        logger.error(f"{e}: Given {branch=} doesn't exist in the repo")

    return new_branch


retrain_slu_from_repo_op = kfp.components.create_component_from_func(
    retrain_slu_from_repo, base_image=pipeline_constants.BASE_IMAGE
)
