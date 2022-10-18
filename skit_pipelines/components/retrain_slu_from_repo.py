import kfp
from kfp.components import InputPath, OutputPath

from skit_pipelines import constants as pipeline_constants


def retrain_slu_from_repo(
    *,
    s3_data_path: InputPath(str),
    annotated_job_data_path: InputPath(str),
    slu_path: InputPath(str),
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
    output_classification_report_path: OutputPath(str),
    output_confusion_matrix_path: OutputPath(str),
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
    from skit_pipelines.components.preprocess.create_true_intent_column.utils import (
        pick_1st_tag,
    )
    from skit_pipelines.utils.normalize import comma_sep_str

    execute_cli = lambda cmd: subprocess.run(cmd.split())
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

    data_info = (
        f"{job_ids=}"
        if job_ids
        else "" + f" {labelstudio_project_ids=}"
        if labelstudio_project_ids
        else "" + f" {s3_paths=}"
        if s3_paths
        else ""
    )

    os.chdir(slu_path)
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
        tagged_df = pd.concat([tagged_df, s3_df])
    except pd.errors.EmptyDataError:
        logger.warning("No csv file from S3 found!")
        if no_annotated_job:
            raise ValueError(
                "Either data from job_ids or s3_path has to be available for retraining to continue."
            )

    try:
        _, tagged_data_path = tempfile.mkstemp(suffix=pipeline_constants.CSV_FILE)
        tagged_df.to_csv(tagged_data_path, index=False)

        repo.git.checkout(branch)
        new_branch = f"{datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}"
        # checkout to new branch
        repo.git.checkout("-b", new_branch)

        execute_cli("pip install poetry -U")
        execute_cli("make install")

        if not os.path.exists("data.dvc") and initial_training:
            execute_cli("slu setup-dirs")
            execute_cli("dvc init")
            execute_cli(f"dvc add {pipeline_constants.DATA}")
            execute_cli(
                f"dvc remote add -d s3remote s3://{bucket}/clients/{repo_name}/"
            )
            use_previous_dataset = False

        elif not initial_training and os.path.exists("data.dvc"):
            execute_cli("dvc pull data.dvc")
            execute_cli(f"mv {pipeline_constants.DATA} {pipeline_constants.OLD_DATA}")
            execute_cli("slu setup-dirs")

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

        execute_cli("ls data")

        if train_split_percent < 100:
            # split into train and test
            execute_cli(
                f"slu split-data --train-size {train_split_percent/100}{' --stratify' if stratify else ''} --file {tagged_data_path}"
            )
            if use_previous_dataset:
                # combine with older train set
                execute_cli(
                    f"slu combine-data --out {new_train_path} {old_train_path} {new_train_path}"
                )
                if os.path.exists(old_test_path):
                    # combine with older test set
                    execute_cli(
                        f"slu combine-data --out {new_test_path} {old_test_path} {new_test_path}"
                    )

        else:
            # don't split dataset - use all as train set
            if use_previous_dataset:
                # combine with older train dataset
                execute_cli(
                    f"slu combine-data --out {new_train_path} {old_train_path} {tagged_data_path}"
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

        # training begins
        execute_cli(f"slu train --epochs {epochs}")
        if os.path.exists(new_test_path):
            test_df = pd.read_csv(new_test_path)
            if "intent" not in test_df: #TODO: remove on phase 2 cicd release
                if "raw.intent" in test_df:
                    test_df.rename(columns={"raw.intent": "intent"}).to_csv(
                        new_test_path, index=False
                    )
                else:
                    test_df["intent"] = []

            execute_cli(f"slu test")
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
