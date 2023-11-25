import kfp
from kfp.components import InputPath, OutputPath

from skit_pipelines import constants as pipeline_constants


def re_presign_s3_urls(
    audio_data_path: InputPath(str),
    output_path: OutputPath(str),
) -> None:

    import pandas as pd
    from loguru import logger
    from tqdm import tqdm

    from skit_pipelines.utils import re_presign_audio_url_if_required

    tqdm.pandas()

    df = pd.read_csv(audio_data_path)
    
    logger.info(f"attempting to re_presign {df.shape[0]} s3 http turn audios ...")
    df["audio_url"] = df["audio_url"].progress_apply(re_presign_audio_url_if_required)
    logger.info("finished re_presigning..")

    df.to_csv(output_path, index=False)


re_presign_s3_urls_op = kfp.components.create_component_from_func(
    re_presign_s3_urls, base_image=pipeline_constants.BASE_IMAGE
)

# if __name__ == "__main__":
#     re_presign_s3_urls("./lohith.csv", "./lohith_newly_signed.csv")
