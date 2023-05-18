import kfp
from kfp.components import OutputPath

from skit_pipelines import constants as pipeline_constants


def download_repo(
    *, git_host_name: str, repo_name: str, project_path: str, output_path: str
) -> str:
    import os

    import git
    from loguru import logger

    from skit_pipelines import constants as pipeline_constants
    logger.info(f"Cloning in {output_path}")
    if git_host_name == pipeline_constants.GITLAB:
        repo_url = pipeline_constants.GET_GITLAB_REPO_URL(
            repo_name=repo_name,
            project_path=project_path,
            user=pipeline_constants.GITLAB_USER,
            token=pipeline_constants.GITLAB_PRIVATE_TOKEN,
        )
        repo = git.Repo.clone_from(url=repo_url, to_path=output_path)

        logger.info(f"{output_path}, {os.listdir(output_path)}")
        logger.info("cloned successfully!")

        return output_path


download_repo_op = kfp.components.create_component_from_func(
    download_repo, base_image=pipeline_constants.BASE_IMAGE
)
