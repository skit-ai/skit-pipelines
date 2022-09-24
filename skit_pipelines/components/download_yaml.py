import kfp
from kfp.components import OutputPath

from skit_pipelines import constants as pipeline_constants

def download_yaml(git_host_name: str, yaml_path: str, output_path: OutputPath(str)):
    import traceback
    from pprint import pprint
    import requests
    import yaml
    from loguru import logger
    from urllib.parse import urljoin

    from skit_pipelines import constants as pipeline_constants
    if not yaml_path:
        logger.info("no yaml path provided")
        with open(output_path, "w") as yaml_file:
            yaml.safe_dump({}, yaml_file)
        return

    if git_host_name == pipeline_constants.GITHUB:
        try:
            yaml_url = urljoin(pipeline_constants.EEVEE_RAW_FILE_GITHUB_REPO_URL, yaml_path)
            logger.debug(f"{yaml_url=}")
            headers = requests.structures.CaseInsensitiveDict()
            headers[
                "Authorization"
            ] = f"token {pipeline_constants.PERSONAL_ACCESS_TOKEN_GITHUB}"

            response = requests.get(yaml_url, headers=headers)
            logger.info(response.status_code)
            if response.status_code == requests.codes.OK:

                loaded_yaml = yaml.safe_load(response.content)

                pprint(loaded_yaml)

                with open(output_path, "w") as yaml_file:
                    yaml.safe_dump(loaded_yaml, yaml_file)

        except Exception as e:
            logger.exception(e)
            print(traceback.print_exc())


download_yaml_op = kfp.components.create_component_from_func(
    download_yaml, base_image=pipeline_constants.BASE_IMAGE
)
