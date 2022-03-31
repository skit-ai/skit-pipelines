import kfp
from kfp.components import InputPath

from skit_pipelines import constants as pipeline_constants


def upload2s3(
    path_on_disk: InputPath(str),
    org_id: int,
    file_type: str,
    bucket: str,
    ext: str = ".csv",
) -> str:
    import boto3
    from loguru import logger

    from skit_pipelines.utils import create_file_name

    s3_resource = boto3.client("s3")
    upload_path = create_file_name(org_id, file_type, ext)
    s3_resource.upload_file(path_on_disk, bucket, upload_path)
    logger.debug(f"Uploaded {path_on_disk} to {upload_path}")
    s3_path = f"s3://{bucket}/{upload_path}"
    return s3_path


upload2s3_op = kfp.components.create_component_from_func(
    upload2s3, base_image=pipeline_constants.BASE_IMAGE
)
