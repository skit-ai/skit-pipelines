import subprocess
from loguru import logger

def run_conda_python_command(command):
    try:
        logger.info(f"Running command : {command}")

        result = subprocess.run(
            command,
            check=True,
            text=True,
            shell=True,
            capture_output=True
        )

        output_lines = result.stdout.strip().splitlines()
        return output_lines
    except subprocess.CalledProcessError as e:
        logger.error(f"Error: {e}")
        return None