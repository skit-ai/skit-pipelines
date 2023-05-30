import kfp

from skit_pipelines import constants as pipeline_constants


def identify_compliance_breaches_llm(
    s3_file_path: str,
) -> str:
    """
    Groups turns into calls and pushes them to an LLM (uses openai chatComplete functionality) to identify
    compliance breaches. The result value for each call is written in an output csv file

    param s3_file_path: Csv file containing turns for calls obtained from fsm Db
    type s3_file_path: str

    output: path of csv file containing complaince breach results for each call in the input
    """

    import os
    import tempfile
    import time

    import openai
    import polars as pl

    from skit_pipelines import constants as pipeline_constants
    from skit_pipelines.components import upload2s3
    from skit_pipelines.components.download_from_s3 import download_csv_from_s3
    from skit_pipelines.components.identify_compliance_breaches_llm.utils import (
        format_call,
        get_prompt_text,
        parse_calls,
        slice_json,
    )

    if pipeline_constants.OPENAI_COMPLIANCE_BREACHES_KEY == "KEY_NOT_SET":
        print("Skipping complaince report generation as the key is not set")
        return "key_not_set"

    fd_download, downloaded_file_path = tempfile.mkstemp(suffix=".csv")
    download_csv_from_s3(storage_path=s3_file_path, output_path=downloaded_file_path)
    openai.api_key = pipeline_constants.OPENAI_COMPLIANCE_BREACHES_KEY

    df = pl.read_csv(downloaded_file_path)
    calls = parse_calls(df)
    prompt_text = get_prompt_text()
    calls = calls[0:100]
    outputs = []

    start_time = time.time()
    for call in calls:
        try:
            call_as_string = format_call(call)
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": prompt_text},
                    {"role": "user", "content": call_as_string},
                ],
                temperature=0,
            )
            print(call_as_string)
            output = response["choices"][0]["message"]["content"]
            breach_status = slice_json(output)["breach"]
            outputs.append(
                [
                    call.id,
                    call.uuid,
                    call.audio_url,
                    call.flow_uuid,
                    call.client_uuid,
                    call.reftime,
                    breach_status,
                    output,
                    response["usage"]["total_tokens"],
                    call_as_string,
                ]
            )
        except Exception as e:
            print("Couldn't get Gpt response because: " + str(e))

    end_time = time.time()
    total_time = str(end_time - start_time)
    print("Time required to obtain compliance breaches from openai for " +
          str(len(calls)) + " calls was " + total_time + " seconds")
    columns = [
        "call_id",
        "call_uuid",
        "audio_url",
        "flow_uuid",
        "client_uuid",
        "reftime",
        "is_breach",
        "compliance_output",
        "tokens_consumed",
        "Call information"
    ]
    df_output = pl.DataFrame(outputs, schema=columns)
    fd_upload, upload_file_path = tempfile.mkstemp(suffix=".csv")
    df_output.write_csv(upload_file_path)

    s3_path = upload2s3(
        upload_file_path,
        file_type=f"llm_compliance_breaches",
        bucket=pipeline_constants.BUCKET,
        ext=".csv",
    )

    os.close(fd_upload)
    os.remove(upload_file_path)

    return s3_path


identify_compliance_breaches_llm_op = kfp.components.create_component_from_func(
    identify_compliance_breaches_llm, base_image=pipeline_constants.BASE_IMAGE
)
