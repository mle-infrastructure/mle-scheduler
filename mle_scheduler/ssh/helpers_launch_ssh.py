import os
from typing import Union


def ssh_get_submission_cmd(
    filename: str,
    cmd_line_arguments: Union[str, None],
    job_arguments: dict,
    ssh_settings: dict,
):
    """Create shell script string to execute on remote SSH server."""
    if cmd_line_arguments is None:
        cmd_line_arguments = ""
    # Write the desired python/bash execution to slurm job submission file
    f_name, f_extension = os.path.splitext(filename)
    if f_extension == ".py":
        cmd = f"python {filename} {cmd_line_arguments}"
    elif f_extension == ".sh":
        cmd = f"bash {filename} {cmd_line_arguments}"
    else:
        raise ValueError(
            f"Script with {f_extension} cannot be handled"
            " by mle-toolbox. Only base .py, .sh experiments"
            " are so far implemented. Please open an issue."
        )

    # Add conda environment activation
    if "use_conda_venv" in job_arguments:
        if job_arguments["use_conda_venv"]:
            script_cmd = "echo $$; /bin/bash -c 'source $(conda info --base)/etc/profile.d/conda.sh && conda activate {} && cd {} && {}'".format(
                job_arguments["env_name"], ssh_settings["remote_dir"], cmd
            )
        else:
            script_cmd = "echo $$; /bin/bash -c 'cd {} && {}'".format(
                ssh_settings["remote_dir"], cmd
            )
    elif "use_venv_venv" in job_arguments:
        if job_arguments["use_venv_venv"]:
            script_cmd = "echo $$; /bin/bash -c 'source {}/{}/bin/activate && cd {} && {}'".format(
                os.environ["WORKON_HOME"],
                job_arguments["env_name"],
                ssh_settings["remote_dir"],
                cmd,
            )
        else:
            script_cmd = "echo $$; /bin/bash -c 'cd {} && {}'".format(
                ssh_settings["remote_dir"], cmd
            )
    else:
        script_cmd = "echo $$; /bin/bash -c 'cd {} && {}'".format(
            ssh_settings["remote_dir"], cmd
        )
    return script_cmd
