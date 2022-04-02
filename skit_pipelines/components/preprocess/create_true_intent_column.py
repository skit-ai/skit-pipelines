import kfp
import json
from kfp.components import InputPath, OutputPath
from skit_pipelines import constants as pipeline_constants


INTENT_Y = pipeline_constants.INTENT_Y


def pick_1st_tag(tag: str):
    tag, *_ = json.loads(tag)
    return tag.get("type")


def create_intent_labels(data_path: InputPath, save_path: OutputPath):
    import pandas as pd

    train_df = pd.read_csv(data_path)
    train_df[INTENT_Y] = train_df.tag.apply(pick_1st_tag)
    train_df.to_csv(save_path, index=False)


create_true_intent_labels_op = kfp.components.create_component_from_func(
    create_intent_labels,
    base_image=pipeline_constants.BASE_IMAGE
)
