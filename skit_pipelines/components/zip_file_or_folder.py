import os
import kfp
from kfp.components import InputPath, OutputPath
from skit_pipelines import constants as pipeline_constants


def zip_file_or_folder(path_on_disk: InputPath(str), 
                       output_path: OutputPath(str)):
    """
    Zip a file or folder.

    :param path_on_disk: Path to the file or folder to be zipped.
    :param output_path: Path to the output zip file.
    """
    import zipfile
    import os
    
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        if os.path.isfile(path_on_disk):
            zipf.write(path_on_disk, os.path.basename(path_on_disk))
        elif os.path.isdir(path_on_disk):
            for root, _, files in os.walk(path_on_disk):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, path_on_disk)
                    zipf.write(file_path, arcname=arcname)
        else:
            raise ValueError(f"Invalid input path: {path_on_disk}")
    return output_path
    

zip_file_or_folder_op = kfp.components.create_component_from_func(
    zip_file_or_folder, base_image=pipeline_constants.BASE_IMAGE
)
