import json
from typing import Dict, List

import pandas as pd
from loguru import logger
from tqdm import tqdm


def adjust_interval_values(interval_value: Dict):

    modified_interval = {}
    if isinstance(interval_value.get("from"), str):
        modified_interval["from"] = {"value": interval_value["from"]}
    if isinstance(interval_value.get("to"), str):
        modified_interval["to"] = {"value": interval_value["to"]}

    if modified_interval:
        return modified_interval

    if (
        isinstance(interval_value.get("from"), dict)
        and interval_value.get("from").get("value")
    ) or (
        isinstance(interval_value.get("to"), dict)
        and interval_value.get("to").get("value")
    ):
        return interval_value


def modify_predictions(df: pd.DataFrame):

    for idx, predicted_entities in tqdm(
        df["raw.entities"].iteritems(),
        total=len(df["raw.entities"]),
        desc="modifiying predicted entities structure.",
    ):

        modified_predictions = []

        try:
            predicted_entities: List[Dict] = json.loads(predicted_entities)
        except Exception as e:
            logger.debug(predicted_entities)
            logger.debug(e)
            continue

        for predicted_entity in predicted_entities:

            mod_pred_entity = {}

            if predicted_entity:

                entity_value = predicted_entity.get("value")
                if entity_value and isinstance(entity_value, dict):
                    if "from" in entity_value or "to" in entity_value:
                        entity_value = adjust_interval_values(entity_value)

                mod_pred_entity = {
                    "type": predicted_entity.get("entity_type")
                    or predicted_entity.get("type"),
                    "value": entity_value,
                    "text": predicted_entity.get("body"),
                }

                modified_predictions.append(mod_pred_entity)

        if modified_predictions:
            df.loc[idx, "predicted_entities_with_modifications"] = json.dumps(
                modified_predictions, ensure_ascii=False
            )

    return df
