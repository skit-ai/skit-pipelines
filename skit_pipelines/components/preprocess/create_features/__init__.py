import kfp
from kfp.components import InputPath, OutputPath

from skit_pipelines import constants as pipeline_constants


def create_features(*,
    data_path: InputPath(str),
    use_state: bool,
    output_path: OutputPath(str),
    mode: str = "train",
):
    import pandas as pd
    from loguru import logger

    from skit_pipelines import constants as pipeline_constants
    from skit_pipelines.components.preprocess.create_features.utils import row2features

    UTTERANCES = pipeline_constants.UTTERANCES
    INTENT_Y = pipeline_constants.INTENT_Y
    TRAIN = pipeline_constants.TRAIN

    df = pd.read_csv(data_path)
    subset = (UTTERANCES, INTENT_Y) if mode == TRAIN else (INTENT_Y,)

    df.dropna(subset=subset, inplace=True)
    df["utterances"] = df.apply(row2features(use_state), axis=1)
    logger.debug(df.utterances[:10])

    df.to_csv(output_path, index=False)


create_features_op = kfp.components.create_component_from_func(
    create_features, base_image=pipeline_constants.BASE_IMAGE
)
