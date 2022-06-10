import json
from skit_pipelines.constants import NAME,PREDICTION

def extract_prediction_from_data(data: str):
    data = json.loads(data)
    if isinstance(data,str):
        data = json.loads(data)
    if PREDICTION not in data: return None
    data = json.loads(data[PREDICTION])
    if NAME not in data: return None
    return data[NAME]