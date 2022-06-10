import json
import re
import traceback
from typing import Any, Dict

import requests


def get_message_data(body: Dict[str, Any]):
    """
    A message from a user to the slack bot.

    Removing attributes other than :code:`event` for brevity, even within
    :code:`event.blocks` is redacted. It is helpful for markdown content that
    users may send.

    .. code-block:: json

        {
            "event": {
                "client_msg_id": "<UUID>",
                "type": "message",
                "text": "help",
                "user": "[A-Z0-9]+",
                "ts": "1654862590.595759",
                "team": "[A-Z0-9]+",
                "blocks": [{}],
                "channel": "[A-Z0-9]+",
                "event_ts": "1654862590.595759",
                "channel_type": "im"
            }
        }

    :param body: The message event.
    :type body: 
    :return: _description_
    :rtype: _type_
    """
    channel = body.get("event", {}).get("channel")
    ts = body.get("event", {}).get("ts")
    text = body.get("event", {}).get("text")
    user = body.get("event", {}).get("user")
    user = f"<@{user}>"
    return channel, ts, text, user


def run_pipeline(pipeline_name, payload, channel_id, message_ts, user):
    if "channel" not in payload:
        payload["channel"] = channel_id

    if "notify" not in payload:
        payload["notify"] = user
    else:
        payload["notify"] += f", {user}"

    res = requests.post(
        f"http://localhost:9991/skit/pipelines/run/{pipeline_name}/", json=payload
    )
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
    return f"Running <{run_url}|{name}>."


def help_message():
    return "<https://skit-ai.github.io/skit-pipelines/#pipelines|Click here> to read about pipelines"


def command_parser(text):
    match = re.match(r"<@[a-zA-Z0-9]+> (run) (.*)", text, re.DOTALL)
    if match and match.group(1) and match.group(2):
        pipeline_name, code_block = [m.strip() for m in match.group(2).split("```")][:2]
        payload = json.loads(code_block)
        for k, v in payload.items():
            if isinstance(v, str):
                payload[k] = v.lstrip("<").rstrip(">")
        return match.group(1), pipeline_name, payload
    return None, None, None


def make_response(channel_id, message_ts, text, user):
    try:
        command, pipeline_name, payload = command_parser(text)
        match command:
            case "run":
                return run_pipeline(pipeline_name, payload, channel_id, message_ts, user)
            case _:
                return help_message()
    except Exception as e:
        response = help_message()
        response += f"\n\nError: {e}"
        response += f"\n\n```\n{traceback.format_exc()}\n```"
    return response
