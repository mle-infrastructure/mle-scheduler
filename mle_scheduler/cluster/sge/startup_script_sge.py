# Useful string lego building blocks for SGE startup file formatting

# Base qsub template
sge_base_job_config = """
#####################################
#!/bin/sh
#$ -binding linear:{num_logical_cores}
#$ -q {queue}
#$ -cwd
#$ -V
#$ -N {job_name}
#$ -e {err_file}.err
#$ -o {log_file}.txt
"""


# Base template for executing .py script
sge_job_exec = """
#####################################
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
"""
