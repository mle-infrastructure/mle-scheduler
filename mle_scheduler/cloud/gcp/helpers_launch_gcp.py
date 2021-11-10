import os
import subprocess as sp
from dotmap import DotMap
from typing import Union, Tuple
from .startup_script_gcp import (
    tmux_setup,
    clone_gcp_bucket_dir,
    install_venv,
    install_additional_setup,
    jax_gpu_build,
    jax_tpu_build,
    exec_python,
    exec_bash,
    sync_results_from_dir,
)


cores_to_machine_type = {
    1: "n1-highcpu-2",
    2: "n1-highcpu-4",
    4: "n1-highcpu-8",
    8: "n1-highcpu-16",
    16: "n1-highcpu-32",
    32: "n1-highcpu-64",
    48: "n1-highcpu-96",
}

valid_gpu_types = [
    "nvidia-tesla-p100",
    "nvidia-tesla-v100",
    "nvidia-tesla-t4",
    "nvidia-tesla-p4",
    "nvidia-tesla-k80",
]


base_gcp_args = dict(
    {
        "ZONE": "us-west1-a",
        "ACCELERATOR_TYPE": None,
        "ACCELERATOR_COUNT": 0,
        "MACHINE_TYPE": "n2-highcpu-8",
        "IMAGE_NAME": "c1-deeplearning-tf-2-4-cu110-v20210414-debian-10",
        "IMAGE_PROJECT": "ml-images",
    }
)


tpu_gcp_args = dict(
    {
        "ZONE": "europe-west4-a",
        "ACCELERATOR_TYPE": "v3-8",
        "RUNTIME_VERSION": "v2-alpha",
    }
)


def gcp_get_submission_cmd(
    vm_name: str, job_args: DotMap, startup_fname: str
) -> Tuple[list, dict]:
    """Construct gcloud VM instance creation cmd to execute via cmd line."""
    if job_args["use_tpus"]:
        job_gcp_args = tpu_gcp_args
    else:
        job_gcp_args = base_gcp_args
        # job_gcp_args.MACHINE_TYPE = cores_to_machine_type[
        #                                 job_args.num_logical_cores]
        if job_args["num_gpus"] > 0:
            assert job_args["gpu_type"] in valid_gpu_types
            job_gcp_args["ACCELERATOR_TYPE"] = job_args["gpu_type"]
            job_gcp_args["ACCELERATOR_COUNT"] = job_args["num_gpus"]

    if job_args["use_tpus"]:
        # TPU VM Alpha gcloud create CMD
        gcp_launch_cmd = [
            "gcloud",
            "alpha",
            "compute",
            "tpus",
            "tpu-vm",
            "create",
            f"{vm_name}",
            "--preemptible",
            f"--zone={job_gcp_args['ZONE']}",
            f"--accelerator-type={job_gcp_args['ACCELERATOR_TYPE']}",
            f"--version={job_gcp_args['RUNTIME_VERSION']}",
            f"--metadata-from-file=startup-script={startup_fname}",
            "--no-user-output-enabled",
            "--verbosity",
            "error",
        ]
    else:
        # CPU VM gcloud create CMD w/o any GPU attached
        gcp_launch_cmd = [
            "gcloud",
            "compute",
            "instances",
            "create",
            f"{vm_name}",
            "--preemptible",
            f"--zone={job_gcp_args['ZONE']}",
            f"--custom-cpu={2*job_args['num_logical_cores']}",
            f"--custom-memory={4096 + 2048*job_args['num_logical_cores']}MB",
            "--custom-vm-type=n1",
            f"--image={job_gcp_args['IMAGE_NAME']}",
            f"--image-project={job_gcp_args['IMAGE_PROJECT']}",
            f"--metadata-from-file=startup-script={startup_fname}",
            "--scopes=cloud-platform,storage-full",
            "--boot-disk-size=128GB",
            "--boot-disk-type=pd-standard",
            "--no-user-output-enabled",
            "--verbosity",
            "error",
        ]

        # Attach GPUs to Job if desired - make sure to install nvidia driver
        if (
            job_gcp_args["ACCELERATOR_COUNT"] > 0
            and job_gcp_args["ACCELERATOR_TYPE"] is not None
        ):
            gcp_launch_cmd += [
                "--metadata=install-nvidia-driver=True"
                "--maintenance-policy=TERMINATE",
                f"--accelerator=type={job_gcp_args['ACCELERATOR_TYPE']},"
                f"count={job_gcp_args['ACCELERATOR_COUNT']}",
            ]

    return gcp_launch_cmd, job_gcp_args


