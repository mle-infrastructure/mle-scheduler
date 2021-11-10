import logging
from mle_scheduler import MLEJob, MLEQueue
from mle_scheduler.ssh import send_dir_ssh, copy_dir_ssh, delete_dir_ssh


def main(resource_to_run: str):
    job_args = {"env_name": "mle-toolbox", "use_conda_venv": True}

    ssh_settings = {
        "user_name": "RobTLange",
        "pkey_path": "~.ssh/id_rsa",
        "main_server": "cluster.ml.tu-berlin.de",
        "jump_server": "",
        "ssh_port": 22,
        "remote_dir": "mle-code-dir",
    }

    # scp the current working directory to a mle-code-dir remote
    send_dir_ssh(ssh_settings)

    job = MLEJob(
        resource_to_run="ssh-node",
        job_filename="train.py",
        config_filename="base_config_1.yaml",
        experiment_dir="logs_ssh_single",
        job_arguments=job_args,
        ssh_settings=ssh_settings,
        logger_level=logging.INFO,
    )

    job.run()

    # Copy over the results from the SSH server
    copy_dir_ssh(ssh_settings, remote_dir="mle-code-dir/logs_ssh_single")

    # Delete the code directory on the SSH server
    delete_dir_ssh(ssh_settings)

    ssh_settings["start_up_copy_dir"] = True
    ssh_settings["clean_up_remote_dir"] = True

    queue = MLEQueue(
        resource_to_run="ssh-node",
        job_filename="train.py",
        config_filenames=["base_config_1.yaml", "base_config_2.yaml"],
        random_seeds=[0, 1],
        experiment_dir="logs_ssh_queue",
        job_arguments=job_args,
        ssh_settings=ssh_settings,
    )

    queue.run()
