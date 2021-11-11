# Lightweight Cluster/Cloud VM Job Scheduling 🚂
[![Pyversions](https://img.shields.io/pypi/pyversions/mle-scheduler.svg?style=flat-square)](https://pypi.python.org/pypi/mle-scheduler)
[![PyPI version](https://badge.fury.io/py/mle-monitor.svg)](https://badge.fury.io/py/mle-scheduler)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
<a href="https://github.com/mle-infrastructure/mle-scheduler/blob/main/docs/logo_transparent.png?raw=true"><img src="https://github.com/mle-infrastructure/mle-scheduler/blob/main/docs/logo_transparent.png?raw=true" width="200" align="right" /></a>

Are you looking for a tool to manage your training runs locally, on Slurm/Grid engine clusters, SSH servers or GCP VMs? `mle-scheduler` provides a lightweight API to launch and monitor job queues. It smoothly orchestrates simultaneous runs for different configs/seeds. It is meant to reduce boilerplate and to make job resource specification intuitive.

<a href="https://github.com/mle-infrastructure/mle-scheduler/blob/main/docs/mle_scheduler_structure.png?raw=true"><img src="https://github.com/mle-infrastructure/mle-scheduler/blob/main/docs/mle_scheduler_structure.png?raw=true" width="850" align="center" /></a>

For a quickstart check out the [notebook blog](https://github.com/mle-infrastructure/mle-hyperopt/blob/main/examples/getting_started.ipynb) or the example scripts 📖

| [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/mle-infrastructure/mle-scheduler/blob/main/examples/getting_started.ipynb)| [Local](https://github.com/mle-infrastructure/mle-scheduler/blob/main/examples/run_local.py) | [Slurm](https://github.com/mle-infrastructure/mle-scheduler/blob/main/examples/run_cluster.py) | [Grid Engine](https://github.com/mle-infrastructure/mle-scheduler/blob/main/examples/run_cluster.py) | [SSH](https://github.com/mle-infrastructure/mle-scheduler/blob/main/examples/run_ssh.py) | [GCP](https://github.com/mle-infrastructure/mle-scheduler/blob/main/examples/run_gcp.py) |
|:----: |:----:|:----: | :----: | :----:| :----:|

## Installation ⏳

```
pip install mle-scheduler
```

## Single Job Management with `MLEJob` 🚀

```python
from mle_scheduler import MLEJob

# python train.py -config base_config_1.yaml -exp_dir logs_single -seed_id 1
job = MLEJob(resource_to_run="local",
             job_filename="train.py",
             config_filename="base_config_1.yaml",
             experiment_dir="logs_single",
             seed_id=1)

_ = job.run()
```

## Job Queue Management with `MLEQueue` 🚀...🚀

```python
from mle_scheduler import MLEQueue

# python train.py -config base_config_1.yaml -seed 0 -exp_dir logs_queue/<date>_base_config_1
# python train.py -config base_config_1.yaml -seed 1 -exp_dir logs_queue/<date>_base_config_1
# python train.py -config base_config_2.yaml -seed 0 -exp_dir logs_queue/<date>_base_config_2
# python train.py -config base_config_2.yaml -seed 1 -exp_dir logs_queue/<date>_base_config_2
queue = MLEQueue(resource_to_run="local",
                 job_filename="train.py",
                 config_filenames=["base_config_1.yaml",
                                   "base_config_2.yaml"],
                 random_seeds=[0, 1],
                 experiment_dir="logs_queue")

queue.run()
```

## Launching Slurm Cluster-Based Jobs

## Launching GridEngine Cluster-Based Jobs

## Launching SSH Server-Based Jobs

## Launching GCP VM-Based Jobs


## Development & Milestones for Next Release

You can run the test suite via `python -m pytest -vv tests/`. If you find a bug or are missing your favourite feature, feel free to contact me [@RobertTLange](https://twitter.com/RobertTLange) or create an issue :hugs:. In future releases I plan on implementing the following:

- [ ] Clean up TPU GCP VM case
- [ ] Add local launching of cluster jobs via SSH to headnode
- [ ] Add Docker/Singularity container setup support
- [ ] Add Azure support
- [ ] Add AWS support
