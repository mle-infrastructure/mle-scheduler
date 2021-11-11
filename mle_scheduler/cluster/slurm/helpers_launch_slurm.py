from .startup_script_slurm import (
    slurm_base_job_config,
    slurm_job_exec,
    slurm_conda_activate,
    slurm_venv_activate,
)


def slurm_generate_startup_file(job_arguments: dict) -> str:
    """Generate the bash script template to submit with SBATCH."""
    # Set the job template depending on the desired number of GPUs
    base_template = (slurm_base_job_config + ".")[:-1]

    # Add desired number of requested gpus
    if "num_gpus" in job_arguments:
        if job_arguments["num_gpus"] > 0:
            base_template += "#SBATCH --gres=gpu:{gpu_type}:{num_gpus}\n"

    # Set the max required memory per job
    if "memory_per_cpu" in job_arguments:
        base_template += "#SBATCH --mem-per-cpu={memory_per_cpu}\n"

    # Set the max required time per job (afterwards terminate)
    if "time_per_job" in job_arguments:
        base_template += "#SBATCH --time={time_per_job}\n"

    # Set the max required memory per job in MB - standardization slurm
    if "memory_per_job" in job_arguments:
        base_template += "#SBATCH --mem={memory_per_job}\n"

    # Add the 'tail' - script execution to the string
    template_out = base_template
    if "use_conda_venv" in job_arguments:
        if job_arguments["use_conda_venv"]:
            template_out += slurm_conda_activate
    elif "use_venv_venv" in job_arguments:
        if job_arguments["use_venv_venv"]:
            template_out += slurm_venv_activate

    # Add optional modules to load (e.g. CUDA, etc.)
    if "modules_to_load" in job_arguments:
        if type(job_arguments["modules_to_load"]) == str:
            template_out += f"\nmodule load {job_arguments['modules_to_load']}"
        elif type(job_arguments["modules_to_load"]) == list:
            for mod in job_arguments["modules_to_load"]:
                template_out += f"\nmodule load {job_arguments['mod']}"
    template_out += slurm_job_exec
    return template_out
