from mle_scheduler.cluster.slurm.helpers_launch_slurm import slurm_generate_startup_file

job_arguments = {
    "num_logical_cores": 5,
    "partition": "standard",
    "job_name": "test_job",
    "err_file": "job",
    "log_file": "job",
    "num_gpus": 1,
    "gpu_type": "RTX2080",
    "env_name": "test_env",
    "script": "python run.py",
    "memory_per_cpu": 2000,
    "time_per_job": "10:05:02",
}

job_script = """#!/bin/bash
#SBATCH --job-name=test_job                   # job name (not id)
#SBATCH --output=job.txt                 # output file
#SBATCH --error=job.err                  # error file
#SBATCH --partition=standard                 # partition to submit to
#SBATCH --cpus-per-task=5     # number of cpus
#SBATCH --gres=gpu:RTX2080:1
#SBATCH --mem-per-cpu=2000
#SBATCH --time=10:05:02

module load nvidia/cuda/10.0
source ~/miniconda3/etc/profile.d/conda.sh
echo "------------------------------------------------------------------------"
. ~/.bashrc && conda activate test_env
echo "Successfully activated virtual environment - Ready to start job"
echo "------------------------------------------------------------------------"
echo "Job started on" `date`
echo "------------------------------------------------------------------------"
python run.py
echo "------------------------------------------------------------------------"
echo "Job ended on" `date`
echo "------------------------------------------------------------------------"
conda deactivate
"""


def test_job_slurm():
    startup_script = slurm_generate_startup_file(job_arguments).format(**job_arguments)
    assert job_script == startup_script
    return
