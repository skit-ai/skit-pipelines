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

    df = pd.read_csv(untagged_records_path, usecols=["call_uuid", "reftime", "call_type", "language", "call_end_status", "disposition", "flow_id", "flow_version", "flow_name", "call_duration", "flow_uuid", "client_uuid", "template_id"])
    df = df.drop_duplicates(subset=["call_uuid"])

    df["date"] = df["reftime"].apply(lambda x: parser.isoparse(x).strftime("%Y-%m-%d"))

    if pipeline_constants.REGION == pipeline_constants.AP_SOUTH_1:
        df["call_link"] = df["call_uuid"].apply(
            lambda x: f"{pipeline_constants.CONSOLE_URL}/{org_id}/call-report/#/call?uuid={x}"
        )
    else:
        df["call_link"] = df.apply(
            lambda x: f"{pipeline_constants.STUDIO_URL}/clients/{x.client_uuid}/voice-agents/{x.flow_uuid}/calls/{x.call_uuid}",
            axis=1
        )

    df["language"] = language_code
    print(df.head())
    df.to_csv("op.csv", index=False)

    print(df.columns)

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
        untagged_records_path="./emeritus_en.csv", org_id="153", language_code="en"
    )

    # fetch_calls_for_slots(
    #     untagged_records_path="./abhinav_applications_18-20-april.csv", language_code="en-US"
    # )