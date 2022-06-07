import kfp
from kfp.components import OutputPath

from skit_pipelines import constants as pipeline_constants


def download_from_s3(
    *, storage_path: str, storage_options: str = "", output_path: OutputPath(str)
) -> None:
    import json
    import re

    import boto3
    from loguru import logger

    from skit_pipelines.api.models import StorageOptions
    from skit_pipelines.utils import create_storage_path

    pattern = re.compile(r"^s3://(.+?)/(.+?)$")
    if storage_options:
        storage_options = StorageOptions(**json.loads(storage_options))
        storage_path = create_storage_path(storage_options, storage_path)

    logger.debug(f"{storage_path=}")
    bucket, key = pattern.match(storage_path).groups()
    logger.debug(f"{bucket=} {key=}")

    s3_resource = boto3.client("s3")
    s3_resource.download_file(bucket, key, output_path)


download_from_s3_op = kfp.components.create_component_from_func(
    download_from_s3, base_image=pipeline_constants.BASE_IMAGE
)
