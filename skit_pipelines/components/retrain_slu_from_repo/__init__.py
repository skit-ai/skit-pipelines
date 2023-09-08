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
    job_ids: str = "",
    labelstudio_project_ids: str = "",
    s3_paths: str = "",
    validate_setup: bool = False,
    customization_repo_name: str = "",
    customization_repo_branch: str = "",
    core_slu_repo_name: str = "",
    core_slu_repo_branch: str = "",
    output_classification_report_path: OutputPath(str),
    production_classification_report_path: OutputPath(str),
    comparison_classification_report_path: OutputPath(str),
    output_confusion_matrix_path: OutputPath(str),
    production_confusion_matrix_path: OutputPath(str),
    # comparison_confusion_matrix_path: OutputPath(str), # TODO enable this
) -> str:
    import os
    import glob
    import subprocess
    import tempfile
    from datetime import datetime
    from tabulate import tabulate

    from typing import Dict, List

    import git
    import pandas as pd
    import yaml
    from loguru import logger

    from skit_pipelines import constants as pipeline_constants
    from skit_pipelines.components.download_repo import download_repo
    from skit_pipelines.components.retrain_slu_from_repo.utils import (
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
        latest_date_dir = max(glob.glob(metrics_dir + "/*"), key=os.path.getctime)
        latest_metrics_dir = max(
            glob.glob(latest_date_dir + "/*"), key=os.path.getctime
        )
        return os.path.join(
            latest_metrics_dir,
            metric_type + pipeline_constants.CSV_FILE,
        )

    remove_intents = comma_sep_str(remove_intents)
    no_annotated_job = False
    custom_test_dataset_present = True

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

    def preprocess_test_dataset(test_df, test_dataset_path):
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
        kfp_volume_classification_report_path=output_classification_report_path,
        kfp_volumne_confusion_matrix_path=output_confusion_matrix_path,
    ):
        """To evaluate a model on a test set."""
        test_df = pd.read_csv(test_dataset_path)
        preprocess_test_dataset(test_df, test_dataset_path)
        execute_cli(
            f"PROJECT_DATA_PATH={os.path.join(project_config_local_path, '..')} "
            f"conda run --no-capture-output -n {core_slu_repo_name} "
            f"slu test --project {repo_name} --file {test_dataset_path}",  # when custom_test_s3_data_path is passed, --file option would be redundant
            split=False,
        ).check_returncode()

        dataset_classification_report_path = get_metrics_path(
            pipeline_constants.CLASSIFICATION_REPORT
        )
        execute_cli(
            f"cp {dataset_classification_report_path} {kfp_volume_classification_report_path}"
        )

        dataset_confusion_matrix_path = get_metrics_path(
            pipeline_constants.FULL_CONFUSION_MATRIX
        )
        execute_cli(f"cp {dataset_confusion_matrix_path} {kfp_volumne_confusion_matrix_path}")

        return dataset_classification_report_path, dataset_confusion_matrix_path

    def create_comparison_classification_report(
        report1_path: str, report2_path: str, output_path: str
    ):
        report1_df = pd.read_csv(report1_path)

        if not report2_path:
            report2_df = pd.DataFrame(
                columns=["Unnamed: 0", "precision", "recall", "f1-score", "support"],
                index=range(len(report1_df)),
            )
        else:
            report2_df = pd.read_csv(report2_path)

        # Extract the class labels from both reports
        classes1 = report1_df["Unnamed: 0"].tolist()
        classes2 = report2_df["Unnamed: 0"].tolist()

        # Create a set of all class labels
        all_classes = classes1 + [x for x in classes2 if x not in classes1]
        all_classes = [x for x in all_classes if not pd.isna(x)]

        # Move "accuracy", "macro avg", and "weighted avg" to the end
        special_rows = ["accuracy", "macro avg", "weighted avg"]
        for special_row in special_rows:
            if special_row in all_classes:
                all_classes.remove(special_row)
                all_classes.append(special_row)

        # Initialize a dictionary to store the comparison data
        comparison_data = {}

        # Iterate through each class label
        for class_label in all_classes:
            # Get the row index for each class label
            index1 = (
                report1_df[report1_df["Unnamed: 0"] == class_label].index[0]
                if class_label in classes1
                else None
            )
            index2 = (
                report2_df[report2_df["Unnamed: 0"] == class_label].index[0]
                if class_label in classes2
                else None
            )

            # Get the precision, recall, f1-score, and support values for each report
            precision1 = report1_df["precision"][index1] if index1 is not None else None
            recall1 = report1_df["recall"][index1] if index1 is not None else None
            f1_score1 = report1_df["f1-score"][index1] if index1 is not None else None
            support1 = int(report1_df["support"][index1]) if index1 is not None else None

            precision2 = report2_df["precision"][index2] if index2 is not None else None
            recall2 = report2_df["recall"][index2] if index2 is not None else None
            f1_score2 = report2_df["f1-score"][index2] if index2 is not None else None
            support2 = int(report2_df["support"][index2]) if index2 is not None else None

            # Create tuples of values for each metric
            precision_tuple = (precision1, precision2)
            recall_tuple = (recall1, recall2)
            f1_score_tuple = (f1_score1, f1_score2)
            support_tuple = (support1, support2)

            # Store the tuples in the comparison data dictionary
            comparison_data[class_label] = (
                precision_tuple,
                recall_tuple,
                f1_score_tuple,
                support_tuple,
            )

        # Create a DataFrame from the comparison data
        comparison_df = pd.DataFrame.from_dict(
            comparison_data,
            orient="index",
            columns=["precision", "recall", "f1-score", "support"],
        )

        comparison_df.to_csv(output_path)
        # Print the comparison report using tabulate for better formatting
        print(tabulate(comparison_df, headers="keys", tablefmt="psql"))

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

    new_branch = f"{datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}"

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

    # Change directory just to make sure
    os.chdir(project_config_local_path)

    try:
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

        if custom_test_dataset_present:
            # there is no need to split the tagged_df into train and test since the custom_test_dataset will be used for evalution of trained model
            # all of the datapoints from tagged_df can be used for training
            train_split_percent = 100

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
            execute_cli(
                f"cp {old_test_path} {new_test_path}"
            )  # if custom_test_dataset is present, new_test_path won't be used.

        if validate_setup:
            if os.path.exists(pipeline_constants.OLD_DATA):
                execute_cli(f"rm -Rf {pipeline_constants.OLD_DATA}")
            _, validate_path = tempfile.mkstemp(suffix=pipeline_constants.CSV_FILE)
            execute_cli(f"cp {validate_path} {output_classification_report_path}")
            execute_cli(f"cp {validate_path} {output_confusion_matrix_path}")
            execute_cli(f"cp {validate_path} {comparison_classification_report_path}")
            execute_cli(f"cp {validate_path} {production_classification_report_path}")
            execute_cli(f"cp {validate_path} {production_confusion_matrix_path}")
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

        # Testing
        final_test_dataset_path = ""
        if custom_test_dataset_present:
            final_test_dataset_path = custom_test_tagged_data_path
        elif os.path.exists(new_test_path):
            final_test_dataset_path = new_test_path

        # alias and filter the new test dataset
        filter_dataset(final_test_dataset_path, remove_intents)
        alias_dataset(final_test_dataset_path, intent_alias_path)

        # testing the model that was just trained
        classification_report_path, confusion_matrix_path = evaluate(
            final_test_dataset_path
        )
        _, merged_classification_report_path = tempfile.mkstemp(
            suffix=pipeline_constants.CSV_FILE
        )
        create_comparison_classification_report(
            classification_report_path, "", merged_classification_report_path
        )

        # create the comparison report between metrics from the latest model and an empty metrics file
        # this is the default when there is no prod model or there is an issue with extracting metrics from prod model
        execute_cli(
            f"cp {merged_classification_report_path} {comparison_classification_report_path}"
        )
        # TODO create comparison for confusion matrix as well
        # just like create_comparison_classification_report, another function needs to be implemented

        if os.path.exists(pipeline_constants.OLD_DATA):
            execute_cli(f"rm -Rf {pipeline_constants.OLD_DATA}")

        execute_cli("dvc add data")
        execute_cli("dvc push data")
       
        execute_cli("dvc config core.no_scm true")
        execute_cli("dvc config core.hardlink_lock true")
       
        execute_cli(f"git status")
        repo.git.add(["data.dvc"])
        execute_cli(f"git status")

        repo.index.commit(
            f"Trained XLMR model using {data_info}",
            author=author,
            committer=committer,
        )
        repo.git.push("origin", new_branch)

        # Setup Production model
        success_extracting_production_metrics = False
        prod_metrics_status_message = "Empty file"
        try:
            if not initial_training and os.path.exists("data.dvc"):
                # if a model already exists (means this is not the first time training the model)
                repo_url = pipeline_constants.GET_GITLAB_REPO_URL(
                    repo_name=repo_name,
                    project_path=pipeline_constants.GITLAB_SLU_PROJECT_CONFIG_PATH,
                    user=pipeline_constants.GITLAB_USER,
                    token=pipeline_constants.GITLAB_PRIVATE_TOKEN,
                )

                # download the data folder from the production branch. The data folder will have the model
                execute_cli(
                    f"dvc get --rev {pipeline_constants.PRODUCTION_BRANCH_ON_CONFIG_REPO} {repo_url} data -o prod_data"
                )

                # remove the newly trained model. The model and its metrics are backed up to dvc and the git branch is already pushed.
                execute_cli("rm -rf data/classification/models")

                # replace the newly trained model with the model from production
                execute_cli(
                    "cp prod_data/classification/models/ data/classification/ -r"
                )

                # evaluate the production model with the same test set and the same codebase as the newly trained model
                prod_classification_report_path, prod_confusion_matrix_path = evaluate(
                    final_test_dataset_path,
                    production_classification_report_path,
                    production_confusion_matrix_path,
                )

                # once metrics from prod model are succesfully extracted, we recreate the comparison report.
                # this time we do it between metrics from latest model and prod model
                create_comparison_classification_report(
                    classification_report_path,
                    prod_classification_report_path,
                    merged_classification_report_path,
                )
                execute_cli(
                    f"cp {merged_classification_report_path} {comparison_classification_report_path}"
                )
                # TODO re-create comparison for confusion matrix as well

                success_extracting_production_metrics = True
            else:
                prod_metrics_status_message = "Skipping extracting metrics from Production model since this is initial training"
                logger.info(prod_metrics_status_message)
        except Exception as e:
            prod_metrics_status_message = (
                f"Error extracting metrics from production model: {e}"
            )
            logger.error(prod_metrics_status_message)

        if not success_extracting_production_metrics:
            # There was some issue with extracting metrics from the production model

            prod_classification_report_path = "prod_classification_report.csv"
            prod_confusion_matrix_path = "prod_confusion_matrix.csv"
            pd.DataFrame([{"message": prod_metrics_status_message}]).to_csv(
                prod_classification_report_path, index=False
            )
            pd.DataFrame([{"message": prod_metrics_status_message}]).to_csv(
                prod_confusion_matrix_path, index=False
            )
            execute_cli(
                f"cp {prod_classification_report_path} {production_classification_report_path}"
            )
            execute_cli(
                f"cp {prod_confusion_matrix_path} {production_confusion_matrix_path}"
            )
    except git.GitCommandError as e:
        logger.error(f"{e}: Given {branch=} doesn't exist in the repo")

    return new_branch


retrain_slu_from_repo_op = kfp.components.create_component_from_func(
    retrain_slu_from_repo, base_image=pipeline_constants.BASE_IMAGE
)
