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
    import spacy
    from presidio_analyzer import AnalyzerEngine, PatternRecognizer, Pattern
    from presidio_anonymizer import AnonymizerEngine
    from presidio_anonymizer.entities import OperatorConfig

    from skit_pipelines import constants as pipeline_constants
    from skit_pipelines.components import upload2s3
    from skit_pipelines.components.download_from_s3 import download_csv_from_s3
    from skit_pipelines.components.identify_compliance_breaches_llm.utils import (
        format_call,
        get_prompt_text,
        parse_calls,
        slice_json,
    )

    # TODO: Make text anonymizer a separate class/component
    print("Downloading spacy model for redacting text using Presidio")
    spacy.cli.download("en_core_web_lg")
    spacy.load("en_core_web_lg")
    analyzer = AnalyzerEngine()
    anonymizer = AnonymizerEngine()

    credit_number_pattern = Pattern(name="numbers_pattern", regex="\d{4}", score=0.5)
    number_recognizer = PatternRecognizer(supported_entity="NUMBER", patterns=[credit_number_pattern])
    analyzer.registry.add_recognizer(number_recognizer)

    def anonymize_text(text):
        results = analyzer.analyze(text=text,
                                   entities=["PHONE_NUMBER", "NUMBER", "PERSON"],
                                   language='en')

        anonymized_text = anonymizer.anonymize(text=text, analyzer_results=results,
                                               operators={
                                                   "PERSON": OperatorConfig("replace", {"new_value": "Lorem Ipsum"}),
                                                   "PHONE_NUMBER": OperatorConfig("replace",
                                                                                  {"new_value": "5555555555"}),
                                                   "NUMBER": OperatorConfig("replace", {"new_value": "1111"})
                                               })
        return anonymized_text.text

    if pipeline_constants.OPENAI_COMPLIANCE_BREACHES_KEY == "KEY_NOT_SET":
        print("Skipping complaince report generation as the key is not set")
        return "key_not_set"

    fd_download, downloaded_file_path = tempfile.mkstemp(suffix=".csv")
    download_csv_from_s3(storage_path=s3_file_path, output_path=downloaded_file_path)
    openai.api_key = pipeline_constants.OPENAI_COMPLIANCE_BREACHES_KEY

    df = pl.read_csv(downloaded_file_path)
    calls = parse_calls(df)
    prompt_text = get_prompt_text()
    calls = calls[0:5]
    outputs = []

    start_time = time.time()
    for call in calls:
        try:
            call_as_string = anonymize_text(format_call(call))
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
                    call.call_url,
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
        "call_url",
        "flow_uuid",
        "client_uuid",
        "reftime",
        "is_breach",
        "compliance_output",
        "tokens_consumed",
        "call_information"
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
