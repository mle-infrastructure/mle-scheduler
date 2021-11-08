import os
import shutil
import datetime
from mle_scheduler import MLEJob, MLEQueue

# Only test this locally! For remote - have to run `run_remote.py` manually


def test_job():
    # Launch a python train_mnist.py -config base_config.json job
    job = MLEJob(
        resource_to_run="local",
        job_filename="examples/train.py",
        config_filename="examples/base_config_1.yaml",
        experiment_dir="logs_single",
        job_arguments={},
    )

    job.run()

    # Check existence of expected files
    date = datetime.datetime.today().strftime("%Y-%m-%d")[2:]
    assert os.path.exists(
        os.path.join("logs_single", date + "_base_config_1", "logs/log_seed_1.hdf5")
    )
    shutil.rmtree("logs_single")
    return


def test_queue():
    # Launch a queue of 4 jobs (2 configs x 2 seeds)
    queue = MLEQueue(
        resource_to_run="local",
        job_filename="examples/train.py",
        config_filenames=["examples/base_config_1.yaml", "examples/base_config_2.yaml"],
        num_seeds=2,
        random_seeds=[0, 1],
        experiment_dir="logs_queue",
        job_arguments={},
    )
    queue.run()

    # Check existence of expected files
    date = datetime.datetime.today().strftime("%Y-%m-%d")[2:]
    assert os.path.exists(os.path.join("logs_queue", date + "_base_config_1"))
    assert os.path.exists(os.path.join("logs_queue", date + "_base_config_2"))
    shutil.rmtree("logs_queue")
    return
