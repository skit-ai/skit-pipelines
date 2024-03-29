import kfp
from kfp.components import OutputPath

from skit_pipelines import constants as pipeline_constants
from typing import Optional

def sample_conversations_generator(
        output_path: OutputPath(str),
        filename: str,
        prompt_file_path: str,
        n_iter: int,
        n_choice: int,
        temperature: float ,
        model: str,
        llm_trainer_repo_name: str,
        llm_trainer_repo_branch: str,
        situation_file_path: str = '',
        situations: str = None,
    ):
    """
    
    :param situations: situations list
    :type situations: str, Optional
    
    :param output_dir: The output directory where the generated conversations gets stored
    :type output_dir: str
    
    :param filename: Acts as a prefix to the default naming used for file
    :type filename: str
    
    :param prompt_file_path: Path to the file where prompt for data generation exists
    :type prompt_file_path: str
    
    :param n_iter: No of times we make iterate on scenarios list to generate conversations
    :type n_iter: int
    
    :param n_choice: No of convs generated in a single time from a scenario.
    :type n_choice: int
    
    :param temperature: Temperature
    :type temperature: float
    
    :param model: Model to be used for generating data 
    t:ype model: str
    
    :param llm_trainer_repo_name: The conversation generation repo name in Github.
    :type llm_trainer_repo_name: str
    
    :param llm_trainer_repo_branch: The branch name in the conversation generation repo to use , defaults to main.
    :type llm_trainer_repo_branch: str, optional
    
    output: path of the txt file where conversations is stored
    """

    import os
    import tempfile

    import git
    from loguru import logger
    from skit_pipelines.components.download_repo import download_repo
    from skit_pipelines.components.sample_conversations_generator.utils import run_conda_python_command
    from skit_pipelines import constants as pipeline_constants
    from skit_pipelines.components.utils import execute_cli
    from skit_pipelines.components.download_from_s3 import download_file_from_s3
    
    def generate_command(situation_list=None, output_dir=None, filename=None, model=None, prompt_file_path=None, n_iter=None, n_choice=None, temperature=None, situation_file_path=None):
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
        if situation_list:
            situation_list_cmd = "--situation " +  " ".join([f"'{situation}'" for situation in situation_list]) 
        else:
            situation_list_cmd = ''
            
        output_dir_cmd = f'--output_dir "{output_dir}"' if output_dir else ""
        filename_cmd = f'--filename "{filename}"' if filename else ""
        model_cmd = f'--model "{model}"' if model else ""
        prompt_file_cmd = f'--prompt_file_path "{prompt_file_path}"' if prompt_file_path else ""
        n_iter_cmd = f'--n-iter {n_iter}' if n_iter else ""
        n_choice_cmd = f'--n-choice {n_choice}' if n_choice else ""
        temperature_cmd = f'--temperature {temperature}' if temperature else ""
        situation_file_path_cmd = f'--situation_file_path "{situation_file_path}"' if situation_file_path else ""
        command = f"""python data_gen_cli.py {situation_list_cmd} {output_dir_cmd} {filename_cmd} {model_cmd} {prompt_file_cmd} {n_iter_cmd} {n_choice_cmd} {temperature_cmd} {situation_file_path_cmd} --save_prompts_to_disk"""
        
        return command.strip()
    
    logger.info(f"situation_file_path in sample_conversations_generator: {situation_file_path}")
    
    run_dir = 'data_generation/'
    logger.info(f"Situations data: {situations}")
    
    if situations:
        situations = [val.strip() for val in situations.split('::')]
    
    prompt_save_path = ''
    if prompt_file_path:
        _, prompt_save_path = tempfile.mkstemp(suffix=".txt")
        download_file_from_s3(storage_path=prompt_file_path, output_path=prompt_save_path)
        logger.info(f"Downloaded prompts at path : {prompt_save_path}")
        
    logger.info(f"Situations : {situations}")
    
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
        
        generated_command = generate_command(
        situation_list=situations,
        output_dir=output_path,
        filename=filename,
        model=model,
        prompt_file_path=prompt_save_path,
        n_iter=n_iter,
        n_choice=n_choice,
        temperature=temperature,
        situation_file_path=situation_file_path
        )
        
        print(f"Generated command : {generated_command}")
        
        command  = f"conda run -n {llm_trainer_repo_name} " + generated_command
        print(f"The final command : {command}")
        
        run_conda_python_command(command)
        
        return output_path
    
    except Exception as exc:
        logger.error(f"Error : {exc}")
        raise exc


sample_conversations_generator_op = kfp.components.create_component_from_func(
    sample_conversations_generator, base_image=pipeline_constants.BASE_IMAGE
)
