import kfp
from kfp.components import InputPath, OutputPath
from skit_pipelines import constants as pipeline_constants


def create_features(
    data_path: InputPath,
    use_state: bool,
    output_path: OutputPath,
    mode: str = pipeline_constants.TRAIN
):
    import pandas as pd
    from skit_pipelines import constants as pipeline_constants
    from skit_pipelines.components.preprocess.create_features.utils import row2features

    UTTERANCES = pipeline_constants.UTTERANCES
    TAG = pipeline_constants.TAG
    TRAIN = pipeline_constants.TRAIN

    df = pd.read_csv(data_path)
    subset = (UTTERANCES, TAG) if mode == TRAIN else (TAG,)

    df.dropna(subset=subset, inplace=True, axis=1)
    df.utterances = df.apply(row2features(use_state, mode))
    df.to_csv(output_path, index=False)


create_features_op = kfp.components.create_component_from_func(
    create_features,
    base_image=pipeline_constants.BASE_IMAGE
)
