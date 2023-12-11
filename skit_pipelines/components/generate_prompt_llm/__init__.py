import kfp
from kfp.components import OutputPath

from skit_pipelines import constants as pipeline_constants
from typing import List


def generate_prompt_llm(
        output_path: OutputPath(str),
        situation: List[str],
        output_dir: str,
        filename: str,
        prompt: str,
        n_iter: int = 1,
        n_choice: int = 2,
        temperature: float = 0.99,
        model: str = 'gpt-4',
        llm_trainer_repo_name: str = "LLMtrainer" ,
        llm_trainer_repo_branch: str = "generate_prompt_refactor"
    ):
    """
    
    param situation: Situation list
    type situation: str, Optional
    
    param output_dir: The output directory where the generated prompts gets stored
    type output_dir: str
    
    param filename: Acts as a prefix to the default naming used for file
    type filename: str
    
    param prompt: Prompt to the model for data generation
    type prompt: str
    
    param n_iter: No of times we make iterate on situation list to generate conversations
    type n_iter: int
    
    param n_choice: No of convs generated in a single time from a situation.
    type n_choice: int
    
    param temperature: Temperature
    type temperature: float
    
    param model: Model to be used for generating data 
    type model: str
    
    param llm_trainer_repo_name: Csv file containing turns for calls obtained from fsm Db
    type llm_trainer_repo_name: str
    
    param llm_trainer_repo_branch: Csv file containing turns for calls obtained from fsm Db
    type llm_trainer_repo_branch: str
    
    output: path of the txt file where conversations is stored
    """

    import os
    import tempfile

    import git
    from loguru import logger
    import json
    import sys
    import time
    from skit_pipelines.components.download_repo import download_repo
    from skit_pipelines.components.generate_prompt_llm.utils import execute_cli, run_conda_python_command
    from skit_pipelines.components import upload2s3
    from skit_pipelines import constants as pipeline_constants
    
    def generate_command(situation_list=None, output_dir=None, filename=None, model=None, prompt=None, n_iter=None, n_choice=None, temperature=None):
        """
        Generate a command string based on the provided parameters.

        Args:
            situation_list (list or None): List of situations.
            output_dir (str or None): Output directory.
            filename (str or None): Filename.
            model (str or None): Model name.
            prompt (str or None): Prompt text.
            n_iter (int or None): Number of iterations.
            n_choice (int or None): Number of choices.
            temperature (float): Temperature.

        Returns:
            str: Generated command string.
        """
        situation_list_cmd = "--situation " +  " ".join([f"'{situation}'" for situation in situation_list]) if situation_list else ""
        output_dir_cmd = f'--output_dir "{output_dir}"' if output_dir else ""
        filename_cmd = f'--filename "{filename}"' if filename else ""
        model_cmd = f'--model "{model}"' if model else ""
        prompt_cmd = f'--prompt "{prompt}"' if prompt else ""
        n_iter_cmd = f'--n-iter {n_iter}' if n_iter else ""
        n_choice_cmd = f'--n-choice {n_choice}' if n_choice else ""
        temperature_cmd = f'--temperature {temperature}' if temperature else ""

        command = f"python data_gen_cli.py {situation_list_cmd} {output_dir_cmd} {filename_cmd} {model_cmd} {prompt_cmd} {n_iter_cmd} {n_choice_cmd} {temperature_cmd}"
        return command.strip()

    
    if not situation:
        logger.debug(f"Situations is not passed. situations: {situation}")
        return None
    
    run_dir = 'data_generation/'
    
    repo_local_path = tempfile.mkdtemp()
    download_repo(
        git_host_name=pipeline_constants.GITHUB,
        repo_name=llm_trainer_repo_name,
        project_path=pipeline_constants.GITHUB_PROJECT_PATH,
        repo_path=repo_local_path,
    )
    os.chdir(repo_local_path)
    repo = git.Repo(".")
    try:
        repo.git.checkout(llm_trainer_repo_branch)
        os.chdir(run_dir)
        execute_cli(
            f"conda create -n {llm_trainer_repo_name} -m python=3.9 -y",
        )
        os.system(". /conda/etc/profile.d/conda.sh")
        execute_cli(
            f"conda run -n {llm_trainer_repo_name} "
            + "conda install openai",
            split=False,
        )
        
        os.mkdir(output_path)
        
        output_dir = output_path
        
        generated_command = generate_command(
        situation_list=situation,
        output_dir=output_dir,
        filename=filename,
        model=model,
        prompt=prompt,
        n_iter=n_iter,
        n_choice=n_choice,
        temperature=temperature)
        
        command  = f"conda run -n {llm_trainer_repo_name} " + generated_command
        
        print(f"The final command : {command}")
        
        run_conda_python_command(command)
        
        return output_path
    except Exception as exc:
        logger.error(f"Error : {exc}")
        raise exc


generate_prompt_llm_op = kfp.components.create_component_from_func(
    generate_prompt_llm, base_image=pipeline_constants.BASE_IMAGE
)
