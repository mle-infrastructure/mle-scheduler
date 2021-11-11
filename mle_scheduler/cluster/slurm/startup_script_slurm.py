# Useful string lego building blocks for Slurm startup file formatting

# Base sbatch template
slurm_base_job_config = """#!/bin/bash
#SBATCH --job-name={job_name}
#SBATCH --output=log.txt
#SBATCH --error=err.err
#SBATCH --partition={partition}
#SBATCH --cpus-per-task={num_logical_cores}
"""


slurm_conda_activate = """
echo "------------------------------------------------------------------------"
source ~/miniconda3/etc/profile.d/conda.sh
echo "------------------------------------------------------------------------"
. ~/.bashrc && conda activate {env_name}
echo "Successfully activated virtual environment - Ready to start job"
"""

slurm_venv_activate = """
echo "------------------------------------------------------------------------"
. ~/.bashrc && source {work_on_dir}/{env_name}/bin/activate
echo "Successfully activated virtual environment - Ready to start job"
"""

# Base template for executing .py script
slurm_job_exec = """
echo "------------------------------------------------------------------------"
echo "Job started on" `date`
echo "------------------------------------------------------------------------"
{script}
echo "------------------------------------------------------------------------"
echo "Job ended on" `date`
echo "------------------------------------------------------------------------"
conda deactivate
"""
