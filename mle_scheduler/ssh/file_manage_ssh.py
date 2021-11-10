import os
from typing import Union
from .ssh_manager import SSH_Manager


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
