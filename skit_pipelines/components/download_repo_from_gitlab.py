import kfp
from kfp.components import OutputPath

from skit_pipelines import constants as pipeline_constants


def download_repo_from_gitlab_func(
    project_id: int, output_path: OutputPath(str)
) -> None:

    import requests
    from loguru import logger

    url = (
        f"https://gitlab.com/api/v4/projects/",
        f"{project_id}/repository/archive?private_token="
        f"{pipeline_constants.GITLAB_PERSONAL_ACCESS_TOKEN}",
    )
    url = "".join(url)

    response = requests.get(url, stream=True)
    logger.debug(f"{response.status_code = }")

    if response.status_code == requests.codes.ok:
        with open(output_path, "wb") as f:
            f.write(response.raw.read())
        logger.info(
            f"repository {project_id} has been downloaded and written to {output_path}"
        )


download_repo_from_gitlab_op = kfp.components.create_component_from_func(
    download_repo_from_gitlab_func, base_image=pipeline_constants.BASE_IMAGE
)


if __name__ == "__main__":

    project_id = 35529988
    download_repo_from_gitlab_func(project_id, "output_dir")