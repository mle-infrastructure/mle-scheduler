# Lightweight Cluster/Cloud VM Job Scheduling 🚂
[![Pyversions](https://img.shields.io/pypi/pyversions/mle-launcher.svg?style=flat-square)](https://pypi.python.org/pypi/mle-launcher)
[![PyPI version](https://badge.fury.io/py/mle-monitor.svg)](https://badge.fury.io/py/mle-launcher)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/RobertTLange/mle-launcher/blob/main/examples/getting_started.ipynb)
<a href="https://github.com/RobertTLange/mle-launcher/blob/main/docs/logo_transparent.png?raw=true"><img src="https://github.com/RobertTLange/mle-launcher/blob/main/docs/logo_transparent.png?raw=true" width="200" align="right" /></a>

`mle-launcher` provides two core functionalities for scheduling/monitoring python/shell-based jobs locally, on SSH servers, Slurm & GridEngine clusters and GCP cloud VMs:

## Single Job Management with `MLEJob` 🚀

```python
from mle_launcher import MLEJob

# Launch a python train_mnist.py -config base_config.json job
job = MLEJob(resource_to_run="slurm",
             job_filename="train.py",
             config_filename="base_config.json")
```

## Job Queue Management with `MLEQueue` 🚀🚀🚀

```python
from mle_launcher import MLEQueue

# Launch a queue of 4 jobs (2 configs x 2 seeds)
# python train_mnist.py -config base_config_1.json -seed 0
# python train_mnist.py -config base_config_1.json -seed 1
# python train_mnist.py -config base_config_2.json -seed 0
# python train_mnist.py -config base_config_2.json -seed 1
queue = MLEQueue(resource_to_run="slurm",
                 job_filename="train.py",
                 config_filenames=["base_config_1.json",
                                   "base_config_2.json"],
                 random_seeds=[0, 1])
```

For a quickstart check out the [notebook blog](https://github.com/mle-infrastructure/mle-hyperopt/blob/main/examples/getting_started.ipynb) 📖.

![](https://github.com/mle-infrastructure/mle-launcher/blob/main/docs/mle_lanucher_structure.png?raw=true)

## Installation ⏳

A PyPI installation is available via:

```
pip install mle-launcher
```

Alternatively, you can clone this repository and afterwards 'manually' install it:

```
git clone https://github.com/mle-infrastructure/mle-launcher.git
cd mle-launcher
pip install -e .
```

## Development & Milestones for Next Release

You can run the test suite via `python -m pytest -vv tests/`. If you find a bug or are missing your favourite feature, feel free to contact me [@RobertTLange](https://twitter.com/RobertTLange) or create an issue :hugs:.
