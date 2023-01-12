from typing import List

import kfp
from kfp.components import InputPath

from skit_pipelines import constants as pipeline_constants


def file_contents_to_markdown_s3(
    ext: str,
    path_on_disk: InputPath(str),
    file_title: str = "",
) -> str:

    import tempfile

    import pandas as pd
    from loguru import logger

    from skit_pipelines import constants as const
    from skit_pipelines.components import upload2s3

    final_content = ""

    if ext == const.CSV_FILE:
        logger.info("file type is csv")
        md_content = pd.read_csv(path_on_disk, index_col=0).to_markdown()
        final_content = f"\n{file_title}\n{md_content}\n"

        _, file_path = tempfile.mkstemp(suffix=".md")
        with open(file_path, "w") as f:
            f.write(final_content)

        s3_path = upload2s3(
            file_path,
            reference=f"-{file_title}",
            file_type=f"MR-Description",
            bucket=const.BUCKET,
            ext=".md",
        )

        return s3_path


file_contents_to_markdown_s3_op = kfp.components.create_component_from_func(
    file_contents_to_markdown_s3, base_image=pipeline_constants.BASE_IMAGE
)
