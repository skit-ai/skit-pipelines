import kfp

from pydash import py_
from kfp.components import InputPath
from skit_pipelines import constants as pipeline_constants


def get_transcript(utterance):
    return utterance.get("transcript")


def normalize_utterances(utterances, state=None):
    transcripts = map(get_transcript, py_.flatten(utterances))
    feature_set = [*transcripts, state] if state and isinstance(state, str) else transcripts
    feature_as_str = " </s> <s> ".join(feature_set)
    return f"<s> {feature_as_str} </s>"


def normalize_df_utterances(
    data_path: InputPath,
    use_state: bool = True
):
    import pandas as pd

    df = pd.read_csv(data_path)
    df.features = df.apply(
        lambda row: normalize_utterances(
            row.utterances,
            row.state if use_state else None
        )
    )


normalize_df_utterances_op = kfp.components.create_component_from_func(
    normalize_df_utterances, base_image=pipeline_constants.BASE_IMAGE
)
