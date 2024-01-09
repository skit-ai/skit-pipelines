def get_file_path_from_folder(folder_path: str, target_file: str):
    import os
    file_path = ''
    all_files = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
    if target_file in all_files:
        file_path = os.path.join(folder_path, target_file)
    return file_path
