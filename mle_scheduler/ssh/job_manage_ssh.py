import os
import time
from typing import Union
from .ssh_manager import SSH_Manager
from .helpers_launch_ssh import ssh_get_submission_cmd


def submit_ssh(
    filename: str,
    cmd_line_arguments: Union[str, None],
    job_arguments: dict,
    ssh_settings: dict,
):
    """Launch a job on an SSH server."""
    # Create bash script string
    script_cmd = ssh_get_submission_cmd(
        filename, cmd_line_arguments, job_arguments, ssh_settings
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


def send_dir_ssh(
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


def copy_dir_ssh(
    ssh_settings: dict,
    remote_dir: str,
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
    if local_dir is None:
        ssh_manager.get_file(remote_dir, os.getcwd())
    else:
        ssh_manager.get_file(remote_dir, local_dir)
    return


def delete_dir_ssh(ssh_settings: dict):
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
