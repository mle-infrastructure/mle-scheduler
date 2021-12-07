# Lightweight Cluster/Cloud VM Job Management 🚀
[![Pyversions](https://img.shields.io/pypi/pyversions/mle-scheduler.svg?style=flat-square)](https://pypi.python.org/pypi/mle-scheduler)
[![PyPI version](https://badge.fury.io/py/mle-scheduler.svg)](https://badge.fury.io/py/mle-scheduler)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![codecov](https://codecov.io/gh/mle-infrastructure/mle-scheduler/branch/main/graph/badge.svg)](https://codecov.io/gh/mle-infrastructure/mle-scheduler)
<a href="https://github.com/mle-infrastructure/mle-scheduler/blob/main/docs/logo_transparent.png?raw=true"><img src="https://github.com/mle-infrastructure/mle-scheduler/blob/main/docs/logo_transparent.png?raw=true" width="200" align="right" /></a>

Are you looking for a tool to manage your training runs locally, on [Slurm](https://slurm.schedmd.com/)/[Open Grid Engine](http://gridscheduler.sourceforge.net/documentation.html) clusters, SSH servers or [Google Cloud Platform VMs](https://cloud.google.com/gcp/)? `mle-scheduler` provides a lightweight API to launch and monitor job queues. It smoothly orchestrates simultaneous runs for different configurations and/or random seeds. It is meant to reduce boilerplate and to make job resource specification intuitive. It comes with two core pillars:

- **`MLEJob`**: Launches and monitors a single job on a resource (Slurm, Open Grid Engine, GCP, SSH, etc.).
- **`MLEQueue`**: Launches and monitors a queue of jobs with different training configurations and/or seeds.

For a quickstart check out the [notebook blog](https://github.com/mle-infrastructure/mle-hyperopt/blob/main/examples/getting_started.ipynb) or the example scripts 📖

| [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/mle-infrastructure/mle-scheduler/blob/main/examples/getting_started.ipynb)| [Local](https://github.com/mle-infrastructure/mle-scheduler/blob/main/examples/run_local.py) | [Slurm](https://github.com/mle-infrastructure/mle-scheduler/blob/main/examples/run_cluster.py) | [Grid Engine](https://github.com/mle-infrastructure/mle-scheduler/blob/main/examples/run_cluster.py) | [SSH](https://github.com/mle-infrastructure/mle-scheduler/blob/main/examples/run_ssh.py) | [GCP](https://github.com/mle-infrastructure/mle-scheduler/blob/main/examples/run_gcp.py) |
|:----: |:----:|:----: | :----: | :----:| :----:|

<a href="https://github.com/mle-infrastructure/mle-scheduler/blob/main/docs/mle_scheduler_structure.png?raw=true"><img src="https://github.com/mle-infrastructure/mle-scheduler/blob/main/docs/mle_scheduler_structure.png?raw=true" width="850" align="center" /></a>

## Installation ⏳

```
pip install mle-scheduler
```

## Managing a Single Job with `MLEJob` Locally 🚀

```python
from mle_scheduler import MLEJob

# python train.py -config base_config_1.yaml -exp_dir logs_single -seed_id 1
job = MLEJob(
    resource_to_run="local",
    job_filename="train.py",
    config_filename="base_config_1.yaml",
    experiment_dir="logs_single",
    seed_id=1
)

_ = job.run()
```

## Managing a Queue of Jobs with `MLEQueue` Locally 🚀...🚀

```python
from mle_scheduler import MLEQueue

# python train.py -config base_config_1.yaml -seed 0 -exp_dir logs_queue/<date>_base_config_1
# python train.py -config base_config_1.yaml -seed 1 -exp_dir logs_queue/<date>_base_config_1
# python train.py -config base_config_2.yaml -seed 0 -exp_dir logs_queue/<date>_base_config_2
# python train.py -config base_config_2.yaml -seed 1 -exp_dir logs_queue/<date>_base_config_2
queue = MLEQueue(
    resource_to_run="local",
    job_filename="train.py",
    config_filenames=["base_config_1.yaml",
                      "base_config_2.yaml"],
    random_seeds=[0, 1],
    experiment_dir="logs_queue"
)

queue.run()
```

## Launching Slurm Cluster-Based Jobs 🐒

```python
# Each job requests 5 CPU cores & 1 V100S GPU & loads CUDA 10.0
job_args = {
    "partition": "<SLURM_PARTITION>",  # Partition to schedule jobs on
    "env_name": "mle-toolbox",  # Env to activate at job start-up
    "use_conda_venv": True,  # Whether to use anaconda venv
    "num_logical_cores": 5,  # Number of requested CPU cores per job
    "num_gpus": 1,  # Number of requested GPUs per job
    "gpu_type": "V100S",  # GPU model requested for each job
    "modules_to_load": "nvidia/cuda/10.0"  # Modules to load at start-up
}

queue = MLEQueue(
    resource_to_run="slurm-cluster",
    job_filename="train.py",
    job_arguments=job_args,
    config_filenames=["base_config_1.yaml",
                      "base_config_2.yaml"],
    experiment_dir="logs_slurm",
    random_seeds=[0, 1]
)
queue.run()
```

## Launching GridEngine Cluster-Based Jobs 🐘

```python
# Each job requests 5 CPU cores & 1 V100S GPU w. CUDA 10.0 loaded
job_args = {
    "queue": "<GRID_ENGINE_QUEUE>",  # Queue to schedule jobs on
    "env_name": "mle-toolbox",  # Env to activate at job start-up
    "use_conda_venv": True,  # Whether to use anaconda venv
    "num_logical_cores": 5,  # Number of requested CPU cores per job
    "num_gpus": 1,  # Number of requested GPUs per job
    "gpu_type": "V100S",  # GPU model requested for each job
    "gpu_prefix": "cuda"  #$ -l {gpu_prefix}="{num_gpus}"
}

queue = MLEQueue(
    resource_to_run="slurm-cluster",
    job_filename="train.py",
    job_arguments=job_args,
    config_filenames=["base_config_1.yaml",
                      "base_config_2.yaml"],
    experiment_dir="logs_grid_engine",
    random_seeds=[0, 1]
)
queue.run()
```

## Launching SSH Server-Based Jobs 🦊

```python
ssh_settings = {
    "user_name": "<SSH_USER_NAME>",  # SSH server user name
    "pkey_path": "<PKEY_PATH>",  # Private key path (e.g. ~/.ssh/id_rsa)
    "main_server": "<SSH_SERVER>",  # SSH Server address
    "jump_server": '',  # Jump host address
    "ssh_port": 22,  # SSH port
    "remote_dir": "mle-code-dir",  # Dir to sync code to on server
    "start_up_copy_dir": True,  # Whether to copy code to server
    "clean_up_remote_dir": True  # Whether to delete remote_dir on exit
}

job_args = {
    "env_name": "mle-toolbox",  # Env to activate at job start-up
    "use_conda_venv": True  # Whether to use anaconda venv
}

queue = MLEQueue(
    resource_to_run="ssh-node",
    job_filename="train.py",
    config_filenames=["base_config_1.yaml",
                      "base_config_2.yaml"],
    random_seeds=[0, 1],
    experiment_dir="logs_ssh_queue",
    job_arguments=job_args,
    ssh_settings=ssh_settings)

queue.run()
```

## Launching GCP VM-Based Jobs 🦄

```python
cloud_settings = {
    "project_name": "<GCP_PROJECT_NAME>",  # Name of your GCP project
    "bucket_name": "<GCS_BUCKET_NAME>", # Name of your GCS bucket
    "remote_dir": "<GCS_CODE_DIR_NAME>",  # Name of code dir in bucket
    "start_up_copy_dir": True,  # Whether to copy code to bucket
    "clean_up_remote_dir": True  # Whether to delete remote_dir on exit
}

job_args = {
    "num_gpus": 0,  # Number of requested GPUs per job
    "gpu_type": None,  # GPU requested e.g. "nvidia-tesla-v100"
    "num_logical_cores": 1,  # Number of requested CPU cores per job
}

queue = MLEQueue(
    resource_to_run="gcp-cloud",
    job_filename="train.py",
    config_filenames=["base_config_1.yaml",
                      "base_config_2.yaml"],
    random_seeds=[0, 1],
    experiment_dir="logs_gcp_queue",
    job_arguments=job_args,
    cloud_settings=cloud_settings,
)
queue.run()
```


## Development & Milestones for Next Release

You can run the test suite via `python -m pytest -vv tests/`. If you find a bug or are missing your favourite feature, feel free to contact me [@RobertTLange](https://twitter.com/RobertTLange) or create an issue :hugs:. In future releases I plan on implementing the following:

- [ ] Add configuration details to examples (time of job, memory, etc.)
- [ ] Clean up TPU GCP VM & JAX dependencies case
- [ ] Add local launching of cluster jobs via SSH to headnode
- [ ] Add Docker/Singularity container setup support
- [ ] Add Azure support
- [ ] Add AWS support
