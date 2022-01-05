import subprocess as sp
import time
import datetime
import os
import random
import re
from .helpers_launch_gcp import (
    gcp_generate_startup_file,
    gcp_get_submission_cmd,
    gcp_delete_vm_instance,
)


def submit_gcp(
    filename: str,
    cmd_line_arguments: str,
    experiment_dir: str,
    job_arguments: dict,
    debug_mode: bool,
    cloud_settings: dict,
):
    """Create a GCP VM job & submit it based on provided file to execute."""
    if "job_name" not in job_arguments:
        job_arguments["job_name"] = "job"

    if "use_tpus" not in job_arguments:
        job_arguments["use_tpus"] = 0

    if "num_gpus" not in job_arguments:
        job_arguments["num_gpus"] = 0

    # 0. Create VM Name - Timestamp + Random 4 digit id
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    random_str = str(random.randrange(1000, 9999))
    vm_name = "-".join(["mle", timestamp, random_str])
    vm_name = re.sub(r"[^a-z0-9-]", "-", vm_name)

    # 1. Generate GCP startup file with provided arguments
    startup_fname = vm_name + "-startup.sh"
    if "extra_install_fname" in job_arguments:
        extra_install_fname = job_arguments["extra_install_fname"]
    else:
        extra_install_fname = None

    gcp_generate_startup_file(
        cloud_settings["remote_dir"],
        cloud_settings["bucket_name"],
        filename,
        experiment_dir,
        startup_fname,
        cmd_line_arguments,
        extra_install_fname,
        job_arguments["use_tpus"],
        job_arguments["num_gpus"] > 0,
    )

    # 2. Generate GCP submission command (`gcloud compute instance create ...`)
    gcp_launch_cmd, job_gcp_args = gcp_get_submission_cmd(
        vm_name, job_arguments, startup_fname
    )

    if debug_mode:
        gcp_launch_cmd += " 2>>err.err 1>>log.txt"

    # 3. Launch GCP VM Instance - Everything handled by startup file
    sp.run(gcp_launch_cmd)

    # 4. Wait until job is listed as running (ca. 2 minute!)
    while True:
        try:
            job_running = monitor_gcp(vm_name, job_arguments)
            if job_running == 1:
                # Delete statup bash file
                try:
                    os.remove(startup_fname)
                except Exception:
                    pass
                return vm_name
            time.sleep(10)
        except sp.CalledProcessError as e:
            stderr = e.stderr
            return_code = e.returncode
            print(stderr, return_code)
            time.sleep(2)

    # Return -1 if job was not listed as starting/running within 100 seconds!
    return -1


def monitor_gcp(vm_name: str, job_arguments: dict):
    """Monitor status of job based on vm_name. Requires stable connection."""
    # Check VM status from command line
    while True:
        try:
            check_cmd = (
                [
                    "gcloud",
                    "alpha",
                    "compute",
                    "tpus",
                    "--zone",
                    "europe-west4-a",
                    "--verbosity",
                    "critical",
                ]
                if job_arguments["use_tpus"]
                else [
                    "gcloud",
                    "compute",
                    "instances",
                    "list",
                    "--verbosity",
                    "critical",
                ]
            )
            out = sp.check_output(check_cmd)
            break
        except sp.CalledProcessError as e:
            stderr = e.stderr
            return_code = e.returncode
            print(stderr, return_code)
            time.sleep(1)

    # Clean up and check if vm_name is in list of all jobs
    job_info = out.split(b"\n")[1:-1]
    running_job_names = []
    for i in range(len(job_info)):
        decoded_job_info = job_info[i].decode("utf-8").split()
        if decoded_job_info[-1] in ["STAGING", "RUNNING"]:
            running_job_names.append(decoded_job_info[0])
    job_status = vm_name in running_job_names
    return job_status


def clean_up_gcp(
    vm_name: str,
    job_arguments: dict,
    experiment_dir: str,
    cloud_settings: dict,
):
    """Delete VM instance and code GCS directory."""
    # Delete GCP Job after it terminated (avoid storage billing)
    gcp_delete_vm_instance(vm_name, job_arguments["use_tpus"])
