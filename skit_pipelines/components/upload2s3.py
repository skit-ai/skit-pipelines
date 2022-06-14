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
    from glob import glob

    import boto3
    from loguru import logger

    from skit_pipelines.api.models import StorageOptions
    from skit_pipelines.utils import (
        create_dir_name,
        create_file_name,
        create_storage_path,
    )

    s3_resource = boto3.client("s3")

    if storage_options:
        storage_options = StorageOptions(**json.loads(storage_options))
        bucket = storage_options.bucket

    if os.path.isfile(path_on_disk):
        upload_path = output_path or create_file_name(reference, file_type, ext)
        s3_resource.upload_file(path_on_disk, bucket, upload_path)
    elif os.path.isdir(path_on_disk):
        upload_path = output_path or create_dir_name(reference, file_type)
        if upload_path.startswith("s3://"):
            object_path = upload_path.replace(f"s3://{bucket}/", "")
        else:
            object_path = upload_path
        for file_on_disk in glob(f"{path_on_disk}/**", recursive=True):
            if not os.path.isfile(file_on_disk):
                continue
            _, file_path = os.path.split(file_on_disk)
            s3_resource.upload_file(
                file_on_disk, bucket, os.path.join(object_path, file_path)
            )

    s3_path = output_path or f"s3://{bucket}/{upload_path}"
    logger.debug(f"Uploaded {path_on_disk} to {upload_path}")
    return s3_path


upload2s3_op = kfp.components.create_component_from_func(
    upload2s3, base_image=pipeline_constants.BASE_IMAGE
)
