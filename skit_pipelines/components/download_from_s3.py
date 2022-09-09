import kfp
from kfp.components import OutputPath

from skit_pipelines import constants as pipeline_constants


def download_csv_from_s3(
    *,
    storage_path: str,
    output_path: OutputPath(str),
) -> None:
    import json
    import re
    import tempfile

    import boto3
    import pandas as pd
    from loguru import logger

    import skit_pipelines.constants as const
    from skit_pipelines.api.models import StorageOptions
    from skit_pipelines.utils import create_storage_path
    from skit_pipelines.utils.normalize import comma_sep_str

    pattern = re.compile(r"^s3://(.+?)/(.+?)$")
    s3_resource = boto3.client("s3")

    logger.debug(f"{storage_path=}")

    if not storage_path:
        pd.DataFrame().to_csv(output_path, index=False)
        return

    _, temp_path = tempfile.mkstemp(suffix=const.CSV_FILE)
    df = pd.DataFrame()
    for file_path in comma_sep_str(storage_path):
        logger.info(f"using {file_path=}")
        bucket, key = pattern.match(file_path).groups()
        logger.debug(f"{bucket=} {key=}")
        s3_resource.download_file(bucket, key, temp_path)
        temp_df = pd.read_csv(temp_path)
        df = pd.concat([df, temp_df])

    df.to_csv(output_path, index=False)

def download_file_from_s3(
    *,
    storage_path: str,
    storage_options: str = "",
    output_path: OutputPath(str),
) -> None:
    import json
    import re
    import tempfile

    import boto3
    import pandas as pd
    from loguru import logger

    import skit_pipelines.constants as const
    from skit_pipelines.api.models import StorageOptions
    from skit_pipelines.utils import create_storage_path
    from skit_pipelines.utils.normalize import comma_sep_str

    pattern = re.compile(r"^s3://(.+?)/(.+?)$")
    s3_resource = boto3.client("s3")

    if storage_options:
        storage_options = StorageOptions(**json.loads(storage_options))
        storage_path = create_storage_path(storage_options, storage_path)

    logger.debug(f"{storage_path=}")
    bucket, key = pattern.match(storage_path).groups()
    logger.debug(f"{bucket=} {key=}")

    s3_resource.download_file(bucket, key, output_path)


def download_directory_from_s3(
    *,
    storage_path: str,
    output_path: OutputPath(str),
) -> None:
    import json
    import re
    import tempfile

    import boto3
    from loguru import logger

    import skit_pipelines.constants as const

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
            if obj.key.endswith('/'):
                continue
            logger.debug(f"downloading file ({obj.key}) to path ({target})")
            bucket.download_file(obj.key, target)
            
    pattern = re.compile(r"^s3://(.+?)/(.+?)$")
    logger.debug(f"{storage_path=}")
    bucket, key = pattern.match(storage_path).groups()
    logger.debug(f"{bucket=} {key=}")

    s3_resource = boto3.resource("s3")
    download_s3_folder(s3_resource, bucket, key, output_path)



download_file_from_s3_op = kfp.components.create_component_from_func(
    download_file_from_s3, base_image=pipeline_constants.BASE_IMAGE
)

download_csv_from_s3_op = kfp.components.create_component_from_func(
    download_csv_from_s3, base_image=pipeline_constants.BASE_IMAGE
)

download_directory_from_s3_op = kfp.components.create_component_from_func(
    download_directory_from_s3, base_image=pipeline_constants.BASE_IMAGE
)