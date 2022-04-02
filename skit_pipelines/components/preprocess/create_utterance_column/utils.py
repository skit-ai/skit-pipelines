import json

from skit_pipelines import constants as pipeline_constants

UTTERANCES = pipeline_constants.UTTERANCES
ALTERNATIVES = pipeline_constants.ALTERNATIVES


def build_utterance(data: str):
    data = json.loads(data)
    utterances = data.get(UTTERANCES) or data.get(ALTERNATIVES)
    return utterances if isinstance(utterances, str) else json.dumps(utterances)
