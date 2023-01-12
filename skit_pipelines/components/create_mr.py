from wsgiref import headers

import kfp
from kfp.components import OutputPath

from skit_pipelines import constants as pipeline_constants


def create_mr(
    git_host_name: str,
    repo_name: str,
    project_path: str,
    target_branch: str,
    source_branch: str,
    mr_title: str,
    s3_description_paths: str,
) -> str:
    import tempfile
    from urllib.parse import urljoin

    import requests
    from loguru import logger

    from skit_pipelines import constants as const
    from skit_pipelines.components.download_from_s3 import download_file_from_s3
    from skit_pipelines.utils.normalize import comma_sep_str

    def get_description(s3_description_paths: str) -> str:
        description = ""
        s3_paths = comma_sep_str(s3_description_paths)
        for s3_path in s3_paths:
            _, save_path = tempfile.mkstemp(suffix=".md")
            download_file_from_s3(storage_path=s3_path, output_path=save_path)
            with open(save_path, "r") as f:
                description += f.read()
        return description

    if git_host_name == const.GITLAB:
        URL = (
            urljoin(
                const.GITLAB_API_BASE, f"{project_path}/{repo_name}".replace("/", "%2F")
            )
            + "/merge_requests?"
        )
        headers = {"PRIVATE-TOKEN": const.GITLAB_PRIVATE_TOKEN}
        payload = {
            "title": mr_title,
            "source_branch": source_branch,
            "target_branch": target_branch,
            "description": get_description(s3_description_paths),
            "remove_source_branch": True,
        }
        logger.info(f"URL: {URL}")
        resp = requests.post(url=URL, data=payload, headers=headers)

        if resp.status_code in [200, 201]:
            web_url = resp.json()["web_url"]
            logger.info("Created MR successfully!")
            return web_url
        else:
            logger.error(f"{resp.status_code}, {resp.text}")
            raise ValueError("Failed to create MR")


create_mr_op = kfp.components.create_component_from_func(
    create_mr, base_image=pipeline_constants.BASE_IMAGE
)
