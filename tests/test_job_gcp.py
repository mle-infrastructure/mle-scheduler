from mle_scheduler.cloud.gcp.helpers_launch_gcp import gcp_get_submission_cmd

vm_name = "temp-vm"
job_arguments = {
    "use_tpus": 0,
    "num_gpus": 0,
    "gpu_type": "nvidia-tesla-v100",
    "num_logical_cores": 1,
    "job_name": "test",
}
startup_fname = "temp-vm"

correct_gcp_launch_cmd = [
    "gcloud",
    "compute",
    "instances",
    "create",
    "temp-vm",
    "--preemptible",
    "--zone=us-west1-a",
    "--custom-cpu=2",
    "--custom-memory=6144MB",
    "--custom-vm-type=n1",
    "--image=c1-deeplearning-tf-2-4-cu110-v20210414-debian-10",
    "--image-project=ml-images",
    "--metadata-from-file=startup-script=temp-vm.sh",
    "--scopes=cloud-platform,storage-full",
    "--boot-disk-size=128GB",
    "--boot-disk-type=pd-standard",
    "--no-user-output-enabled",
    "--verbosity",
    "error",
]
correct_job_gcp_args = {
    "ZONE": "us-west1-a",
    "ACCELERATOR_TYPE": None,
    "ACCELERATOR_COUNT": 0,
    "MACHINE_TYPE": "n2-highcpu-8",
    "IMAGE_NAME": "c1-deeplearning-tf-2-4-cu110-v20210414-debian-10",
    "IMAGE_PROJECT": "ml-images",
}


def test_submission_cmd_gcp():
    gcp_launch_cmd, job_gcp_args = gcp_get_submission_cmd(
        vm_name, job_arguments, startup_fname
    )
    return
