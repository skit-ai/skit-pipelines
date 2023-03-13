import json
import math
import tempfile
import os

import kfp
import openai
import pandas as pd
from kfp.components import InputPath

from skit_pipelines import constants as pipeline_constants
from skit_pipelines.components import upload2s3
from skit_pipelines.components.download_from_s3 import download_csv_from_s3

INTENT_MODEL = "text-davinci-003"
PROMPTS_FILENAME = "intent_prompts.txt"
ALLOWED_INTENTS = ['_confirm_', '_cancel_']


def get_prompts():
    f = open(PROMPTS_FILENAME, 'r')
    f.seek(0)
    prompt_text = f.read()
    f.close()
    return prompt_text


def fetch_gpt_intent_prediction(
    s3_file_path: InputPath(str),
) -> str:
    print("Function under development")

    # TODO: Move this to secrets file
    openai.api_key = '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'

    prompt_text = get_prompts()

    fd_download, downloaded_file_path = tempfile.mkstemp(suffix=".csv")
    download_csv_from_s3(storage_path=s3_file_path, output_path=downloaded_file_path)
    f = pd.read_csv(downloaded_file_path)

    df = f[["call_id", "call_uuid", "state", "prediction", "intent", "utterances", "context"]]
    df = df[df[['utterances']].notnull().all(1)]
    df = df.loc[df['intent'].isin(ALLOWED_INTENTS)]

    # TODO: Remove this condition once an official openai key is available
    df = df.head()

    df['gpt_intent'] = "N/A"
    df['gpt_prob'] = 0

    # Not using df.apply() as rate limiter in GPT will become an issue there.
    # For loops allows for easier control over the api calls
    for i, row in df.iterrows():
        utterance = row["utterances"]
        conversation_context = json.loads(utterance)[0][0]["transcript"]
        input_text = prompt_text
        input_text = input_text.replace('{{conversation_context}}', conversation_context)
        input_text = input_text.replace('{{state}}', row["state"])
        response = openai.Completion.create(engine=INTENT_MODEL, prompt=input_text, max_tokens=1024, temperature=0, n=1,
                                            logprobs=1)

        df['gpt_intent'][i] = response["choices"][0]["text"]
        df['gpt_prob'][i] = math.exp(sum(response["choices"][0]["logprobs"]["token_logprobs"][:-3]))

    fd_upload, upload_file_path = tempfile.mkstemp(suffix=".csv")
    df.to_csv(upload_file_path, index=False)
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
