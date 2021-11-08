# Lightweight Cluster/Cloud VM Job Scheduling 🚂
[![Pyversions](https://img.shields.io/pypi/pyversions/mle-scheduler.svg?style=flat-square)](https://pypi.python.org/pypi/mle-scheduler)
[![PyPI version](https://badge.fury.io/py/mle-monitor.svg)](https://badge.fury.io/py/mle-scheduler)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/mle-infrastructure/mle-scheduler/blob/main/examples/getting_started.ipynb)
<a href="https://github.com/mle-infrastructure/mle-scheduler/blob/main/docs/logo_transparent.png?raw=true"><img src="https://github.com/mle-infrastructure/mle-scheduler/blob/main/docs/logo_transparent.png?raw=true" width="200" align="right" /></a>

`mle-scheduler` provides two core functionalities for scheduling/monitoring python/shell-based jobs locally, on SSH servers, Slurm & GridEngine clusters and GCP cloud VMs:

## Single Job Management with `MLEJob` 🚀

```python
from mle_scheduler import MLEJob

# Launch a single job via
# python train_mnist.py -config base_config_1.yaml -exp_dir logs_single/<date>_base_config_1
job = MLEJob(resource_to_run="local",
             job_filename="train.py",
             config_filename="base_config_1.yaml",
             experiment_dir="logs_single")

job.run()
```

## Job Queue Management with `MLEQueue` 🚀🚀🚀

```python
from mle_scheduler import MLEQueue

# Launch a queue of 4 jobs (2 configs x 2 seeds)
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

## Running Jobs on Remote Resources

Supply `job_arguments` ...


For a quickstart check out the [notebook blog](https://github.com/mle-infrastructure/mle-hyperopt/blob/main/examples/getting_started.ipynb) 📖.

![](https://github.com/mle-infrastructure/mle-scheduler/blob/main/docs/mle_scheduler_structure.png?raw=true)

## Installation ⏳

A PyPI installation is available via:

```
pip install mle-scheduler
```

Alternatively, you can clone this repository and afterwards 'manually' install it:

```
git clone https://github.com/mle-infrastructure/mle-scheduler.git
cd mle-scheduler
pip install -e .
```

## Development & Milestones for Next Release

You can run the test suite via `python -m pytest -vv tests/`. If you find a bug or are missing your favourite feature, feel free to contact me [@RobertTLange](https://twitter.com/RobertTLange) or create an issue :hugs:.
