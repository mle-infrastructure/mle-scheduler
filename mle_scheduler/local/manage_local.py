import os
import random
import string
import shlex
import subprocess as sp
import sys

PYTHON_EXECUTABLE = (
    sys.executable
)  # local executable Python file (more reliable than `python`)


def submit_conda(
    filename: str, cmd_line_arguments: str, job_arguments: dict, debug: bool = True
):
    """Create a local job & submit it based on provided file to execute."""
    f_name, f_extension = os.path.splitext(filename)
    if f_extension == ".py":
        cmd = f"{PYTHON_EXECUTABLE} {filename} {cmd_line_arguments}"
    elif f_extension == ".sh":
        cmd = f"bash {filename} {cmd_line_arguments}"
    else:
        raise ValueError(
            f"Script with {f_extension} cannot be handled"
            " by mle-launcher. Only base .py, .sh experiments"
            " are so far implemented. Please open an issue."
        )

    try:
        env_name = job_arguments["env_name"]
        current_env = os.environ["CONDA_PREFIX"]
        if current_env != env_name:
            # activate the correct conda environment
            cmd = f"source $(conda info --base)/etc/profile.d/conda.sh \
                    && conda activate {env_name} \
                    && {cmd}"
    except Exception:
        pass
    proc = submit_subprocess(cmd, debug)
    return proc


def submit_venv(
    filename: str, cmd_line_arguments: str, job_arguments: dict, debug: bool = True
):
    """Create a local job & submit it based on provided file to execute."""
    cmd = f"{PYTHON_EXECUTABLE} {filename} {cmd_line_arguments}"
    env_name = job_arguments["env_name"]
    command_template = '/bin/bash -c "source {}/{}/bin/activate && {}"'
    cmd = shlex.split(command_template.format(os.environ["WORKON_HOME"], env_name, cmd))
    proc = submit_subprocess(cmd, debug)
    return proc


def submit_local(filename: str, cmd_line_arguments: str, debug: bool = True):
    """Create a local job & submit it based on provided file to execute."""
    cmd = f"{PYTHON_EXECUTABLE} {filename} {cmd_line_arguments}"
    proc = submit_subprocess(cmd, debug)
    return proc


def submit_subprocess(cmd: str, debug: bool = True) -> sp.Popen:
    """Submit a subprocess & return the process."""
    # Pipe stdout & stderr to separate files.
    if debug:
        cmd += " 2>>err.err 1>>log.txt"
    while True:
        try:
            proc = sp.Popen(cmd, shell=True, stdout=sp.PIPE, stderr=sp.PIPE)
            break
        except Exception:
            continue
    return proc


def random_id(length: int = 8) -> str:
    """Sample a random string to use for job id."""
    return "".join(random.sample(string.ascii_letters + string.digits, length))
