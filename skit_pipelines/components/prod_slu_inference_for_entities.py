import argparse
from pathlib import Path

import kfp
from kfp.components import InputPath, OutputPath

from skit_pipelines import constants as pipeline_constants


def prod_slu_inference_func(
    s3_tagged_data_path: InputPath(str),
    output_path: OutputPath(str),
    slu_image_on_ecr: str,
    lang: str,
    use_existing_prediction: bool = True,
    use_duckling: bool = False,
) -> None:

    import base64
    import json
    import time
    import traceback
    from typing import Dict, List

    import boto3
    import docker
    import pandas as pd
    import requests
    from docker.models.containers import Container
    from loguru import logger
    from requests.adapters import HTTPAdapter, Retry
    from tqdm import tqdm

    SLU_HOST = "http://localhost:9002"
    NUM_MAX_RETRIES = 10
    DUCKLING_IMAGE_NAME_ON_ECR = "536612919621.dkr.ecr.ap-south-1.amazonaws.com/vernacular-voice-services/ai/duckling:master"
    SLU_ENTRYPOINT_CMD = "uwsgi --http :9002 --enable-threads --single-interpreter --threads 1 --callable=app --module slu.src.api.endpoints:app --ini uwsgi.ini"

    tqdm.pandas()

    def remove_container_if_exists(docker_client, container_name):

        try:
            container : Container = docker_client.containers.get(container_name)
            logger.info(f"container {container_name} has been running ...")
            container.kill()
            logger.info(f"container {container_name} has been killed ...")
        except Exception as e:
            logger.warning(e)
            # logger.exception(traceback.print_stack())

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
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session

    def create_data_column(row):

        return {
            "alternatives": row["alternatives"],
            "state": row["state"],
            "reftime": row["reftime"],
        }

    def make_request_to_slu(payload: Dict, session: requests.Session) -> str:

        if not payload:
            return {}

        try:
            r = session.post(f"{SLU_HOST}/predict/{lang}/slu", json=payload)
            time.sleep(0.01)

            if r.status_code == requests.codes.OK and "message" not in r.json():
                # print(r.content)
                return r.json()
            else:
                logger.warning(r.status_code)
                logger.warning(r.content)

        except Exception as e:
            logger.exception(e)
            logger.exception(traceback.print_stack())

        return {}

    def extract_entities_from_tag_predicted(truth_predicted: Dict):

        if "response" not in truth_predicted:
            return []

        if "entities" not in truth_predicted["response"]:
            return []

        truth_entities: List = truth_predicted["response"]["entities"]

        if not isinstance(truth_entities, list) or (not truth_entities):
            return []

        first_entity: Dict = truth_entities[0]
        keys_to_be_present = ["entity_type", "value"]

        if not isinstance(first_entity, dict):
            return []

        if any([k not in first_entity for k in keys_to_be_present]):
            return []

        eevee_schema_entity = {}

        for key in keys_to_be_present:
            if first_entity.get(key) is not None:
                if key == "entity_type":
                    eevee_schema_entity["type"] = first_entity[key]
                else:
                    eevee_schema_entity[key] = first_entity[key]

        interval_types = ["date", "time", "datetime"]
        if eevee_schema_entity["type"] in interval_types and isinstance(
            eevee_schema_entity["value"], dict
        ):
            eevee_type_value = eevee_schema_entity["value"]
            to_replace_value = {}
            if isinstance(eevee_type_value.get("from"), str):
                to_replace_value["from"] = {"value": eevee_type_value.get("from")}
            if isinstance(eevee_type_value.get("to"), str):
                to_replace_value["to"] = {"value": eevee_type_value.get("to")}

            if to_replace_value:
                eevee_schema_entity["value"] = to_replace_value
            else:
                eevee_schema_entity["value"] = None

        if any(val is None for val in eevee_schema_entity.values()):
            return []

        if not eevee_schema_entity:
            return []

        return [eevee_schema_entity]

    def extract_entities_from_predicted(predicted: Dict):

        if "slots" not in predicted:
            return []

        predicted_slots: List = predicted["slots"]

        if not isinstance(predicted_slots, list) or not predicted_slots:
            return []

        first_slot: Dict = predicted_slots[0]

        if not isinstance(first_slot, dict):
            return []

        if "values" not in first_slot:
            return []

        if not first_slot["values"]:
            return []

        first_slot_values: Dict = first_slot["values"][0]

        eevee_schema_entity = {}

        keys_to_be_present = ["type", "value", "text"]
        if any([k not in first_slot_values for k in keys_to_be_present]):
            return []

        for key in keys_to_be_present:
            if first_slot_values.get(key) is not None:
                eevee_schema_entity[key] = first_slot_values[key]

        interval_types = ["date", "time", "datetime"]
        if eevee_schema_entity["type"] in interval_types and isinstance(
            eevee_schema_entity["value"], dict
        ):
            eevee_type_value = eevee_schema_entity["value"]
            to_replace_value = {}
            if isinstance(eevee_type_value.get("from"), str):
                to_replace_value["from"] = {"value": eevee_type_value.get("from")}
            if isinstance(eevee_type_value.get("to"), str):
                to_replace_value["to"] = {"value": eevee_type_value.get("to")}

            if to_replace_value:
                eevee_schema_entity["value"] = to_replace_value
            else:
                eevee_schema_entity["value"] = None

        if any(val is None for val in eevee_schema_entity.values()):
            return []

        if not eevee_schema_entity:
            return []

        return [eevee_schema_entity]

    try:

        # docker run detach duckling + slu, using docker-py
        # https://docker-py.readthedocs.io/{lang}/stable/
        docker_client = docker.from_env()

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

        remove_container_if_exists(docker_client, "slu_container")
        remove_container_if_exists(docker_client, "duckling_container")

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
            # network="host",
            ports={"9002/tcp": 9002}, # no need since we are using "host"
            # volumes={"/var/run/docker.sock": {"bind": "/var/run/docker.sock", "mode": "rw"}},
        )

        if use_duckling:
            logger.info(f"pulling duckling docker image from ECR ...")
            docker_client.images.pull(DUCKLING_IMAGE_NAME_ON_ECR)
            logger.info(f"creating duckling_container ...")
            duckling_container: Container = docker_client.containers.run(
                DUCKLING_IMAGE_NAME_ON_ECR,
                command="./duckling-example-exe",
                detach=True,
                remove=True,
                name="duckling_container",
                # network="host",
                ports={"8000/tcp": 8000}, # no need since we are using "host"
                # volumes={"/var/run/docker.sock": {"bind": "/var/run/docker.sock", "mode": "rw"}},
            )

        logger.info(f"waiting for SLU container to accept requests ...")
        s = requests_retry_session(retries=NUM_MAX_RETRIES)
        r = s.get(SLU_HOST)

        if r.status_code == requests.codes.OK:
            logger.info("SLU server container up and running")
        else:
            logger.error("SLU failed after several retries")

        df = pd.read_csv(s3_tagged_data_path)

        df["data"] = df.apply(lambda row: create_data_column(row), axis=1)
        logger.info(f"loaded {s3_tagged_data_path}")
        logger.info(f"size of the dataset {len(df)}")

        if use_existing_prediction:
            logger.info("reusing existing predictions from `data` column.")
            df["prediction"] = df["prediction"].apply(json.loads)
        else:
            logger.info(
                "making request to SLU for generating new predictions from `data` column."
            )
            session = requests_retry_session(retries=NUM_MAX_RETRIES)
            df["prediction"] = df["data"].progress_apply(
                make_request_to_slu, args=(session,)
            )

        # how to pass empty region tagged text?
        # skip making requests for them
        df["tag"] = df["tag"].apply(json.loads)
        df["entity_region_tagged_text"] = df["tag"].apply(
            lambda x: x[0].get("text") if x else ""
        )

        tag_as_payload = []
        for _, row in df.iterrows():
            text = row["entity_region_tagged_text"]
            if text:
                payload = row["data"]
                payload.pop("alternatives")
                payload["text"] = text
            else:
                payload = {}
            tag_as_payload.append(payload)

        df["tag_payload"] = tag_as_payload

        logger.info(
            "making request to SLU for generating new predictions from `tag` derived text for ground-truth."
        )
        session = requests_retry_session(retries=NUM_MAX_RETRIES)
        df["tag_but_slu_predicted"] = df["tag_payload"].progress_apply(
            make_request_to_slu, args=(session,)
        )

        df.rename(columns={"conversation_uuid": "id"}, inplace=True)
        df["true_entities"] = df["tag_but_slu_predicted"].apply(
            extract_entities_from_tag_predicted
        )
        df["pred_entities"] = df["prediction"].apply(extract_entities_from_predicted)

        # saving python object as JSON parsable string after saving to disk
        # otherwise it gets saved as string of byte string and it is not JSON parsable.
        columns_to_save_as_json = [
            "tag_payload",
            "tag_but_slu_predicted",
            "prediction",
            "true_entities",
            "pred_entities",
        ]
        for column in columns_to_save_as_json:
            df[column] = df[column].apply(json.dumps)
        print(df.head())
        print(df.columns)

        df.to_csv(output_path, index=False)

    except Exception as e:
        logger.exception(e)
        logger.exception(traceback.format_stack())

    finally:
        duckling_container.kill()
        slu_container.kill()


