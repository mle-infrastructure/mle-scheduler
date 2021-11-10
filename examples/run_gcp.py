from mle_scheduler import MLEJob, MLEQueue


def main(resource_to_run: str):
    cloud_settings = {
        "user_name": "RobTLange",
        "pkey_path": "~.ssh/id_rsa",
        "main_server": "cluster.ml.tu-berlin.de",
        "jump_server": "",
        "ssh_port": 22,
        "remote_dir": "mle-code-dir",
    }

    job_args = {
        "env_name": "mle-toolbox",
        "use_conda_venv": True,
        "num_logical_cores": 1,
        "job_name": "test",
        "err_file": "job",
        "log_file": "job",
    }

    # Launch a python train_mnist.py -config base_config.json job
    job = MLEJob(
        resource_to_run=resource_to_run,
        job_filename="train.py",
        config_filename="base_config_1.yaml",
        experiment_dir="logs_single",
        job_arguments=job_args,
        cloud_settings=cloud_settings,
    )

    job.run()

    queue = MLEQueue(
        resource_to_run=resource_to_run,
        job_filename="train.py",
        config_filenames=["base_config_1.yaml", "base_config_2.yaml"],
        random_seeds=[0, 1],
        experiment_dir="logs_queue",
        job_arguments=job_args,
        cloud_settings=cloud_settings,
    )
    queue.run()
