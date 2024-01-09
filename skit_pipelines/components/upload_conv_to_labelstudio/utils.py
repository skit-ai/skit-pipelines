import os
import pandas as pd
from loguru import logger

def process_folder_and_save_csv(folder_path, situations_id_info):
    output_csv_path = os.path.join(folder_path, "labelstudio_upload.csv")
    situation_to_file_path_mapper = {}

    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)

        if os.path.isfile(file_path):
            parts = filename.split('_')
            if len(parts) >= 4:
                situation_id = int(parts[0])
                situation_to_file_path_mapper.setdefault(situation_id, []).append(file_path)

    data_list = []
    for situation in situations_id_info:
        situation_id_from_db = situation['situation_id']
        situation_str = situation['situation']
        scenario = situation['scenario']
        scenario_category = situation['scenario_category']

        file_paths = situation_to_file_path_mapper.get(situation_id_from_db, [])
        for file_path in file_paths:
            with open(file_path, 'r') as file_obj:
                file_content = file_obj.read()
                data_list.append({'scenario': scenario, 'scenario_category': scenario_category, 'situation_str': situation_str, 'call': file_content})
    
    df = pd.DataFrame(data_list)
    logger.info(f"df size: {df.shape[0]}")
    df.to_csv(output_csv_path, index=False)
    print(f"Data has been saved to {output_csv_path}")
    return output_csv_path