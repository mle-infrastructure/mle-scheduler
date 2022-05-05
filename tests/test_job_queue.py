import os
import shutil
from mle_scheduler import MLEJob, MLEQueue

# Only test this locally! For remote - have to run example `run_XXX.py` manually


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
    assert os.path.exists(
        os.path.join("logs_single", "base_config_1", "logs/log_seed_1.hdf5")
    )
    shutil.rmtree("logs_single")
    return


def test_queue():
    # Launch a queue of 4 jobs (2 configs x 2 seeds)
    queue = MLEQueue(
        resource_to_run="local",
        job_filename="examples/train.py",
        config_filenames=[
            "examples/base_config_1.yaml",
            "examples/base_config_2.yaml",
        ],
        num_seeds=2,
        random_seeds=[0, 1],
        experiment_dir="logs_queue",
        job_arguments={},
    )
    queue.run()

    # Check existence of expected files
    assert os.path.exists(
        os.path.join("logs_queue", "base_config_1/logs/log_seed_0.hdf5")
    )
    assert os.path.exists(
        os.path.join("logs_queue", "base_config_1/logs/log_seed_1.hdf5")
    )

    assert os.path.exists(
        os.path.join("logs_queue", "base_config_2/logs/log_seed_0.hdf5")
    )
    assert os.path.exists(
        os.path.join("logs_queue", "base_config_2/logs/log_seed_1.hdf5")
    )

    shutil.rmtree("logs_queue")
    return


def test_automerge_seeds():
    # Launch a queue of 4 jobs (2 configs x 2 seeds)
    queue = MLEQueue(
        resource_to_run="local",
        job_filename="examples/train.py",
        config_filenames=[
            "examples/base_config_1.yaml",
            "examples/base_config_2.yaml",
        ],
        num_seeds=2,
        random_seeds=[0, 1],
        experiment_dir="logs_merge",
        job_arguments={},
        automerge_seeds=True,
    )
    queue.run()

    # Check existence of expected files
    assert os.path.exists(
        os.path.join("logs_merge", "base_config_1/logs/log.hdf5")
    )
    assert os.path.exists(
        os.path.join("logs_merge", "base_config_2/logs/log.hdf5")
    )
    shutil.rmtree("logs_merge")
    return


def test_automerge_configs():
    # Launch a queue of 4 jobs (2 configs x 2 seeds)
    queue = MLEQueue(
        resource_to_run="local",
        job_filename="examples/train.py",
        config_filenames=[
            "examples/base_config_1.yaml",
            "examples/base_config_2.yaml",
        ],
        num_seeds=2,
        random_seeds=[0, 1],
        experiment_dir="logs_merge",
        job_arguments={},
        automerge_configs=True,
    )
    queue.run()

    # Check existence of expected files
    assert os.path.exists(os.path.join("logs_merge", "meta_log.hdf5"))
    assert os.path.exists(
        os.path.join("logs_merge", "base_config_1/logs/log.hdf5")
    )
    assert os.path.exists(
        os.path.join("logs_merge", "base_config_2/logs/log.hdf5")
    )
    shutil.rmtree("logs_merge")
    return
