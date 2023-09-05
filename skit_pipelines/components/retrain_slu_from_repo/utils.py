import json
from loguru import logger


def pick_1st_tag(tag: str):
    try:
        tag = json.loads(tag)

        # if tag was applied json twice while serializing
        if isinstance(tag, str):
            tag = json.loads(tag)

        if isinstance(tag, list):
            tag = tag[0]
        elif isinstance(tag, dict):
            return tag["choices"][0]
        return tag
    except json.JSONDecodeError:
        logger.warning(
            "Couldn't obtain necessary value from tag for "
        )
        return tag
