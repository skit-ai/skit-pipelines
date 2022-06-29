import json

import pandas as pd
import pydash as py_

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
    feature_as_str = f" {END_TOKEN} {START_TOKEN} ".join(transcripts)
    return f"{START_TOKEN} {feature_as_str} {END_TOKEN}"


def featurize_state(state):
    return f"{START_TOKEN} {state} {END_TOKEN}"


def row2features(use_state: bool):
    def featurize(row: pd.Series):
        if UTTERANCES in row:
            utterances = json.loads(row[UTTERANCES])
            state = row[STATE] if use_state else ""
        elif ALTERNATIVES in row:
            utterances = json.loads(row[ALTERNATIVES])
            state = row[STATE] if use_state else ""
        elif "data" in row:
            data = json.loads(row.data)
            data = json.loads(data) if isinstance(data, str) else data
            utterances = data.get(UTTERANCES) or data.get(ALTERNATIVES)
            utterances = (
                json.loads(utterances) if isinstance(utterances, str) else utterances
            )
            state = data.get(STATE)
        else:
            raise ValueError(f"No utterances found in row: {row}")

        feat_utterance = featurize_utterances(utterances)
        feat_state = featurize_state(state) if use_state else ""
        return f"{feat_utterance} {feat_state}" if use_state else f"{feat_utterance}"

    return featurize
