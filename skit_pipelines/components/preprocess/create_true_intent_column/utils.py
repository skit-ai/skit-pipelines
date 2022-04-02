import json


def pick_1st_tag(tag: str):
    tag, *_ = json.loads(tag)
    return tag.get("type")
