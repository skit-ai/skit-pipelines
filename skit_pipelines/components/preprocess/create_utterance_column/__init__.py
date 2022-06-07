import kfp
from kfp.components import InputPath, OutputPath

from skit_pipelines import constants as pipeline_constants


def create_utterances(data_path: InputPath(str), output_path: OutputPath(str)):
    import pandas as pd
    from loguru import logger

    from skit_pipelines import constants as pipeline_constants
    from skit_pipelines.components.preprocess.create_utterance_column.utils import (
        build_utterance,
    )

    UTTERANCES = pipeline_constants.UTTERANCES

    df = pd.read_csv(data_path)
    logger.debug(f"Read {len(df)} rows from {data_path}")
    df = df[df.data.notna()]
    df = df[df.tag.notna()]
    logger.debug(f"After removing rows with missing data, {len(df)} rows remain")
    df.data.dropna(inplace=True)
    df[UTTERANCES] = df.data.apply(build_utterance)
    logger.debug(df.utterances[:10])
    df.to_csv(output_path, index=False)


create_utterances_op = kfp.components.create_component_from_func(
    create_utterances, base_image=pipeline_constants.BASE_IMAGE
)
