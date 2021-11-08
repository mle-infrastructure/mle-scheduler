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
from .file_management_gcp import delete_gcs_dir


def submit_gcp(
    filename: str,
    cmd_line_arguments: str,
    job_arguments: dict,
    experiment_dir: str,
    gcp_code_dir: str,
    gcp_results_dir: str,
    gcp_bucket_name: str,
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
        gcp_code_dir,
        gcp_results_dir,
        gcp_bucket_name,
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


def clean_up_gcp(
    vm_name: str,
    job_arguments: dict,
    experiment_dir: str,
    gcp_results_dir: str,
    gcp_code_dir: str,
    gcp_project_name: str,
    gcp_bucket_name: str,
):
    """Delete VM instance and code GCS directory."""
    # Delete GCP Job after it terminated (avoid storage billing)
    gcp_delete_vm_instance(vm_name, job_arguments.use_tpus)

    # Delete code dir in GCS bucket (only keep results of computation)
    delete_gcs_dir(gcp_code_dir, gcp_project_name, gcp_bucket_name)

    # Download results back to local directory
    from .file_management_gcp import download_gcs_dir

    download_gcs_dir(
        gcs_path=os.path.join(gcp_results_dir, experiment_dir),
        gcp_project_name=gcp_project_name,
        gcp_bucket_name=gcp_bucket_name,
        local_path="./" + experiment_dir,
    )
