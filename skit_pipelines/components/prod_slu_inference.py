import kfp
from kfp.components import OutputPath
from torch import detach

# from skit_pipelines import constants as pipeline_constants

# def prod_slu_inference_func(slu_repo_tar_path: str, output_path: OutputPath(str)) -> None:
def prod_slu_inference_func(slu_repo_tar_path: str, tog_tagged_data_path : str, project_id: int) -> None:

    import os
    import tarfile
    import subprocess
    import base64

    import boto3
    import docker
    from docker.models.containers import Container
    import pandas as pd
    from loguru import logger

    with tarfile.open(slu_repo_tar_path, "r:gz") as tar:
        tar.extractall(path=f"./{project_id}/")
    
    logger.info(f"untarred {slu_repo_tar_path} to {project_id} directory")

    items_inside_tar = os.listdir(f"{project_id}")
    logger.debug(f"contents inside provided tar: {items_inside_tar}")

    branch_names = ["master", "main"]
    for item in items_inside_tar:
        path_to_item = f"./{project_id}/{item}"
        if os.path.isdir(path_to_item) and any([branch_name in item for branch_name in branch_names]):
            os.rename(path_to_item, f"./{project_id}/slu")
            logger.info(f"downloaded repo renamed from '{item}' to 'slu'")


    os.chdir(f"./{project_id}/slu/")
    logger.debug(f"shifted working directory to: {os.getcwd()}")
    slu_contents = os.listdir()
    if "poetry.lock" in slu_contents:
        logger.debug("found poetry.lock")
    elif "pyproject.toml" in slu_contents:
        logger.debug("found pyproject.toml")
    else:
        logger.error("missing both poetry.lock and pyproject.toml")
        logger.debug(f"contents within slu repo: {os.listdir()}")
    
    # poetry lib for installation
    proc = subprocess.run("poetry install", shell=True, check=True)
    print(f"[STDOUT] :: \n {proc.stdout.decode()}")
    print(f"[STDERR] :: \n {proc.stderr.decode()}")

    # docker run detach duckling, using docker-py
    # https://docker-py.readthedocs.io/en/stable/
    # but to USE AWS ECR
    docker_client = docker.from_env()

    # image name
    DUCKLING_IMAGE_NAME_ON_ECR = "536612919621.dkr.ecr.ap-south-1.amazonaws.com/vernacular-voice-services/ai/duckling:master"

    # docker image pulling from ecr
    # aws ecr get-login-password --region ap-south-1 | docker login --username AWS --password-stdin 536612919621.dkr.ecr.ap-south-1.amazonaws.com
    # docker pull 536612919621.dkr.ecr.ap-south-1.amazonaws.com/vernacular-voice-services/ai/duckling:master

    ecr_client = boto3.client('ecr', region_name='ap-south-1')
    token = ecr_client.get_authorization_token()
    username, password = base64.b64decode(token['authorizationData'][0]['authorizationToken']).decode().split(':')
    registry = token['authorizationData'][0]['proxyEndpoint']
    docker_client.login(username, password, registry=registry)

    docker_client.images.pull(DUCKLING_IMAGE_NAME_ON_ECR)
    duckling_container : Container = docker_client.containers.run(
        DUCKLING_IMAGE_NAME_ON_ECR, 
        command="./duckling-example-exe",
        detach=True, 
        ports={"8000/tcp": 8000}
    )

    api_import_file_path = "slu/src/api/endpoints.py"
    if os.path.isfile(api_import_file_path):
        logger.info(f"found: {api_import_file_path}")

    import slu.src.api.endpoints as api
    logger.info("loaded: PREDICT_API")
    print(api.PREDICT_API)

    # get dataframe input with alternatives column

    df = pd.read_csv(tog_tagged_data_path)
    tagged_region_entity_text_column_name = "text"

    df["response"] = df[tagged_region_entity_text_column_name].apply(lambda x: api.PREDICT_API(
                alternatives=x,
                # context=context,
                # intents_info=intents_info,
                # history=history,
                # lang=lang,
            ))
    # ))
    print(df["response"].head())

    duckling_container.kill()






# prod_slu_inference_func_op = kfp.components.create_component_from_func(
#     prod_slu_inference_func, base_image=pipeline_constants.BASE_IMAGE
# )


if __name__ == "__main__":

    # project_id = 32702497
    project_id = 31749390
    slu_repo_tar_path = f"{project_id}.tar.gz"
    prod_slu_inference_func(slu_repo_tar_path, project_id)