def gcp_generate_startup_file(
    remote_code_dir: str,
    gcp_bucket_name: str,
    job_filename: str,
    experiment_dir: str,
    startup_fname: str,
    cmd_line_arguments: str,
    extra_install_fname: Union[None, str],
    use_tpus: bool = False,
    use_cuda: bool = False,
) -> None:
    """Generate bash script template to launch at VM startup."""
    # Build the start job execution script
    # 1. Connecting to tmux via: gcloud compute ssh $VM -- /sudo_tmux_a.sh
    # 2a. Launch venv & install dependencies from requirements.txt
    # 2b. [OPTIONAL] Setup JAX TPU/GPU build
    # 3. Separate tmux split for rsync of results to GCS bucket
    startup_script_content = (
        "#!/bin/bash"
        + tmux_setup
        + clone_gcp_bucket_dir.format(
            remote_dir=remote_code_dir, gcp_bucket_name=gcp_bucket_name
        )
        + install_venv.format(remote_dir=remote_code_dir)
    )

    if extra_install_fname is not None:
        # Bash execute .sh file for additional requirements (if specified)
        startup_script_content += install_additional_setup.format(extra_install_fname)

    if use_tpus:
        # Install TPU version JAX
        startup_script_content += jax_tpu_build
    elif use_cuda:
        # Install GPU version JAX
        startup_script_content += jax_gpu_build

    # Write the desired python/bash execution to slurm job submission file
    f_name, f_extension = os.path.splitext(job_filename)
    if f_extension == ".py":
        startup_script_content += exec_python.format(
            remote_dir=remote_code_dir,
            filename=job_filename,
            cmd_line_arguments=cmd_line_arguments,
        )
    elif f_extension == ".sh":
        startup_script_content += exec_bash.format(
            remote_dir=remote_code_dir,
            filename=job_filename,
            cmd_line_arguments=cmd_line_arguments,
        )
    else:
        raise ValueError(
            f"Script with {f_extension} cannot be handled"
            " by mle-toolbox. Only base .py, .sh experiments"
            " are so far implemented. Please open an issue."
        )

    startup_script_content += sync_results_from_dir.format(
        remote_code_dir=remote_code_dir,
        gcp_bucket_name=gcp_bucket_name,
        experiment_dir=experiment_dir,
    )

    # Write startup script to physical file
    with open(startup_fname, "w", encoding="utf8") as f:
        f.write(startup_script_content)


def gcp_delete_vm_instance(vm_name: str, use_tpus: bool = False) -> None:
    """Quitely delete job by its name + zone. TODO: Add robustness check."""
    vm_zone = "europe-west4-a" if use_tpus else "us-west1-a"
    if not use_tpus:
        gcp_delete_cmd = [
            "gcloud",
            "compute",
            "instances",
            "delete",
            f"{vm_name}",
            "--zone",
            f"{vm_zone}",
            "--quiet",
            "--no-user-output-enabled",
            "--verbosity",
            "error",
        ]
    else:
        gcp_delete_cmd = [
            "gcloud",
            "alpha",
            "compute",
            "tpus",
            "tpu-vm",
            "delete",
            f"{vm_name}",
            "--zone",
            f"{vm_zone}",
            "--quiet",
            "--no-user-output-enabled",
            "--verbosity",
            "error",
        ]
    sp.run(gcp_delete_cmd)
