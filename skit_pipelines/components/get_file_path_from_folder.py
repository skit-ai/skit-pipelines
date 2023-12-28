from typing import Any

import kfp

from skit_pipelines import constants as pipeline_constants

def get_file_path_from_folder(folder_path: str, target_file: str):
    import os
    all_files = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
    if target_file in all_files:
        file_path = os.path.join(folder_path, target_file)
        return file_path
    else:
        return None

get_file_path_from_folder_op = kfp.components.create_component_from_func(
    get_file_path_from_folder, base_image=pipeline_constants.BASE_IMAGE
)
