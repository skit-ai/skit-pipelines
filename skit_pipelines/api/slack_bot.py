import json
import re
import traceback

import requests


def get_message_data(body):
    channel = body.get("event", {}).get("channel")
    ts = body.get("event", {}).get("ts")
    text = body.get("event", {}).get("text")
    return channel, ts, text


async def run_pipeline(pipeline_name, payload):
    res = requests.post(f"http://localhost:9991/skit/pipelines/run/{pipeline_name}/", json=payload)
    if res.status_code != 200:
        return f"""
Failed to create pipeline:
```
{json.dumps(res.json(), indent=2)}
```
""".strip()
    success_message = res.json().get("response")
    run_url = success_message.get("run_url")
    name = success_message.get("name")
    return f"Running <{run_url} | {name}> pipeline."


def help_message():
    return """
Currently supported commands are:

@charon run *pipeline-name*
```
{
\t"arg1": "val1",
\t"arg2": "val2",
\t...
}
```

<https://github.com/skit-ai/skit-pipelines#pipelines | Click here> to read about pipelines and their documentation.
"""


def command_parser(text):
    match = re.match(r"<@[a-zA-Z0-9]+> (run) (.*)", text, re.DOTALL)
    if match and match.group(1) and match.group(2):
        pipeline_name, code_block = [m.strip() for m in match.group(2).split("```")][:2]
        payload = json.loads(code_block)
        return match.group(1), pipeline_name, payload
    return None, None, None


def make_response(text):
    try:
        command, pipeline_name, payload = command_parser(text)
        match command:
            case "run": return run_pipeline(pipeline_name, payload)
            case _: return help_message()
    except Exception as e:
        response = help_message()
        response += f"\n\nError: {e}"
        response += f"\n\n```\n{traceback.format_exc()}\n```"
    return response
