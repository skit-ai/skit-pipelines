import json


def pick_text_from_tag(tag: str):
    try:
        tag = json.loads(tag)["text"] if isinstance(tag, str) else tag["text"]
        return tag
    except json.JSONDecodeError:
        return tag
