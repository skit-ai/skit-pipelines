
import kfp
from kfp.components import InputPath
from typing import List
from skit_pipelines import constants as pipeline_constants



def file_contents_to_markdown(
    ext: str,
    path_on_disk: InputPath(str),
    file_title: str = "",
) -> str:
    
    import pandas as pd
    from skit_pipelines import constants as const
    from loguru import logger

    final_content = ""
    
    if ext == const.CSV_FILE:
        md_content = pd.read_csv(path_on_disk, index_col=0).to_markdown()
        final_content = f"\n{file_title}\n{md_content}\n"
        
    return final_content


file_contents_to_markdown_op = kfp.components.create_component_from_func(
    file_contents_to_markdown, base_image=pipeline_constants.BASE_IMAGE
)
