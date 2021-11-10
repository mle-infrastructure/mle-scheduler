from mle_scheduler import MLEJob, MLEQueue
from mle_scheduler.cloud.gcp import send_dir_gcp, copy_dir_gcp, delete_dir_gcp


def main(resource_to_run: str):
    cloud_settings = {
        "project_name": "mle-toolbox",
        "bucket_name": "mle-protocol",
        "remote_dir": "mle-code-dir",
    }

    # Send config file to remote machine - independent of code base!
    send_dir_gcp(cloud_settings)

    job_args = {
        "use_tpus": 0,
        "num_gpus": 0,
        "gpu_type": "nvidia-tesla-v100",
        "num_logical_cores": 1,
        "job_name": "test",
    }

    job = MLEJob(
        resource_to_run="gcp-cloud",
        job_filename="train.py",
        config_filename="base_config_1.yaml",
        experiment_dir="logs_gcp_single",
        job_arguments=job_args,
        cloud_settings=cloud_settings,
        logger_level=logging.INFO,
    )

    job.run()

    # Copy over the results from the SSH server
    copy_dir_gcp(cloud_settings, remote_dir="mle-code-dir/logs_gcp_single")

    # Delete the code directory on the SSH server
    delete_dir_gcp(cloud_settings)

    cloud_settings["start_up_copy_dir"] = True
    cloud_settings["clean_up_remote_dir"] = True

    queue = MLEQueue(
        resource_to_run="gcp-cloud",
        job_filename="train.py",
        config_filenames=["base_config_1.yaml", "base_config_2.yaml"],
        random_seeds=[0, 1],
        experiment_dir="logs_gcp_queue",
        job_arguments=job_args,
        cloud_settings=cloud_settings,
    )
    queue.run()
