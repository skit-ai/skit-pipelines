import kfp
import json
from kfp.components import InputPath, OutputPath
from skit_pipelines import constants as pipeline_constants


def create_utterances(data_path: InputPath(str), output_path: OutputPath(str)):
    import pandas as pd
    from skit_pipelines import constants as pipeline_constants
    from skit_pipelines.components.preprocess.create_utterance_column.utils import build_utterance


    UTTERANCES = pipeline_constants.UTTERANCES

    df = pd.read_csv(data_path)
    df[UTTERANCES] = df.data.apply(build_utterance)
    df.to_csv(output_path, index=False)


create_utterances_op = kfp.components.create_component_from_func(
    create_utterances,
    base_image=pipeline_constants.BASE_IMAGE
)
