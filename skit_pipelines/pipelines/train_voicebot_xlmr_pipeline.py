import kfp

from skit_pipelines import constants as pipeline_constants
from skit_pipelines.components import (
    fetch_tagged_dataset_op,
    download_from_s3_op,
    train_xlmr_voicebot_op
)


@kfp.dsl.pipeline(
    name="Fetch Tagged Dataset Pipeline",
    description="fetches tagged dataset from tog with respective arguments",
)
def run_fetch_tagged_dataset(
    job_id: int,
    task_type: str,
    timezone: str,
    start_date: str,
    end_date: str,
    s3_path: str,
    utterance_column: str,
    label_column: str,
    model_type: str = "xlmroberta",
    model_name: str = "xlm-roberta-base",
):
    with kfp.dsl.Condition(s3_path):
        tagged_df = download_from_s3_op(s3_path)

    with kfp.dsl.Condition(not s3_path):
        tagged_df = fetch_tagged_dataset_op(
            job_id,
            task_type=task_type,
            timezone=timezone,
            start_date=start_date,
            end_date=end_date,
        )

    print(tagged_df.outputs["output"])

    # preprocess the file: aliases, remove duplicates, etc.

    # create train and test splits

    # train model
    train_xlmr_voicebot_op(
        tagged_df.outputs["output"],
        utterance_column=utterance_column,
        label_column=label_column,
        model_type=model_type,
        model_name=model_name
    )
    # produce test set metrics.
