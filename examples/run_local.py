import logging
from mle_scheduler import MLEJob, MLEQueue


def main():
    # Run a single job
    job = MLEJob(
        resource_to_run="local",
        job_filename="train.py",
        config_filename="base_config_1.yaml",
        experiment_dir="logs_ssh_single",
        logger_level=logging.INFO,
    )

    job.run()

    # Run a queue of 4 jobs
    queue = MLEQueue(
        resource_to_run="local",
        job_filename="train.py",
        config_filenames=["base_config_1.yaml", "base_config_2.yaml"],
        random_seeds=[0, 1],
        experiment_dir="logs_ssh_queue",
        logger_level=logging.INFO,
    )

    queue.run()


if __name__ == "__main__":
    main()
