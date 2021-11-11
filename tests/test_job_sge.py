from mle_scheduler.cluster.sge.helpers_launch_sge import sge_generate_startup_file

job_arguments = {
    "num_logical_cores": 5,
    "queue": "test_queue",
    "job_name": "test_job",
    "err_file": "job",
    "log_file": "job",
    "num_gpus": 1,
    "gpu_type": "RTX2080",
    "env_name": "test_env",
    "script": "python run.py",
    "exclude_nodes": ["temp.tu-berlin.de"],
    "memory_per_job": 2000,
    "time_per_job": "10:05:02",
}

job_script = """
#####################################
#!/bin/sh
#$ -binding linear:5
#$ -q test_queue
#$ -cwd
#$ -V
#$ -N test_job
#$ -e job.err
#$ -o job.txt
#$ -l cuda="1",gputype="RTX2080"
#$ -l hostname=!temp.tu-berlin.de
#$ -l h_vmem=2000M
#$ -l mem_free=2000M
#$ -l h_rt=10:05:02
#$ -terse

#####################################
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
"""


def test_job_grid_engine():
    startup_script = sge_generate_startup_file(job_arguments).format(**job_arguments)
    assert job_script == startup_script
    return
