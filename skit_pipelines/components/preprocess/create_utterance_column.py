import kfp
import json
from kfp.components import InputPath, OutputPath
from skit_pipelines import constants as pipeline_constants


UTTERANCES = pipeline_constants.UTTERANCES
ALTERNATIVES = pipeline_constants.ALTERNATIVES


def build_utterance(data: str):
    data = json.loads(data)
    utterances = data.get(UTTERANCES) or data.get(ALTERNATIVES)
    return utterances if isinstance(utterances, str) else json.dumps(utterances)


def create_utterances(data_path: InputPath, save_path: OutputPath):
    import pandas as pd

    df = pd.read_csv(data_path)
    df[UTTERANCES] = df.data.apply(build_utterance)
    df.to_csv(save_path, index=False)


create_utterances_op = kfp.components.create_component_from_func(
    create_utterances,
    base_image=pipeline_constants.BASE_IMAGE
)
