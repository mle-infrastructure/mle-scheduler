# Useful string lego building blocks for Slurm startup file formatting

# Base sbatch template
slurm_base_job_config = """#!/bin/bash
#SBATCH --job-name={job_name}                   # job name (not id)
#SBATCH --output=log.txt                        # output file
#SBATCH --error=err.err                         # error file
#SBATCH --partition={partition}                 # partition to submit to
#SBATCH --cpus-per-task={num_logical_cores}     # number of cpus
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
