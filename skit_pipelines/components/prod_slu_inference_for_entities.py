import traceback
import kfp
from kfp.components import InputPath, OutputPath
from tqdm import tqdm

# from skit_pipelines import constants as pipeline_constants


# def prod_slu_inference_func(slu_repo_tar_path: str, output_path: OutputPath(str)) -> None:
def prod_slu_inference_func(
    slu_image_on_ecr: str, s3_tagged_data_path: str,
    lang: str,
    use_existing_prediction: bool=True
) -> None:

    import time
    import json
    import base64

    from typing import Dict

    import boto3
    import docker
    import pandas as pd
    from docker.models.containers import Container
    from loguru import logger
    import requests
    from requests.adapters import HTTPAdapter, Retry
    from tqdm import tqdm

    SLU_HOST = "http://localhost:9002"
    NUM_MAX_RETRIES = 100
    DUCKLING_IMAGE_NAME_ON_ECR = "536612919621.dkr.ecr.ap-south-1.amazonaws.com/vernacular-voice-services/ai/duckling:master"
    SLU_ENTRYPOINT_CMD = "uwsgi --http :9002 --enable-threads --single-interpreter --threads 1 --callable=app --module slu.src.api.endpoints:app --ini uwsgi.ini"

    tqdm.pandas()

    def requests_retry_session(
        retries=3,
        backoff_factor=0.3,
        status_forcelist=(500, 502, 504),
        session=None,
    ):
        # ripped off from: https://www.peterbe.com/plog/best-practice-with-retries-with-requests
        session = session or requests.Session()
        retry = Retry(
            total=retries,
            read=retries,
            connect=retries,
            backoff_factor=backoff_factor,
            status_forcelist=status_forcelist,
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        return session


    def create_data_column(row):

        return {
            "alternatives": row["alternatives"],
            "state": row["state"],
            "reftime": row["reftime"]
        }


    def make_request_to_slu(payload: Dict) -> str:

        try:
            s = requests_retry_session(retries=NUM_MAX_RETRIES)
            r = s.post(f"{SLU_HOST}/predict/{lang}/slu", json=payload)
            time.sleep(0.01)

            if r.status_code == requests.codes.OK:
                print(r.content)
                return r.content
            else:
                logger.warning(r.status_code)
                logger.warning(r.content)

        except Exception as e:
            logger.exception(e)
            logger.exception(traceback.print_stack())
        
        # to be altered
        return json.dumps(None)


    # docker run detach duckling + slu, using docker-py
    # https://docker-py.readthedocs.io/{lang}/stable/
    docker_client = docker.from_env()

    
    try:
        logger.info("trying to authenticate and docker login with ecr credentials ...")
        ecr_client = boto3.client("ecr", region_name="ap-south-1")
        token = ecr_client.get_authorization_token()
        username, password = (
            base64.b64decode(token["authorizationData"][0]["authorizationToken"])
            .decode()
            .split(":")
        )
        registry = token["authorizationData"][0]["proxyEndpoint"]
        stat = docker_client.login(username, password, registry=registry)
        if stat:
            logger.info("successfully authenticated and docker logged-in ...")

    except Exception as e:
        logger.exception(e)
        logger.exception(traceback.print_stack())

    logger.info(f"pulling slu docker image from ECR ...")
    docker_client.images.pull(slu_image_on_ecr)
    
    logger.info(f"creating slu_container ...")
    slu_container: Container = docker_client.containers.run(
        slu_image_on_ecr,
        command=SLU_ENTRYPOINT_CMD,
        detach=True,
        environment={"SENTRY_DSN": ""},
        remove=True,
        name="slu_container",
        network="host",
        # ports={"9002/tcp": 9002}, # no need since we are using "host"
    )

    logger.info(f"pulling duckling docker image from ECR ...")
    docker_client.images.pull(DUCKLING_IMAGE_NAME_ON_ECR)
    logger.info(f"creating duckling_container ...")
    duckling_container: Container = docker_client.containers.run(
        DUCKLING_IMAGE_NAME_ON_ECR,
        command="./duckling-example-exe",
        detach=True,
        remove=True,
        name="duckling_container",
        network="host",
        # ports={"8000/tcp": 8000}, # no need since we are using "host"
    )


    try:
        logger.info(f"waiting for SLU container to accept requests ...")
        s = requests_retry_session(retries=NUM_MAX_RETRIES)
        r = s.get(SLU_HOST)

        if r.status_code == requests.codes.OK:
            logger.info("SLU server container up and running")
        else:
            logger.error("SLU failed after several retries")

    except Exception as e:
        logger.exception(e)
        logger.exception(traceback.format_stack())

    df = pd.read_csv(s3_tagged_data_path)

    df["data"] = df.apply(lambda row: create_data_column(row), axis=1)
    logger.info(f"loaded {s3_tagged_data_path}")
    logger.info(f"size of the dataset {len(df)}")

    df["tag"] = df["tag"].apply(json.loads)


    try:

        if use_existing_prediction:
            logger.info("reusing existing predictions from `data` column.")
        else:
            logger.info("making request to SLU for generating new predictions from `data` column.")
            df["prediction"] = df["data"].progress_apply(make_request_to_slu)


        # how to pass empty region tagged text?
        # skip making requests for them
        df["entity_region_tagged_text"] = df["tag"].apply(lambda x: x[0].get("text") if x else "")

        tag_as_payload = []
        for _, row in df.iterrows():
            text = row["entity_region_tagged_text"]
            payload = row["data"]
            payload.pop("alternatives")
            payload["text"] = text
            tag_as_payload.append(payload)

        df["tag_payload"] = tag_as_payload

        logger.info("making request to SLU for generating new predictions from `tag` derived text for ground-truth.")
        df["tag_but_slu_predicted"] = df["tag_payload"].progress_apply(make_request_to_slu)

        df["tag_payload"] = df["tag_payload"].apply(json.dumps)

        print(df.head())
        df.to_csv("./okok.csv")

    except Exception as e:
        logger.exception(e)
        logger.exception(traceback.format_stack())

    finally:
        duckling_container.kill()
        slu_container.kill()


# prod_slu_inference_op = kfp.components.create_component_from_func(
#     prod_slu_inference_func, base_image=pipeline_constants.BASE_IMAGE
# )


if __name__ == "__main__":

    # # kent stuff which works - keshav
    slu_image_on_ecr = "536612919621.dkr.ecr.ap-south-1.amazonaws.com/vernacular-voice-services/ai/clients/kent-uc2:master"
    entity_job_s3_path = "s3://vernacular-ml/project/73_4358/2022-06-15/73_4358-2022-06-15-tagged.csv"
    lang = "hi"

    # ashley - american finance - vinay
    # slu_image_on_ecr = "536612919621.dkr.ecr.ap-south-1.amazonaws.com/vernacular-voice-services/ai/clients/ashley:master"
    # entity_job_s3_path = "s3://vernacular-ml/project/129_3861/2022-06-14/129_3861-2022-06-14-tagged.csv"
    # lang = "en"

    # vodafone - amey
    # slu_image_on_ecr = "536612919621.dkr.ecr.ap-south-1.amazonaws.com/vernacular-voice-services/ai/clients/vodafone-test:master"
    # entity_job_s3_path = "s3://vernacular-ml/project/65_3322/2022-06-15/65_3322-2022-06-15-tagged.csv"
    # lang = "en"

    prod_slu_inference_func(slu_image_on_ecr, entity_job_s3_path, lang, use_existing_prediction=False)
