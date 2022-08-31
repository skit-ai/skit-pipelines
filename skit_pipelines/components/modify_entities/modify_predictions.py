
import pandas as pd
from tqdm import tqdm
import json

from typing import List, Dict


def modify_predictions(df: pd.DataFrame):

    for idx, predicted_entities in tqdm(df["raw.entities"].iteritems(), total=len(df["raw.entities"]), desc="modifiying predicted entities structure."):

        modified_predictions = []
        predicted_entities : List[Dict] = json.loads(predicted_entities)

        for predicted_entity in predicted_entities:

            mod_pred_entity = {}

            if predicted_entity:
                mod_pred_entity = {
                    "type": predicted_entity.get("entity_type") or predicted_entity.get("type"),
                    "value": predicted_entity.get("value"),
                    "text": predicted_entity.get("body"),
                }

                modified_predictions.append(mod_pred_entity)
        
        if modified_predictions:
            df.loc[idx, "predicted_entities_with_modifications"] = json.dumps(modified_predictions, ensure_ascii=False)

    return df