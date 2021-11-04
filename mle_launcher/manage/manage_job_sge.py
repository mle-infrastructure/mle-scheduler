import os
import time
import subprocess as sp
from typing import Union
from .manage_job_local import submit_subprocess, random_id
from ..cluster.sge.helpers_launch_sge import sge_generate_startup_file
from mle_toolbox import mle_config


def sge_submit_job(
    filename: str, cmd_line_arguments: str, job_arguments: dict, clean_up: bool = True
) -> str:
    """Create a qsub job & submit it based on provided file to execute."""
    # Create base string of job id
    base = "submit_{0}".format(random_id())

    # Write the desired python/bash execution to sge job submission file
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
    sge_job_template = sge_generate_startup_file(job_arguments)

    open(base + ".qsub", "w").write(sge_job_template.format(**job_arguments))

    # Submit the job via subprocess call
    command = "qsub < " + base + ".qsub " + "&>/dev/null"
    proc = submit_subprocess(command)

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
        job_info = out.split(b"\n")
        job_id = int(job_info[0].decode("utf-8").split()[0])

    # Wait until the job is listed under the qstat scheduled jobs
    while True:
        try:
            out = sp.check_output(["qstat", "-u", mle_config.sge.credentials.user_name])
            job_info = out.split(b"\n")[2:]
            running_job_ids = [
                int(job_info[i].decode("utf-8").split()[0])
                for i in range(len(job_info) - 1)
            ]
            job_running = job_id in running_job_ids
            if job_running:
                break
        except sp.CalledProcessError as e:
            stderr = e.stderr
            return_code = e.returncode
            print(stderr, return_code)
            time.sleep(0.5)

    # Finally delete all the unnemle_configessary log files
    if clean_up:
        os.remove(base + ".qsub")
    return job_id


def sge_monitor_job(job_id: Union[list, int]) -> bool:
    """Monitor the status of a job based on its id."""
    while True:
        try:
            out = sp.check_output(["qstat", "-u", mle_config.sge.credentials.user_name])
            break
        except sp.CalledProcessError as e:
            stderr = e.stderr
            return_code = e.returncode
            print(stderr, return_code)
            time.sleep(0.5)

    job_info = out.split(b"\n")[2:]
    running_job_ids = [
        int(job_info[i].decode("utf-8").split()[0]) for i in range(len(job_info) - 1)
    ]
    if type(job_id) == int:
        job_id = [job_id]
    S1 = set(job_id)
    S2 = set(running_job_ids)
    job_status = len(S1.intersection(S2)) > 0
    return job_status
