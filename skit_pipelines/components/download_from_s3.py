import kfp
from kfp.components import OutputPath

from skit_pipelines import constants as pipeline_constants

def download_from_s3(
    *, storage_path: str, storage_options: str = "", output_path: OutputPath(str), recursive: bool = False
) -> None:
    import json
    import re

    import boto3
    from loguru import logger

    from skit_pipelines.api.models import StorageOptions
    from skit_pipelines.utils import create_storage_path

    def download_s3_folder(s3_resource, bucket_name, s3_folder, local_dir=None):
        """
        Download the contents of a folder directory
        Args:
            bucket_name: the name of the s3 bucket
            s3_folder: the folder path in the s3 bucket
            local_dir: a relative or absolute directory path in the local file system
        """
        import os
        bucket = s3_resource.Bucket(bucket_name)
        for obj in bucket.objects.filter(Prefix=s3_folder):
            target = obj.key if local_dir is None \
                else os.path.join(local_dir, os.path.relpath(obj.key, s3_folder))
            if not os.path.exists(os.path.dirname(target)):
                os.makedirs(os.path.dirname(target))
            if obj.key[-1] == '/':
                continue
            logger.debug(f"downloading file ({obj.key}) to path ({target})")
            bucket.download_file(obj.key, target)

    pattern = re.compile(r"^s3://(.+?)/(.+?)$")
    if storage_options:
        storage_options = StorageOptions(**json.loads(storage_options))
        storage_path = create_storage_path(storage_options, storage_path)
    
    if not storage_path:
        logger.debug(f"storage_path was empty, placing an empty file on output_path = {output_path}")
        open(output_path,"w").close()
        return


    logger.debug(f"{storage_path=}")
    bucket, key = pattern.match(storage_path).groups()
    logger.debug(f"{bucket=} {key=}")

    if not recursive:
        s3_resource = boto3.client("s3")
        s3_resource.download_file(bucket, key, output_path)
    else:
        # s3_resource = boto3.resource('s3')
        s3_resource = boto3.resource("s3")
        download_s3_folder(s3_resource,bucket,key,output_path)


download_from_s3_op = kfp.components.create_component_from_func(
    download_from_s3, base_image=pipeline_constants.BASE_IMAGE
)
