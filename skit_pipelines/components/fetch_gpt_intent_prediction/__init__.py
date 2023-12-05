import kfp

from skit_pipelines import constants as pipeline_constants


def fetch_gpt_intent_prediction(
    s3_file_path: str,
    use_assisted_annotation: bool,
) -> str:
    import json
    import math
    import os
    import tempfile

    import openai
    import pandas as pd

    from skit_pipelines import constants as pipeline_constants
    from skit_pipelines.components import upload2s3
    from skit_pipelines.components.download_from_s3 import download_csv_from_s3
    from skit_pipelines.components.fetch_gpt_intent_prediction.constants import get_prompt_text

    # from skit_pipelines.components.fetch_gpt_intent_prediction import constants as gpt_constants

    def gpt_accuracy(df_row):
        if df_row["intent"] == df_row["gpt_intent"]:
            return "yes"
        return "no"

    if (
        not use_assisted_annotation
        or pipeline_constants.OPENAI_API_KEY == "KEY_NOT_SET"
    ):
        print("Skipping intent predictions by GPT")
        return s3_file_path

    openai.api_key = pipeline_constants.OPENAI_API_KEY

    print("Executing intent prediction by GPT3-davinci")
    fd_download, downloaded_file_path = tempfile.mkstemp(suffix=".csv")
    download_csv_from_s3(storage_path=s3_file_path, output_path=downloaded_file_path)
    f = pd.read_csv(downloaded_file_path)

    df = f[
        [
            "call_id",
            "call_uuid",
            "state",
            "prediction",
            "intent",
            "utterances",
            "context",
        ]
    ]
    df = df[df[["utterances"]].notnull().all(1)]
    df = df[df[["context"]].notna().all(1)]

    # TODO: Uncomment this condition once validation phrase is done
    # df = df.loc[df['intent'].isin(pipeline_constants.ALLOWED_INTENTS)]

    f["gpt_intent"] = "N/A"
    f["gpt_prob"] = 0
    f["gpt3-tokens-consumed"] = 0

    """ Not using df.apply() as rate limiter in GPT will become an issue there.
        For loops allows for easier control over the api calls """
    for i, row in df.iterrows():
        try:
            user_utterance = json.loads(row["utterances"])[0][0]["transcript"]
            bot_response = json.loads(row["context"])["bot_response"]
            conversation_context = (
                "[Bot]: " + bot_response + "  \n " + "[User]: " + user_utterance
            )

            input_text = get_prompt_text()
            input_text = input_text.replace(
                "{{conversation_context}}", conversation_context
            )
            input_text = input_text.replace("{{state}}", row["state"])
            response = openai.Completion.create(
                engine=pipeline_constants.INTENT_MODEL,
                prompt=input_text,
                max_tokens=1024,
                temperature=0,
                n=1,
                logprobs=1,
            )

            f.at[i, "gpt_intent"] = response["choices"][0]["text"]
            f.at[i, "gpt_prob"] = math.exp(
                sum(response["choices"][0]["logprobs"]["token_logprobs"][:-3])
            )
            f.at[i, "gpt3-tokens-consumed"] = response["usage"]["total_tokens"]
        except Exception as e:
            print("Couldn't get Gpt response because: " + str(e))

    f["gpt_intent"] = f["gpt_intent"].str.strip()
    # f['gpt_intent'] = f['gpt_intent'].replace({"confirm": "_confirm_", "cancel": "_cancel_"})
    f["use_gpt_intent"] = f.apply(lambda f_row: gpt_accuracy(f_row), axis=1)
    fd_upload, upload_file_path = tempfile.mkstemp(suffix=".csv")
    f.to_csv(upload_file_path, index=False)
    s3_path = upload2s3(
        upload_file_path,
        file_type=f"Gpt_intent_predictions",
        bucket=pipeline_constants.BUCKET,
        ext=".csv",
    )

    os.close(fd_download)
    os.remove(downloaded_file_path)
    os.close(fd_upload)
    os.remove(upload_file_path)

    return s3_path


fetch_gpt_intent_prediction_op = kfp.components.create_component_from_func(
    fetch_gpt_intent_prediction, base_image=pipeline_constants.BASE_IMAGE
)
