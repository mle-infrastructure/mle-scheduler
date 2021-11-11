from mle_scheduler.ssh.helpers_launch_ssh import ssh_get_submission_cmd

filename = "train.py"
cmd_line_arguments = "-exp_dir logs_ssh_single -config base_config_1.yaml"
job_arguments = {"env_name": "mle-toolbox", "use_conda_venv": True}
ssh_settings = {
    "remote_dir": "mle-code-dir",
}


correct_cmd = "echo $$; /bin/bash -c 'source $(conda info --base)/etc/profile.d/conda.sh && conda activate mle-toolbox && cd mle-code-dir && python train.py -exp_dir logs_ssh_single -config base_config_1.yaml'"


def test_submission_cmd_ssh():
    script_cmd = ssh_get_submission_cmd(
        filename, cmd_line_arguments, job_arguments, ssh_settings
    )
    assert script_cmd == correct_cmd
