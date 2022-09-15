from distutils.util import execute

import kfp
from kfp.components import InputPath, OutputPath

from skit_pipelines import constants as pipeline_constants


def retrain_slu_from_repo(
    *,
    s3_data_path: InputPath(str),
    annotated_job_data_path: InputPath(str),
    slu_path: InputPath(str),
    branch: str,
    remove_intents: str = "",
    use_previous_dataset: bool = True,
    train_split_percent: int = 85,
    stratify: bool = False,
    epochs: int = 10,
) -> str:
    import os
    import subprocess
    import tempfile
    from typing import Dict, List

    import git
    import pandas as pd
    from loguru import logger

    from skit_pipelines import constants as pipeline_constants
    from skit_pipelines.components.preprocess.create_true_intent_column.utils import (
        pick_1st_tag,
    )
    from skit_pipelines.utils.normalize import comma_sep_str

    execute_cli = lambda cmd: subprocess.run(cmd.split())
    create_dataset_path = lambda version, dataset_type: os.path.join(
        "data",
        version,
        "classification/datasets",
        dataset_type + pipeline_constants.CSV_FILE,
    )

    remove_intents = comma_sep_str(remove_intents)
    no_annotated_job = False

    def execute_cli_output(cmd):
        popen = subprocess.Popen(
            cmd.split(), stdout=subprocess.PIPE, universal_newlines=True
        )
        for stdout_line in iter(popen.stdout.readline, ""):
            yield stdout_line.rstrip("\n")
        popen.stdout.close()
        return_code = popen.wait()

        if return_code:
            raise subprocess.CalledProcessError(return_code, cmd)

    def get_slu_version():
        return next(execute_cli_output("poetry version -s"))

    def smol_version_bump(version):
        *parent, child = version.split(".")
        parent.append(str(int(child) + 1))
        return ".".join(parent)

    def filter_dataset(
        dataset_path: str,
        remove_intents: List[str],
        intent_col: str = pipeline_constants.TAG,
    ) -> None:
        dataset = pd.read_csv(dataset_path)
        dataset[~dataset[intent_col].isin(remove_intents)].to_csv(
            dataset_path, index=False
        )

    def alias_dataset(
        dataset: pd.DataFrame, alias_intents_config: Dict[str, str]
    ) -> None:
        pass

    # TODO create slu alias-data command - not imp rn

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

        execute_cli("pip install poetry -U")
        execute_cli("poetry install")
        execute_cli("dvc pull data.dvc")
        current_slu_version = get_slu_version()
        new_slu_version = smol_version_bump(current_slu_version)
        execute_cli(f"slu setup-dirs --version {new_slu_version}")

        current_train_path = create_dataset_path(
            current_slu_version, pipeline_constants.TRAIN
        )
        current_test_path = create_dataset_path(
            current_slu_version, pipeline_constants.TEST
        )

        new_train_path = create_dataset_path(new_slu_version, pipeline_constants.TRAIN)
        new_test_path = create_dataset_path(new_slu_version, pipeline_constants.TEST)

        execute_cli("ls data")

        if train_split_percent < 100:
            # split into train and test
            execute_cli(
                f"slu split-data --version {new_slu_version} --train-size {train_split_percent/100}{' --stratify' if stratify else ''} --file {tagged_data_path}"
            )
            if use_previous_dataset:
                # combine with older train set
                execute_cli(
                    f"slu combine-data --out {new_train_path} {current_train_path} {new_train_path}"
                )
                if os.path.exists(current_test_path):
                    # combine with older test set
                    execute_cli(
                        f"slu combine-data --out {new_test_path} {current_test_path} {new_test_path}"
                    )
                # apply filter on new test dataset
                filter_dataset(new_test_path, remove_intents)
        else:
            # don't split dataset
            if use_previous_dataset:
                # combine with older train dataset
                execute_cli(
                    f"slu combine-data --out {new_train_path} {current_train_path} {tagged_data_path}"
                )
            else:
                # copy new dataset to new path
                execute_cli(f"cp {tagged_data_path} {new_train_path}")
            # apply filter on new train dataset
            filter_dataset(new_train_path, remove_intents)
        # if alias then alias new train and new test set

        execute_cli(f"slu train --version {new_slu_version} --epochs {epochs}")
        if os.path.exists(current_test_path):
            execute_cli(f"slu test --version {new_slu_version}")

        logger.info("After training untracked files:", repo.untracked_files)

        repo.index.add(["config/"])
        repo.index.commit(
            f"Trained {new_slu_version} model", author=author, committer=committer
        )  # TODO - add more info like dataset used and all

        execute_cli(f"slu release --version {new_slu_version} --auto")

    except git.GitCommandError as e:
        logger.error(f"{e}: Given {branch=} doesn't exist in the repo")

    return new_slu_version


retrain_slu_from_repo_op = kfp.components.create_component_from_func(
    retrain_slu_from_repo, base_image=pipeline_constants.BASE_IMAGE
)
