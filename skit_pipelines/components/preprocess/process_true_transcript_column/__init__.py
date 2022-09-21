import kfp
from kfp.components import InputPath, OutputPath

from skit_pipelines import constants as pipeline_constants


def process_true_transcript_labels(
    data_path: InputPath(str), true_label_column: str, output_path: OutputPath(str)
):
    import re

    import pandas as pd
    from loguru import logger

    from skit_pipelines import constants as pipeline_constants

    def process_true_transcript(transcript):
        if type(transcript) != str:
            return ""
        return re.sub(r"\<[^)]*?\>", "", transcript).strip()

    train_df = pd.read_csv(data_path)
    logger.debug("before processing:")
    logger.debug(train_df[true_label_column][:15])
    train_df[true_label_column] = train_df[true_label_column].apply(
        process_true_transcript
    )
    logger.debug("after processing:")
    logger.debug(train_df[true_label_column][:15])

    train_df.to_csv(output_path, index=False)


process_true_transcript_labels_op = kfp.components.create_component_from_func(
    process_true_transcript_labels, base_image=pipeline_constants.BASE_IMAGE
)
