## [v0.0.5] - [01/05/2021]

### Added

- Adds `MLEQueue` option to delete config after job has finished
- Adds `debug_mode` option to store `stdout` & `stderr` to files
- Adds merging/loading of generated logs in `MLEQueue` w. `automerge_configs` option

## [v0.0.4] - [12/07/2021]

### Added

- Adds automerging of generated `mle-logging` logs in queue
- Track config base strings for auto-merging of mle-logs & add `merge_configs`
- Allow scheduling on multiple partitions via `-p <part1>,<part2>` & queues via `-q <queue1>,<queue2>`


## [v0.0.1]-[v0.0.3] - [11/12/2021]

### Added

First release 🤗 implementing core API of `MLEJob` and `MLEQueue`

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

### Fixed

- Fixed relative imports for PyPI installation.
