import kfp
from kfp.components import InputPath, OutputPath

from skit_pipelines import constants as pipeline_constants


def extract_info_from_dataset(
    dataset_path: InputPath(str), output_path: OutputPath(str), timezone: str
):

    import pickle

    import pandas as pd
    import pytz
    from dateutil.parser import parse
    from loguru import logger

    df = pd.read_csv(dataset_path)
    logger.info(f"size of the dataset: {len(df)}")

    pytz_tz = pytz.timezone(timezone)

    def give_appropriate_datetime(datetime_str, pytz_tz):
        # handling wrong tz offset
        # https://stackoverflow.com/questions/6410971/python-datetime-object-show-wrong-timezone-offset
        datetime_without_tz = parse(datetime_str).replace(tzinfo=None)
        return pytz_tz.localize(datetime_without_tz)

    language = df["raw.language"].iloc[0]
    job_id = df["job_id"].iloc[0]
    n_calls = df["call_uuid"].nunique()
    n_turns = df["conversation_uuid"].nunique()
    min_tagged_time = df["tagged_time"].min()
    max_tagged_time = df["tagged_time"].max()
    min_reftime = df["reftime"].min()
    max_reftime = df["reftime"].max()

    min_reftime = give_appropriate_datetime(min_reftime, pytz_tz)
    max_reftime = give_appropriate_datetime(max_reftime, pytz_tz)

    min_tagged_time = give_appropriate_datetime(min_tagged_time, pytz_tz)
    max_tagged_time = give_appropriate_datetime(max_tagged_time, pytz_tz)

    duplicated_conversations = df["conversation_uuid"].duplicated().sum()
    if duplicated_conversations > 0:
        logger.info(
            f"there are {duplicated_conversations} duplicated converations in the dataset."
        )

    collected_info = {
        "language": language,
        "dataset_job_id": job_id,
        "n_calls": n_calls,
        "n_turns": n_turns,
        "calls_from_date": min_reftime,
        "calls_to_date": max_reftime,
        "tagged_from_date": min_tagged_time,
        "tagged_to_date": max_tagged_time,
    }
    logger.debug(collected_info)

    with open(output_path, "wb") as f:
        pickle.dump(collected_info, f)


extract_info_from_dataset_op = kfp.components.create_component_from_func(
    extract_info_from_dataset, base_image=pipeline_constants.BASE_IMAGE
)

# if __name__ == "__main__":

#     extract_info_from_dataset(
#         dataset_path="3091.csv",
#         output_path="saved_dictionary.pkl",
#         timezone="Asia/Kolkata"
#     )