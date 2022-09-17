import base64
import os
import re
import traceback
from typing import Any, Dict, Tuple, Union
from urllib.parse import urljoin

import requests
from jsoncomment import JsonComment
from loguru import logger

import skit_pipelines.constants as const

json = JsonComment()
CommandType = Union[str, None]
PipelineNameType = Union[str, None]
PayloadType = Union[Dict[str, Any], None]


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


def authenticate_bot():
    payload = {"username": const.KF_USERNAME, "password": const.KF_PASSWORD}

    resp = requests.post(urljoin("http://localhost:9991/", "token"), data=payload)
    with open(const.ACCESS_TOKEN_PATH, "w") as f:
        json.dump(resp.json(), f, indent=2)


def read_access_token(token_fetch=False) -> str:

    if not os.path.exists(const.ACCESS_TOKEN_PATH) or token_fetch:
        authenticate_bot()
    with open(const.ACCESS_TOKEN_PATH, "r") as f:
        token = json.load(f).get("access_token")
    return token


def make_run_requests(url_path, payload, access_token):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
    }
    return requests.post(url_path, json=payload, headers=headers)


def run_pipeline(pipeline_name, payload, channel_id=None, message_ts=None, user=None):
    if "channel" not in payload:
        payload["channel"] = channel_id
        payload["slack_thread"] = message_ts

    payload["notify"] = (
        user if "notify" not in payload else f"{payload['notify']} ,{user}"
    )
    url_path = f"http://localhost:9991/skit/pipelines/run/{pipeline_name}/"
    access_token = read_access_token()
    res = make_run_requests(url_path, payload, access_token)

    if res.status_code == 401:
        new_access_token = read_access_token(token_fetch=True)
        res = make_run_requests(url_path, payload, new_access_token)

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


def recurr_run_format(
    pipeline_name: str, encoded_payload: str, channel_id: str, message_ts, user
):
    return f"""
To create a recurring run of {pipeline_name} use:
```/remind {const.DEFAULT_CHANNEL} "@{const.SLACK_BOT_NAME} run {pipeline_name} b64_{encoded_payload}" <In ten minutes/30 May/Every Tuesday>```
"""


def help_message():
    return "<https://skit-ai.github.io/skit-pipelines/#pipelines|Click here> to read about pipelines"


def encode_payload(payload: PayloadType) -> str:
    """
    Encodes a JSON to base64 string

    :param payload: A JSON payload.
    :type payload: PayloadType
    :return: BASE64 encoded payload.
    :rtype: str
    """

    return base64.b64encode(json.dumps(payload).encode("utf-8")).decode("utf-8")


def decode_payload(encoded_payload: str) -> PayloadType:
    """
    Decodes a base64 string to JSON

    :param encoded_payload: A base64 string.
    :type encoded_payload: str
    :return: decoded JSON.
    :rtype: PayloadType
    """

    return json.loads(base64.b64decode(encoded_payload.encode("utf-8")).decode("utf-8"))


def command_parser(text: str) -> Tuple[CommandType, PipelineNameType, PayloadType]:
    """
    Parses pipeline run commands.

    .. note:: We assume commands to follow the following template:

        @slackbot run <pipeline_name>
        ```
        {
        "param_1": "value",
        }
        ```

    This allows us to parse the pipeline name and arguments conveniently but there are certain
    pitfalls we need to keep in mind.

    1. We slack markdown auto-format for links. if the value is a link it will be automatically formatted
        by slack and users have no way to remove it in the code-blocks. Either way it leads to poor UX. The
        link format is either <link> or <link|description>.

    2. KFP doesn't like arguments other than strings and numbers. So for pipelines that may need dictionaries, we serialize
        the dictionary to JSON and pass it as a string. This is inconvenient because users need to remember escaping strings,
        the payload quickly becomes unreadable in case of any nesting.

    We handle [1] by parsing the markdown and using only the link since that's the user's expectation.
    For [2] we require users to pass indented, neat, dictionaries. The serialization is done here so that pipelines are happy.

    :param text: The command text.
    :type text: str
    :return: The command, pipeline name, and payload.
    :rtype: Tuple[str]
    """

    logger.info(f"text sent to slackbot - {text=}")
    match = re.search(
        r"<@[a-zA-Z0-9|a-zA-Z0-9]+>[\n\r\s]+(run|create_recurring)[\n\r\s]+(.*)",
        text,
        re.DOTALL,
    )
    b64_match = re.search(
        r"(b64_(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?)",
        text,
        re.DOTALL,
    )

    if match:
        run_type, remaining_params = match.group(1), match.group(2).rstrip(".")
        if run_type and remaining_params:
            if b64_match and (encoded_payload := b64_match.group(1)):
                pipeline_name = remaining_params.replace(encoded_payload, "").strip()
                try:
                    payload = decode_payload(encoded_payload.replace("b64_", ""))
                except json.JSONDecodeError as e:
                    raise SyntaxError(
                        f"The {encoded_payload=} isn't a valid b64 encoded json: {e}"
                    )
            else:
                pipeline_name, code_block = [
                    m.strip() for m in remaining_params.split("```")
                ][:2]
                try:
                    payload = json.loads(code_block)
                except (SyntaxError, ValueError) as e:
                    raise SyntaxError(f"The {code_block=} isn't a valid json: {e}")

            for k, v in payload.items():
                if isinstance(v, str):
                    if v.startswith("<") and v.endswith(">"):
                        payload[k] = v.lstrip("<").rstrip(">").split("|")[0]
                if isinstance(v, (dict, list)):
                    payload[k] = json.dumps(v)
            return run_type, pipeline_name, payload
    return None, None, None


def make_response(channel_id, message_ts, text, user):
    """
    Makes response for a given command in text.

    To schedule a run one can do -

    ```
    @charon create_recurring <pipeline_name> <json parameters inside blockquote>
    ```

    then it'll respond with -

    ```
    To create a recurring run of <pipeline_name> use:
    /remind #bots "@charon run <pipeline_name> <encoded parameters>" <In ten minutes/30 May/Every Tuesday/etc>
    ```

    copy paste and change the `time` depending on when pipeline should run, this will trigger slackbot reminders -> make the pipeline run accordingly.
    """
    try:
        command, pipeline_name, payload = command_parser(text)
        if command == "run":
            return run_pipeline(pipeline_name, payload, channel_id, message_ts, user)
        elif command == "create_recurring":
            b64_payload = encode_payload(payload)
            return recurr_run_format(
                pipeline_name, b64_payload, channel_id, message_ts, user
            )
        else:
            return help_message()
    except Exception as e:
        response = help_message()
        response += f"\n\nError: {e}"
        response += f"\n\n```\n{traceback.format_exc()}\n```"
    return response
