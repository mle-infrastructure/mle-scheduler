import logging
from mle_scheduler import MLEJob, MLEQueue


def main(resource_to_run: str):
    job_args = {
        "env_name": "mle-toolbox",
        "use_conda_virtual_env": True,
        "num_logical_cores": 1,
        "job_name": "test",
        "err_file": "job",
        "log_file": "job",
    }
    if resource_to_run == "sge-cluster":
        job_args["queue"] = "cognition-all.q"
    elif resource_to_run == "slurm-cluster":
        job_args["partition"] = "standard"

    # Launch a python train_mnist.py -config base_config.json job
    job = MLEJob(
        resource_to_run=resource_to_run,
        job_filename="train.py",
        config_filename="base_config_1.yaml",
        experiment_dir="logs_single",
        job_arguments=job_args,
        logger_level=logging.INFO,
    )

    job.run()

    # Launch a queue of 4 jobs (2 configs x 2 seeds)
    # python train.py -config base_config_1.yaml -seed 0 -exp_dir logs_queue/<date>_base_config_1
    # python train.py -config base_config_1.yaml -seed 1 -exp_dir logs_queue/<date>_base_config_1
    # python train.py -config base_config_2.yaml -seed 0 -exp_dir logs_queue/<date>_base_config_2
    # python train.py -config base_config_2.yaml -seed 1 -exp_dir logs_queue/<date>_base_config_2
    queue = MLEQueue(
        resource_to_run=resource_to_run,
        job_filename="train.py",
        config_filenames=["base_config_1.yaml", "base_config_2.yaml"],
        random_seeds=[0, 1],
        experiment_dir="logs_queue",
        job_arguments=job_args,
        logger_level=logging.INFO,
    )
    queue.run()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Description of your program")
    parser.add_argument("-resource", "--resource_to_run")
    args = vars(parser.parse_args())
    main(args["resource_to_run"])
