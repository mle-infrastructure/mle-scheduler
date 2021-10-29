import subprocess as sp
import time
import datetime
import os
import random
import re
from dotmap import DotMap
from typing import Union
from ..cloud.gcp.helpers_launch_gcp import (
    gcp_generate_startup_file,
    gcp_get_submission_cmd,
    gcp_delete_vm_instance,
)
from mle_toolbox import mle_config


def gcp_check_job_args(job_arguments: Union[dict, None]) -> dict:
    """Check the input job arguments & add default values if missing."""
    if job_arguments is None:
        job_arguments = {}

    # Add the default config values if they are missing from job_args
    for k, v in mle_config.gcp.default_job_arguments.items():
        if k not in job_arguments.keys():
            job_arguments[k] = v

    # If no local code dir provided: Copy over the current working dir
    if "local_code_dir" not in job_arguments.keys():
        job_arguments["local_code_dir"] = os.getcwd()
    return DotMap(job_arguments)


def gcp_submit_job(
    filename: str,
    cmd_line_arguments: str,
    job_arguments: dict,
    experiment_dir: str,
    clean_up: bool = True,
):
    """Create a GCP VM job & submit it based on provided file to execute."""
    # 0. Create VM Name - Timestamp + Random 4 digit id
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    random_str = str(random.randrange(1000, 9999))
    vm_name = "-".join([job_arguments["job_name"], timestamp, random_str])
    vm_name = re.sub(r"[^a-z0-9-]", "-", vm_name)

    # 1. Generate GCP startup file with provided arguments
    startup_fname = vm_name + "-startup.sh"
    if "extra_install_fname" in job_arguments.keys():
        extra_install_fname = job_arguments.extra_install_fname
    else:
        extra_install_fname = None

    gcp_generate_startup_file(
        mle_config.gcp.code_dir,
        mle_config.gcp.results_dir,
        mle_config.gcp.bucket_name,
        filename,
        experiment_dir,
        startup_fname,
        cmd_line_arguments,
        extra_install_fname,
        job_arguments.use_tpus,
        job_arguments.num_gpus > 0,
    )

    # 2. Generate GCP submission command (`gcloud compute instance create ...`)
    gcp_launch_cmd, job_gcp_args = gcp_get_submission_cmd(
        vm_name, job_arguments, startup_fname
    )

    # 3. Launch GCP VM Instance - Everything handled by startup file
    sp.run(gcp_launch_cmd)

    # 4. Wait until job is listed as running (ca. 2 minute!)
    while True:
        try:
            job_running = gcp_monitor_job(vm_name, job_arguments)
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


def gcp_monitor_job(vm_name: str, job_arguments: dict):
    """Monitor status of job based on vm_name. Requires stable connection."""
    # Check VM status from command line
    use_tpu = job_arguments.use_tpus
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
                if use_tpu
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


def gcp_clean_up(vm_name: str, job_arguments: dict, experiment_dir: str):
    """Delete VM instance and code GCS directory."""
    # Delete GCP Job after it terminated (avoid storage billing)
    gcp_delete_vm_instance(vm_name, job_arguments.use_tpus)

    # Delete code dir in GCS bucket (only keep results of computation)
    # delete_gcs_dir(gcs_path=mle_config.gcp.code_dir)

    # Download results back to local directory
    from mle_toolbox.remote.gcloud_transfer import download_gcs_dir

    download_gcs_dir(
        gcs_path=os.path.join(mle_config.gcp.results_dir, experiment_dir),
        local_path="./" + experiment_dir,
    )
