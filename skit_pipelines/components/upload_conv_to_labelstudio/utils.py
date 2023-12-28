import os
import pandas as pd

def process_folder_and_save_csv(folder_path, situations_id_info):
    
    
    # _, output_csv_path = tempfile.mkstemp(suffix=".csv")
    output_csv_path = os.path.join(folder_path, "labelstudio_upload.csv")
    df = pd.DataFrame(columns=['scenario_category', 'scenario', 'situation_str', 'call'])
    situation_to_file_path_mapper = {}
    

    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)

        # Check if it's a file (not a subdirectory)
        if os.path.isfile(file_path):
            # Extract information from the file name
            parts = filename.split('_')
            if len(parts) >= 4:
                situation_id = parts[0]
                situation_to_file_path_mapper[situation_id] = file_path

    for situation in situations_id_info:
            situation_id_from_db  = situation['situation_id']
            situation_str  = situation['situation']
            scenario  = situation['scenario']
            scenario_category  = situation['scenario_category']
            if situation_id_from_db in situation_to_file_path_mapper:
                file_path_for_mapping = situation_to_file_path_mapper[situation_id_from_db]
                with open(file_path_for_mapping, 'r') as file:
                    file_content = file.read()
                    df = df.append({'scenario':scenario, 'scenario_category':scenario_category, 'situation_str':situation_str, 'call': file_content}, ignore_index=True)


    df.to_csv(output_csv_path, index=False)
    print(f"Data has been saved to {output_csv_path}")
    return output_csv_path