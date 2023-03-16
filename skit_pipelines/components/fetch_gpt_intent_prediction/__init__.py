import kfp

from skit_pipelines import constants as pipeline_constants


def fetch_gpt_intent_prediction(
        s3_file_path: str,
) -> str:
    import json
    import math
    import tempfile
    import os

    import openai
    import pandas as pd

    from skit_pipelines.components import upload2s3
    from skit_pipelines.components.download_from_s3 import download_csv_from_s3
    from skit_pipelines import constants as pipeline_constants
    # from skit_pipelines.components.fetch_gpt_intent_prediction import constants as gpt_constants

    INTENT_MODEL: str = "text-davinci-003"
    ALLOWED_INTENTS = ['_confirm_', '_cancel_', '_identity_', 'inform_dob']

    PROMPT_TEXT = """In the below conversation turn between a debt collection bot and a user:

    STATE: {{state}}
    {{conversation_context}}

    If the user is answering the bot with an affirmative or confirming what the bot says (consider yep, yeah, or the like as "yes"), answer ‘_confirm_’
    If the user is denying what the bot says, answer ‘_cancel_’
    If the user is unsure, answer '_maybe_'
    If the user asks who the bot is, where the bot is calling from, or why the bot is calling, answer ‘_identity_’
    If the user requests that the bot repeat something, answer ‘_repeat_’
    If the user doesn't wish to speak to machines and robots or wants to speak to a human agent / operator / customer service / person, answer 'ask_for_agent'
    If the user is greeting the bot or saying hello, answer ‘_greeting_’
    If the user appears to be providing a 4 digit number when the bot asks for their social security number, answer 'inform_ssn_number'
    If the user appears to be providing a date when the bot asks for their date of birth , answer 'inform_dob'
    If the user is saying anything else or you are unsure of what they are saying, answer ‘Other’

    Answer:"""

    # TODO: Move this to secrets file
    openai.api_key = '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'
    prompt_text = PROMPT_TEXT

    fd_download, downloaded_file_path = tempfile.mkstemp(suffix=".csv")
    print(s3_file_path)
    download_csv_from_s3(storage_path=s3_file_path, output_path=downloaded_file_path)
    f = pd.read_csv(downloaded_file_path)

    df = f[["call_id", "call_uuid", "state", "prediction", "intent", "utterances", "context"]]
    df = df[df[['utterances']].notnull().all(1)]
    df = df.loc[df['intent'].isin(ALLOWED_INTENTS)]

    # TODO: Remove this condition once an official openai key is available
    df = df.head()

    f['gpt_intent'] = "N/A"
    f['gpt_prob'] = 0

    ''' Not using df.apply() as rate limiter in GPT will become an issue there.
        For loops allows for easier control over the api calls '''
    for i, row in df.iterrows():
        utterance = row["utterances"]
        conversation_context = json.loads(utterance)[0][0]["transcript"]
        input_text = prompt_text
        input_text = input_text.replace('{{conversation_context}}', conversation_context)
        input_text = input_text.replace('{{state}}', row["state"])
        response = openai.Completion.create(engine=INTENT_MODEL, prompt=input_text, max_tokens=1024,
                                            temperature=0, n=1,
                                            logprobs=1)

        f['gpt_intent'][i] = response["choices"][0]["text"]
        f['gpt_prob'][i] = math.exp(sum(response["choices"][0]["logprobs"]["token_logprobs"][:-3]))

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
