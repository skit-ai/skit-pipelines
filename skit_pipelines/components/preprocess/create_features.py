import json

import kfp
from kfp.components import InputPath, OutputPath
from pydash import py_

from skit_pipelines import constants as pipeline_constants


UTTERANCES = pipeline_constants.UTTERANCES
ALTERNATIVES = pipeline_constants.ALTERNATIVES
STATE = pipeline_constants.STATE
TAG = pipeline_constants.TAG
TRAIN = pipeline_constants.TRAIN
START_TOKEN = pipeline_constants.START_TOKEN
END_TOKEN = pipeline_constants.END_TOKEN
TRANSCRIPT = pipeline_constants.TRANSCRIPT


def get_transcript(utterance):
    return utterance.get(TRANSCRIPT)


def featurize_utterances(utterances):
    transcripts = map(get_transcript, py_.flatten(utterances))
    feature_as_str = " {END_TOKEN} {START_TOKEN} ".join(transcripts)
    return f"{START_TOKEN} {feature_as_str} {END_TOKEN}"


def featurize_state(state):
    return f"{START_TOKEN} {state} {END_TOKEN}"


def row2features(use_state: bool):
    def featurize(row):
        data            = json.loads(row.data)
        utterances      = data.get(UTTERANCES) or data.get(ALTERNATIVES)
        utterances      = json.loads(utterances) if isinstance(utterances, str) else utterances
        feat_utterance  = featurize_utterances(utterances)
        feat_state      = featurize_state(data.get(STATE))
        return f"{feat_utterance} {feat_state}" if use_state else f"{feat_utterance}"
    return featurize


def create_features(
    data_path: InputPath,
    use_state: bool,
    output_path: OutputPath,
    mode: str = TRAIN
):
    import pandas as pd

    df = pd.read_csv(data_path)
    subset = (UTTERANCES, TAG) if mode == TRAIN else (TAG,)

    df.dropna(subset=subset, inplace=True, axis=1)
    df.utterances = df.apply(row2features(use_state, mode))
    df.to_csv(output_path, index=False)


create_features_op = kfp.components.create_component_from_func(
    create_features,
    base_image=pipeline_constants.BASE_IMAGE
)
