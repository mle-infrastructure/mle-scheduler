import os
import time
import shlex
from typing import Union
from .ssh_manager import SSH_Manager
from ..local import random_id


def submit_ssh(
    filename: str,
    cmd_line_arguments: str,
    job_arguments: dict,
    ssh_settings: dict,
    clean_up: bool = True,
):
    """Launch a job on an SSH server."""
    # Write the desired python/bash execution to slurm job submission file
    f_name, f_extension = os.path.splitext(filename)
    if f_extension == ".py":
        script = f"conda activate {job_arguments['env_name']} && python {filename} {cmd_line_arguments}"
    elif f_extension == ".sh":
        script = f"conda activate {job_arguments['env_name']} && bash {filename} {cmd_line_arguments}"
    else:
        raise ValueError(
            f"Script with {f_extension} cannot be handled"
            " by mle-toolbox. Only base .py, .sh experiments"
            " are so far implemented. Please open an issue."
        )

    # Put together script to execute in a python subprocess
    script_cmd = shlex.split(script)
    script_to_exec = f"""import subprocess as sp
while True:
    try:
        proc = sp.Popen({script_cmd}, shell=True, stdout=sp.PIPE, stderr=sp.PIPE)
        break
    except Exception:
        continue
    """

    # Create manager for file sync and subprocess exec
    ssh_manager = SSH_Manager(
        user_name=ssh_settings["user_name"],
        pkey_path=ssh_settings["pkey_path"],
        main_server=ssh_settings["main_server"],
        jump_server=ssh_settings["jump_server"],
        ssh_port=ssh_settings["ssh_port"],
    )

    # Store execution file in python script on server
    file_name = "submit_{0}.py".format(random_id())
    ssh_manager.write_to_file(script_to_exec, file_name)

    # Execute the job subprocess submission file
    sp_script = f"echo $$; exec python {file_name} >> log.txt"
    stdin, stdout, stderr = ssh_manager.execute_command([sp_script])
    pid = int(stdout.readline())

    if clean_up:
        ssh_manager.delete_file(file_name)

    return pid


def monitor_ssh(job_id: Union[list, int], ssh_settings: dict):
    """Check if PID is running on an SSH server."""
    # Create manager for file sync and subprocess exec
    ssh_manager = SSH_Manager(
        user_name=ssh_settings["user_name"],
        pkey_path=ssh_settings["pkey_path"],
        main_server=ssh_settings["main_server"],
        jump_server=ssh_settings["jump_server"],
        ssh_port=ssh_settings["ssh_port"],
    )
    # Check if PID is in running processes
    sp_script = f"ps -p {job_id}"

    while True:
        try:
            stdin, stdout, stderr = ssh_manager.execute_command([sp_script])
            break
        except Exception as e:
            print(e)
            time.sleep(0.5)

    # Check if job is listed in running ones
    counter = 0
    for line in stdout:
        counter += 1
    return counter > 1


def clean_up_ssh(ssh_settings: dict):
    """Delete log.txt file."""
    # Create manager for file sync and subprocess exec
    ssh_manager = SSH_Manager(
        user_name=ssh_settings["user_name"],
        pkey_path=ssh_settings["pkey_path"],
        main_server=ssh_settings["main_server"],
        jump_server=ssh_settings["jump_server"],
        ssh_port=ssh_settings["ssh_port"],
    )
    ssh_manager.delete_file("log.txt")
