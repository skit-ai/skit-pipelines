import kfp

from skit_pipelines import constants as pipeline_constants


def fetch_calls_for_slots(
    untagged_records_path: str,
    org_id: str = "",
    language_code="",
    start_date="",
    end_date="",
) -> str:

    import pandas as pd
    from dateutil import parser

    from skit_pipelines import constants as pipeline_constants
    from skit_pipelines.components import upload2s3

    df = pd.read_csv(untagged_records_path, usecols=["call_uuid", "reftime"])
    df = df.drop_duplicates(subset=["call_uuid"])

    df["date"] = df["reftime"].apply(lambda x: parser.isoparse(x).strftime("%Y-%m-%d"))
    df["call_link"] = df["call_uuid"].apply(
        lambda x: f"{pipeline_constants.CONSOLE_URL}/{org_id}/call-report/#/call?uuid={x}"
    )
    df["language"] = language_code

    df.drop(labels=["call_uuid", "reftime"], axis="columns", inplace=True)
    print(df.head())
    df.to_csv("op.csv", index=False)

    s3_path = upload2s3(
        "op.csv",
        reference=f"call-level-{org_id}-{start_date}-{end_date}",
        file_type=f"{language_code}-untagged",
        bucket=pipeline_constants.BUCKET,
        ext=".csv",
    )
    return s3_path


fetch_calls_for_slots_op = kfp.components.create_component_from_func(
    fetch_calls_for_slots, base_image=pipeline_constants.BASE_IMAGE
)


if __name__ == "__main__":

    fetch_calls_for_slots(
        untagged_records_path="./indigo_untagged.csv", org_id="34", language_code="en"
    )
