import os
import time
import subprocess as sp
from typing import Union
from ...local import submit_subprocess, random_id
from .helpers_launch_slurm import slurm_generate_startup_file


def submit_slurm(
    filename: str,
    cmd_line_arguments: str,
    job_arguments: dict,
    user_name: str,
    debug_mode: bool,
    clean_up: bool = True,
) -> str:
    """Create a qsub job & submit it based on provided file to execute."""
    # Create base string of job id
    base = "submit_{0}".format(random_id())

    # Write the desired python/bash execution to slurm job submission file
    f_name, f_extension = os.path.splitext(filename)
    if f_extension == ".py":
        script = f"python {filename} {cmd_line_arguments}"
    elif f_extension == ".sh":
        script = f"bash {filename} {cmd_line_arguments}"
    else:
        raise ValueError(
            f"Script with {f_extension} cannot be handled"
            " by mle-toolbox. Only base .py, .sh experiments"
            " are so far implemented. Please open an issue."
        )
    job_arguments["script"] = script
    slurm_job_template = slurm_generate_startup_file(job_arguments)

    # Create combined string if multiple jobs provided as list
    if type(job_arguments["partition"]) == list:
        job_arguments["partition"] = ",".join(job_arguments["partition"])

    # Add path for virtualenv activation
    if "use_venv_venv" in job_arguments:
        if job_arguments["use_venv_venv"]:
            job_arguments["work_on_dir"] = os.environ["WORKON_HOME"]

    # Reformatting of time for Slurm SBASH - d-hh:mm but in is dd:hh:mm
    if "time_per_job" in job_arguments:
        days, hours, minutes = job_arguments["time_per_job"].split(":")
        slurm_time = days[1] + "-" + hours + ":" + minutes
        job_arguments["time_per_job"] = slurm_time

    # Add job name if not given in arguments
    if "job_name" not in job_arguments:
        job_arguments["job_name"] = "job"

    # Write slurm scheduling script to bash file
    open(base + ".sh", "w").write(slurm_job_template.format(**job_arguments))

    # Submit the job via subprocess call
    command = "sbatch < " + base + ".sh"
    while True:
        proc = submit_subprocess(command, debug_mode)

        # Wait until system has processed submission
        while True:
            poll = proc.poll()
            if poll is None:
                continue
            else:
                break

        # Get output & error messages (if there is an error)
        out, err = proc.communicate()
        if proc.returncode != 0:
            print(out, err)
            job_id = -1
        else:
            job_id = int(out.decode("utf-8").split()[-1])
            break
    # Wait until the job is listed under the qstat scheduled jobs
    while True:
        job_running = monitor_slurm(job_id, user_name)
        if job_running:
            break
    # Finally delete all the unneccessary submission file
    if clean_up:
        os.remove(base + ".sh")

    return job_id


def monitor_slurm(job_id: Union[list, int], user_name: str) -> bool:
    """Monitor the status of a job based on its id."""
    while True:
        try:
            out = sp.check_output(["squeue", "-u", user_name])
            break
        except sp.CalledProcessError as e:
            stderr = e.stderr
            return_code = e.returncode
            print(stderr, return_code)
            time.sleep(0.5)

    job_info = out.split(b"\n")[1:]
    running_job_ids = [
        int(job_info[i].decode("utf-8").split()[0]) for i in range(len(job_info) - 1)
    ]
    if type(job_id) == int:
        job_id = [job_id]
    S1 = set(job_id)
    S2 = set(running_job_ids)
    job_status = len(S1.intersection(S2)) > 0
    return job_status
