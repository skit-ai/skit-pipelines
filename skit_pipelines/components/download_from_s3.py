import kfp
from kfp.components import InputPath, OutputPath

from skit_pipelines import constants as pipeline_constants


def download_from_s3(
    s3_path: str,
    output_path: OutputPath(str)
) -> None:
    import re
    import boto3
    from loguru import logger

    pattern = re.compile(r"^s3://(.+?)/(.+?)$")
    logger.debug(f"{s3_path=}")
    bucket, key = pattern.match(s3_path).groups()
    logger.debug(f"{bucket=} {key=}")

    s3_resource = boto3.client("s3")
    s3_resource.download_file(bucket, key, output_path)


download_from_s3_op = kfp.components.create_component_from_func(
    download_from_s3, base_image=pipeline_constants.BASE_IMAGE
)
