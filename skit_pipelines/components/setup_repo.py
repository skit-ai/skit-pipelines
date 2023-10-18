import os
import git
import tempfile
from skit_pipelines.components.download_repo import download_repo
from skit_pipelines import constants as pipeline_constants
from skit_pipelines.components.utils import (execute_cli)
from loguru import logger


"Download a SLU repo and install all necessary dependencies (using conda) as found in its dockerfile"
def setup_utility_repo(
        repo_name, repo_branch, run_dir=None, run_cmd=None, runtime_env_var=None
):
    repo_local_path = tempfile.mkdtemp()
    download_repo(
        git_host_name=pipeline_constants.GITLAB,
        repo_name=repo_name,
        project_path=pipeline_constants.GITLAB_SLU_PROJECT_PATH,
        repo_path=repo_local_path,
    )
    os.chdir(repo_local_path)
    repo = git.Repo(".")
    repo.config_writer().set_value(
        "user", "name", pipeline_constants.GITLAB_USER
    ).release()
    repo.config_writer().set_value(
        "user", "email", pipeline_constants.GITLAB_USER_EMAIL
    ).release()

    try:
        repo.git.checkout(repo_branch)
        execute_cli(
            f"conda create -n {repo_name} -m python=3.8 -y",
        )
        os.system(". /conda/etc/profile.d/conda.sh")
        execute_cli(
            f"conda run -n {repo_name} "
            + "pip install poetry==$(grep POETRY_VER Dockerfile | awk -F= '{print $2}')",
            split=False,
        )
        execute_cli(f"conda run -n {repo_name} poetry install").check_returncode()
        if run_dir:
            os.chdir(run_dir)
        if run_cmd:
            command = f"{runtime_env_var if runtime_env_var else ''} conda run -n {repo_name} {run_cmd} &"
            logger.info(f"running command {command}")
            execute_cli(command, split=False)
        execute_cli("ps aux | grep task", split=False)

        return repo_local_path

    except Exception as exc:
        raise exc