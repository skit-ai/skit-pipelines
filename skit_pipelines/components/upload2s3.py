from typing import Union

import kfp
from kfp.components import InputPath

from skit_pipelines import constants as pipeline_constants


def upload2s3(
    path_on_disk: InputPath(str),
    reference: str = "",
    file_type: str = "",
    bucket: str = "",
    ext: str = ".csv",
    output_path: str = "",
    storage_options: str = "",
) -> str:
    import json
    import os
    import tarfile
    import tempfile

    import boto3
    from loguru import logger

    from skit_pipelines.api.models import StorageOptions
    from skit_pipelines.utils import create_file_name

    s3_resource = boto3.client("s3")

    if storage_options:
        storage_options = StorageOptions(**json.loads(storage_options))
        bucket = storage_options.bucket

    if os.path.isdir(path_on_disk):
        _, tar_path = tempfile.mkstemp(suffix=".tar.gz")
        with tarfile.open(tar_path, "w:gz") as tar:
            tar.add(path_on_disk)
        path_on_disk = tar_path

    upload_path = output_path or create_file_name(reference, file_type, ext)
    s3_resource.upload_file(path_on_disk, bucket, upload_path)

    s3_path = f"s3://{bucket}/{upload_path}"
    logger.debug(f"Uploaded {path_on_disk} to {upload_path}")
    return s3_path


upload2s3_op = kfp.components.create_component_from_func(
    upload2s3, base_image=pipeline_constants.BASE_IMAGE
)
