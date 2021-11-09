import os
import time
from typing import Union
from .ssh_manager import SSH_Manager


def send_code_ssh(
    ssh_settings: dict,
    local_dir: Union[str, None] = None,
):
    """Helper for sending code directory to SSH server."""
    if local_dir is None:
        local_dir = os.getcwd()
    # Create manager for file sync and subprocess exec
    ssh_manager = SSH_Manager(
        user_name=ssh_settings["user_name"],
        pkey_path=ssh_settings["pkey_path"],
        main_server=ssh_settings["main_server"],
        jump_server=ssh_settings["jump_server"],
        ssh_port=ssh_settings["ssh_port"],
    )
    ssh_manager.sync_dir(local_dir, ssh_settings["remote_dir"])
    return


def copy_results_ssh(
    ssh_settings: dict,
    remote_dir: Union[str, None] = None,
    local_dir: Union[str, None] = None,
):
    """Helper for copying results directory back to local machine."""
    # Create manager for file sync and subprocess exec
    ssh_manager = SSH_Manager(
        user_name=ssh_settings["user_name"],
        pkey_path=ssh_settings["pkey_path"],
        main_server=ssh_settings["main_server"],
        jump_server=ssh_settings["jump_server"],
        ssh_port=ssh_settings["ssh_port"],
    )
    ssh_manager.get_file(remote_dir, os.getcwd())
    # os.rename(remote_dir, local_dir)
    return


def submit_ssh(
    filename: str,
    cmd_line_arguments: Union[str, None],
    job_arguments: dict,
    ssh_settings: dict,
):
    """Launch a job on an SSH server."""
    if cmd_line_arguments is None:
        cmd_line_arguments = ""
    # Write the desired python/bash execution to slurm job submission file
    f_name, f_extension = os.path.splitext(filename)
    if f_extension == ".py":
        cmd = f"python {filename} {cmd_line_arguments}"
    elif f_extension == ".sh":
        cmd = f"bash {filename} {cmd_line_arguments}"
    else:
        raise ValueError(
            f"Script with {f_extension} cannot be handled"
            " by mle-toolbox. Only base .py, .sh experiments"
            " are so far implemented. Please open an issue."
        )

    # Add conda environment activation
    script_cmd = "echo $$; /bin/bash -c 'source $(conda info --base)/etc/profile.d/conda.sh && conda activate {} && cd {} && {}'".format(
        job_arguments["env_name"], ssh_settings["remote_dir"], cmd
    )

    # Create manager for file sync and subprocess exec
    ssh_manager = SSH_Manager(
        user_name=ssh_settings["user_name"],
        pkey_path=ssh_settings["pkey_path"],
        main_server=ssh_settings["main_server"],
        jump_server=ssh_settings["jump_server"],
        ssh_port=ssh_settings["ssh_port"],
    )

    stdin, stdout, stderr = ssh_manager.execute_command([script_cmd])
    pid = int(stdout.readline())
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
    ssh_manager.delete_dir(ssh_settings["remote_dir"])
