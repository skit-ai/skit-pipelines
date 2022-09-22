import kfp
from kfp.components import InputPath, OutputPath

from skit_pipelines import constants as pipeline_constants


def extract_true_transcript_labels_to_txt(
    data_path: InputPath(str), true_label_column: str, output_path: OutputPath(str)
):
    import pandas as pd
    from loguru import logger
    def get_str(s):
        if type(s) == str: return s
        return ""
    train_df = pd.read_csv(data_path)
    contents = "\n".join(train_df[true_label_column].apply(get_str))
    logger.debug("extracting true transcripts:")
    logger.debug("\n".join(train_df[true_label_column].iloc[:10].apply(get_str)))
    
    with open(output_path,"wt") as f:
        print(contents,file=f)


extract_true_transcript_labels_to_txt_op = kfp.components.create_component_from_func(
    extract_true_transcript_labels_to_txt, base_image=pipeline_constants.BASE_IMAGE
)