# prod_slu_inference_op = kfp.components.create_component_from_func(
#     prod_slu_inference_func, base_image=pipeline_constants.BASE_IMAGE
# )


def main(args):

    Path(args.output_path).parent.mkdir(parents=True, exist_ok=True)

    prod_slu_inference_func(
        args.s3_tagged_data_path,
        args.output_path,
        args.slu_image_on_ecr,
        args.lang,
        args.use_existing_prediction,
        args.use_duckling,
    )



if __name__ == "__main__":

    # # kent stuff which works - keshav
    # slu_image_on_ecr = "536612919621.dkr.ecr.ap-south-1.amazonaws.com/vernacular-voice-services/ai/clients/kent-uc2:master"
    # entity_job_s3_path = "s3://vernacular-ml/project/73_4358/2022-06-15/73_4358-2022-06-15-tagged.csv"
    # lang = "hi"
    # prod_slu_inference_func(entity_job_s3_path, "keshav-kent.csv" ,slu_image_on_ecr, lang)

    # ashley - american finance - vinay
    # slu_image_on_ecr = "536612919621.dkr.ecr.ap-south-1.amazonaws.com/vernacular-voice-services/ai/clients/ashley:master"
    # entity_job_s3_path = "s3://vernacular-ml/project/129_3861/2022-06-14/129_3861-2022-06-14-tagged.csv"
    # lang = "en"
    # prod_slu_inference_func(entity_job_s3_path, "vinay-ashley.csv" ,slu_image_on_ecr, lang, use_duckling=True)

    # vodafone - amey
    # slu_image_on_ecr = "536612919621.dkr.ecr.ap-south-1.amazonaws.com/vernacular-voice-services/ai/clients/vodafone-test:master"
    # entity_job_s3_path = (
    #     "s3://vernacular-ml/project/65_3322/2022-06-15/65_3322-2022-06-15-tagged.csv"
    # )
    # lang = "en"
    # prod_slu_inference_func(
    #     entity_job_s3_path,
    #     "amey-vodafone.csv",
    #     slu_image_on_ecr,
    #     lang,
    #     use_duckling=True,
    # )


    # s3_tagged_data_path: InputPath(str),
    # output_path: OutputPath(str),
    # slu_image_on_ecr: str,
    # lang: str,
    # use_existing_prediction: bool = True,
    # use_duckling: bool = False,


    parser = argparse.ArgumentParser(
        description="Take s3 csv file path, ecr docker image repository and perform inference ")

    parser.add_argument(
        "--s3_tagged_data_path",
        type=str,
        required=True,
    )

    parser.add_argument(
        "--output_path",
        type=str,
        required=True,
    )

    parser.add_argument(
        "--slu_image_on_ecr",
        type=str,
        help="",
        required=True,
    )

    parser.add_argument(
        "--lang",
        type=str,
        help="",
        required=True,
    )

    parser.add_argument(
        "--use_existing_prediction",
        type=bool,
        help="",
        required=False,
        default=True
    )

    parser.add_argument(
        "--use_duckling",
        type=bool,
        help="",
        required=False,
        default=True
    )

    args = parser.parse_args()
    main(args)