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

    import openai
    import polars as pl

    from skit_pipelines.components.identify_compliance_breaches_llm.utils import format_call, get_prompt_text, parse_calls, slice_json
    from skit_pipelines import constants as pipeline_constants
    from skit_pipelines.components import upload2s3
    from skit_pipelines.components.download_from_s3 import download_csv_from_s3

    fd_download, downloaded_file_path = tempfile.mkstemp(suffix=".csv")
    download_csv_from_s3(storage_path=s3_file_path, output_path=downloaded_file_path)
    openai.api_key = "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"

    df = pl.read_csv(downloaded_file_path)
    calls = parse_calls(df)
    prompt_text = get_prompt_text()
    calls = calls[0:5]
    outputs = []

    for call in calls:
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": prompt_text},
                    {"role": "user", "content": format_call(call)},
                ],
                temperature=0,
            )
            print(format_call(call))
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
                ]
            )
        except Exception as e:
            print("Couldn't get Gpt response because: " + str(e))

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