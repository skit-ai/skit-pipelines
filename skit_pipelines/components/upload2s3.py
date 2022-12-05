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
    upload_as_directory: bool = False,
) -> str:
    import json
    import os
    import tarfile
    import tempfile

    import boto3
    from loguru import logger

    from skit_pipelines.api.models import StorageOptions
    from skit_pipelines.utils import create_file_name

    def upload_s3_folder(s3_resource, bucket, path_on_disk, upload_path):
        for root, dirs, files in os.walk(path_on_disk):
            for file in files:
                middle_part = os.path.relpath(root, path_on_disk)
                middle_part = "" if middle_part == "." else middle_part
                s3_resource.upload_file(
                    os.path.join(root, file),
                    bucket,
                    os.path.join(upload_path, middle_part, file),
                )
                logger.debug(
                    f"Uploaded ({os.path.join(root, file)}) to ({os.path.join(upload_path, middle_part, file)})"
                )

    s3_resource = boto3.client("s3")

    if upload_as_directory and ext:
        raise ValueError("`upload_as_directory` can not be set with a non-empty `ext`")

    if storage_options:
        storage_options = StorageOptions(**json.loads(storage_options))
        bucket = storage_options.bucket

    if os.path.isdir(path_on_disk) and not upload_as_directory:
        _, tar_path = tempfile.mkstemp(suffix=".tar.gz")
        with tarfile.open(tar_path, "w:gz") as tar:
            tar.add(path_on_disk)
        path_on_disk = tar_path

    upload_path = output_path or create_file_name(reference, file_type, ext)
    if not upload_as_directory:
        s3_resource.upload_file(path_on_disk, bucket, upload_path)
    else:
        upload_s3_folder(s3_resource, bucket, path_on_disk, upload_path)

    s3_path = f"s3://{bucket}/{upload_path}"
    logger.debug(f"Uploaded {path_on_disk} to {upload_path}")
    return s3_path


upload2s3_op = kfp.components.create_component_from_func(
    upload2s3, base_image=pipeline_constants.BASE_IMAGE
)
