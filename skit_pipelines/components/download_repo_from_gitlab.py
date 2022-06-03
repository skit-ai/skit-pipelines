import kfp
from kfp.components import OutputPath

from skit_pipelines import constants as pipeline_constants

# def download_repo_from_gitlab_func(project_id: int, output_path: OutputPath(str)) -> None:
def download_repo_from_gitlab_func(project_id: int) -> None:

    import requests
    from loguru import logger
    
    url = (
        f"https://gitlab.com/api/v4/projects/",
        f"{project_id}/repository/archive?private_token="
        f"{pipeline_constants.GITLAB_PERSONAL_ACCESS_TOKEN}"
    )
    url = "".join(url)


    target_path = f"{project_id}.tar.gz"

    response = requests.get(url, stream=True)
    logger.debug(f"{response.status_code = }")

    if response.status_code == requests.codes.ok:
        with open(target_path, 'wb') as f:
            f.write(response.raw.read())
        logger.info(f"repository {project_id} has been downloaded and written to {target_path}")



# download_repo_from_gitlab_op = kfp.components.create_component_from_func(
#     download_repo_from_gitlab_func, base_image=pipeline_constants.BASE_IMAGE
# )


if __name__ == "__main__":


    # project_id = 32702497
    project_id = 31749390
    download_repo_from_gitlab_func(project_id)