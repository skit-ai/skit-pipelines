import json


def pick_1st_tag(tag: str):

    try:
        tag = json.loads(tag)

        # if tag was applied json twice while serializing
        if isinstance(tag, str):
            tag = json.loads(tag)
        
        # since lablestudio and tog can have more than one tags
        # for the same datapoint, we access only the first element
        # from the json array
        if isinstance(tag, list):
            tag = tag[0]


        if isinstance(tag, dict):

            # labelstudio way of extracting the first intent
            if "choices" in tag:
                return tag["choices"][0]

            # tog way of extracting the first intent
            if "type" in tag:
                return tag["type"]

    except json.JSONDecodeError:
        return tag
