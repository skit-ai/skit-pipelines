import json
from datetime import datetime
import traceback
from tqdm import tqdm

import requests
import pytz
import pandas as pd
from dateutil.parser import parse
from typing import List
from loguru import logger

from skit_pipelines import constants as pipeline_constants


def handle_failing_value_cases(value, text, duckling_req_payload):


    # edge cases where date/time comes out as integer with duckling
    if isinstance(value, int):
        logger.warning(f"duckling predicted {value} for the payload: ")
        logger.info(str(duckling_req_payload))
        value = None
        return value

    if isinstance(value, str):
        try:
            _ = parse(value)
            return value
        except Exception as e:
            logger.exception(e)
            logger.warning(traceback.format_exc())
            logger.warning(f"duckling predicted {value} for the payload: ")
            logger.info(str(duckling_req_payload))
        
            try:
                parsed_datetime = parse(text)
                logger.debug(str(parsed_datetime))
                return parsed_datetime.strftime('%Y-%m-%dT%H:%M:%S.%f')
            except Exception as e:
                logger.exception(e)
                logger.warning(traceback.format_exc())
                logger.warning(f"dateutil tried to extract date from {text}, but failed")
                logger.info(str(duckling_req_payload))
                return None

    return value

def create_duckling_payload(
        text: str,
        dimensions : List[str],
        reference_time = None,
        locale = "en_IN",
        use_latent = False,
        timezone: str = "Asia/Kolkata"
    ):

    payload = {
        "text": text,
        "locale": locale,
        "tz": timezone,
        "dims": json.dumps(dimensions),
        "reftime": reference_time,
        "latent": use_latent,
    }

    return payload

def get_entities_from_duckling(
    text, reftime, dimensions, locale, timezone, pytz_tz
):

    # using duckling for time, date & datetime tagged types only.

    headers = {
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"
            }

    duckling_req_payload = create_duckling_payload(
        text=text,
        dimensions=dimensions,
        reference_time=reftime,
        locale=locale,
        use_latent=True,
        timezone=timezone
    )

    # pprint(duckling_req_payload)

    response = requests.post(f'http://{pipeline_constants.DUCKLING_HOST}/parse', headers=headers, data=duckling_req_payload)
    # print(response.status_code) 
    value = None

    if response.status_code == 200:

        entities_list = response.json()
        if entities_list:
            entity = entities_list[0]
            value_store = entity.get("value", {})
            if "value" in value_store:
                value = value_store["value"]
            elif "from" in value_store and "to" in value_store:
                value = {"from": value_store.get("from"), "to": value_store.get("to")}
            elif "from" in value_store:
                value = {"from": value_store.get("from")}
            elif "to" in value_store:
                value = {"to": value_store.get("to")}

            if entity["dim"] == "duration":
                normalized_value = entity.get("value", {}).get("normalized", {})
                if normalized_value.get("unit") == "second":
                    value = reftime + normalized_value.get("value")
                    try:
                        value = datetime.fromtimestamp(value / 1000, pytz_tz)
                        value = value.isoformat()
                    except ValueError:
                        value = None

            # pprint(value)
            value = handle_failing_value_cases(value, text, duckling_req_payload)

    return value

def modify_truth(df: pd.DataFrame, timezone: str = "Asia/Kolkata"):

    pytz_tz = pytz.timezone(timezone)

    for i, row in tqdm(df.iterrows(), total=len(df), desc="making duckling hits to get entity values."):

        try:
            tog_job_lang = row["raw.language"]

            datetime_without_tz = parse(row["reftime"]).replace(tzinfo=None)
            reftime = pytz_tz.localize(datetime_without_tz)
            reftime = int(reftime.timestamp() * 1000)

            if tog_job_lang == "en":
                locale = "en_IN"
            else:
                locale = tog_job_lang

            tags = json.loads(row["tag"])

            if not tags:
                continue

            tagged_entities = []

            for tag in tags:

                entity_type = tag["type"].lower()
                entity_region_tagged_text = tag["text"]

                if (not entity_type) or (not entity_region_tagged_text):
                    continue

                entity_region_tagged_text = entity_region_tagged_text.replace("~","")
                entity_value = None

                if entity_type in ["date", "time", "datetime"]:
                    dimensions = [entity_type]
                    entity_value = get_entities_from_duckling(
                        entity_region_tagged_text,
                        reftime,
                        dimensions,
                        locale,
                        timezone,
                        pytz_tz
                    )
                    if entity_value is None:
                        logger.warning(f"for {entity_region_tagged_text = } & {entity_type = } duckling predictions are not included.")
                        continue

                elif "/" in tag["type"]:
                    entity_type, entity_value = tag["type"].split("/")

                else:
                    entity_value = entity_region_tagged_text


                if entity_type and entity_value:
                    tagged_entities.append({
                        "type": entity_type,
                        "value": entity_value,
                        "text": entity_region_tagged_text,
                    })


        except Exception as e:
            logger.error(e)
            logger.error(traceback.format_exc())      

        if tagged_entities:
            df.loc[i, "truth_entities_with_duckling"] = json.dumps(tagged_entities, ensure_ascii=False) 

    return df
    