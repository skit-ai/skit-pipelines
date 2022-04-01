import kfp
import json
from kfp.components import InputPath
from skit_pipelines import constants as pipeline_constants



def pick_1st_tag_from_json_string(tag: str):
    tag, *_ = json.loads(tag)
    return tag.get("type")


def pick_single_label(data_path: InputPath):
    import pandas as pd

    train_df = pd.read_csv(data_path)
    train_df.tag = train_df.tag.apply(pick_1st_tag_from_json_string)
