import json
import os
import re
import ast

import aiohttp
from slack_bolt import App

from skit_pipelines import constants as const


app = App(token=os.environ["SLACK_TOKEN"])


def get_reply_metadata(body):
    channel = body.get("event", {}).get("channel")
    ts = body.get("event", {}).get("ts")
    text = body.get("event", {}).get("text")
    return channel, ts, text


async def run_pipeline(pipeline_name, payload):
    async with aiohttp.ClientSession() as session:
        async with session.post(f"http://localhost:9991/skit/pipelines/run/{pipeline_name}/", json=payload) as resp:
            response_message = await resp.text()
            status_code = resp.status
    if status_code != 200:
        return f"""
Failed to create pipeline:
```
{response_message}
```
""".strip()
    success_message = response_message.get("response")
    run_url = success_message.get("run_url")
    name = success_message.get("name")
    return f"Running <{run_url}|{name}> pipeline."


def help():
    return """
Currently supported commands are:

@charon run *pipeline-name*
```
{
\t"arg1": "val1",
\t"arg2": "val2"
}
```

<https://github.com/skit-ai/skit-pipelines | List of pipelines and there documentation>
"""


def command_parser(text):
    match = re.match(r"@<[a-zA-Z0-9]+> (run) (.+)", text).group(1)
    if match:
        try:
            payload_idx = text.index("```")
            code_block = text[payload_idx:].replace("`", "")
            payload = ast.literal_eval(code_block)
            return match.group(1), match.group(2), payload
        except ValueError:
            return None, None, None
    return None, None, None


@app.event("app_mention")
async def handle_app_mention_events(body, say, logger):
    """
    This function is called when the bot (@charon) is called in any slack channel.
    If the query made by the bot is a command for fsm/tog-{push|pull},
    it pings apigateway server with a dictionary of parsed arguments, and the original request body.

    :param body: [description]
    :type body: [type]
    :param say: [description]
    :type say: [type]
    :param _: [description]
    :type _: [type]
    """
    channel_id, message_ts, text = get_reply_metadata(body)
    command, pipeline_name, payload = command_parser(text)
    match command:
        case "run"  : response = await run_pipeline(pipeline_name, payload)
        case _      : response = help()
    say(
        thread_ts=message_ts,
        channel=channel_id,
        unfurl_link=True,
        text=response,
    )
