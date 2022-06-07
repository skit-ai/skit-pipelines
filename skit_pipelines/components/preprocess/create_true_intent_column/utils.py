import json


def pick_1st_tag(tag: str):
    try:
        tag = json.loads(tag)
        tag, *_ = json.loads(tag) if isinstance(tag, str) else tag
        return tag.get("type")
    except json.JSONDecodeError:
        return tag
