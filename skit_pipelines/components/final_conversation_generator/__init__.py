import kfp
from kfp.components import OutputPath

from skit_pipelines import constants as pipeline_constants
from typing import Optional, List, Dict

def final_conversation_generator(
        output_path: OutputPath(str),
        situation_info_list: List[Dict[str, str]],
        s3_links_to_prompts: str,
        n_iter: int,
        n_choice: int,
        temperature: float ,
        model: str,
        llm_trainer_repo_name: str,
        llm_trainer_repo_branch: str
    ):
    
    """
    
    :param situation_info_list: list containing the id and situation mapping from the table
    :type situation_info_list: list
    
    :param s3_links_to_prompts: s3 links to the prompt to the model for data generation
    :type s3_links_to_prompts: str
    
    :param n_iter: No of times we make iterate on scenarios list to generate conversations
    :type n_iter: int
    
    :param n_choice: No of convs generated in a single time from a scenario.
    :type n_choice: int
    
    :param temperature: Temperature
    :type temperature: float
    
    :param model: Model to be used for generating data 
    :type model: str
    
    :param llm_trainer_repo_name: The conversation generation repo name in Github.
    :type llm_trainer_repo_name: str
    
    :param llm_trainer_repo_branch: The branch name in the conversation generation repo to use , defaults to main.
    :type llm_trainer_repo_branch: str, optional
    
    output: path of the txt file where conversations is stored
    """

    import tempfile

    from loguru import logger
    import json
    from skit_pipelines.components.download_from_s3 import download_file_from_s3
    from skit_pipelines.components.sample_conversations_generator import sample_conversations_generator
    
    prompt_path  = ""
    output_dir = output_path
    _, situation_save_path  = tempfile.mkstemp(suffix=".json")
    situation_dict = {}
    if s3_links_to_prompts != '':
        _, prompt_path = tempfile.mkstemp(suffix=".txt")
        download_file_from_s3(storage_path=s3_links_to_prompts, output_path=prompt_path)
        
    for data in situation_info_list:
        situation_dict[data['situation_id']] = data['situation']
        with open(situation_save_path, 'w') as json_file:
            json.dump(situation_dict, json_file, indent=2)

    sample_conversations_generator(
    situations='',
    llm_trainer_repo_name=llm_trainer_repo_name,
    llm_trainer_repo_branch=llm_trainer_repo_branch,
    output_path=output_path,
    filename='',
    model=model,
    prompt_file_path=prompt_path,
    n_iter=n_iter,
    n_choice=n_choice,
    temperature=temperature,
    situation_file_path=situation_save_path,
    )
    
    return output_dir
    
final_conversation_generator_op = kfp.components.create_component_from_func(
    final_conversation_generator, base_image=pipeline_constants.BASE_IMAGE
)
