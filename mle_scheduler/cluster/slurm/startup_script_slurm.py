# Useful string lego building blocks for Slurm startup file formatting

# Base sbatch template
slurm_base_job_config = """#!/bin/bash
#SBATCH --job-name={job_name}                   # job name (not id)
#SBATCH --output={log_file}.txt                 # output file
#SBATCH --error={err_file}.err                  # error file
#SBATCH --partition={partition}                 # partition to submit to
#SBATCH --cpus-per-task={num_logical_cores}     # number of cpus
"""


# Base template for executing .py script
slurm_job_exec = """
module load nvidia/cuda/10.0
source ~/miniconda3/etc/profile.d/conda.sh
echo "------------------------------------------------------------------------"
. ~/.bashrc && conda activate {env_name}
echo "Successfully activated virtual environment - Ready to start job"
echo "------------------------------------------------------------------------"
echo "Job started on" `date`
echo "------------------------------------------------------------------------"
{script}
echo "------------------------------------------------------------------------"
echo "Job ended on" `date`
echo "------------------------------------------------------------------------"
conda deactivate
"""
