# Useful string lego building blocks for GCP startup file formatting
#   1. Copy code directory from GCS bucket
#   2. Setting up tmux session (a) htop (b) startup exec (c) GCS rsync results
#   3. Installation of venv, requirements and jaxlib accelerator dependencies
#   4. Python Base Job File Execution
#   5. Sync Results with GCS bucket

# Inspired by the flax GCP example: https://github.com/google/flax/tree/main/examples/cloud

clone_gcp_bucket_dir = """
mkdir {remote_dir}
sudo chmod 777 {remote_dir}
gsutil cp -r gs://{gcp_bucket_name}/{remote_dir} .
"""

tmux_setup = """
# Login directly with:
# gcloud compute ssh $VM -- sudo_tmux_a.sh
echo -e '#!/bin/bash\nsudo tmux_a.sh' > sudo_tmux_a.sh
chmod a+x sudo_tmux_a.sh
echo -e '#!/bin/bash\ntmux a' > tmux_a.sh
chmod a+x /tmux_a.sh
"""

install_venv = """# Setup virtual env + install base required packages
tmux new-session -s gcp_exp -d htop ENTER
tmux split-window
tmux send "
    set -x
    [ -d gcp_exp ] || (
    cd {remote_dir}
    python3 -m pip install virtualenv
    python3 -m virtualenv env
    . env/bin/activate
    pip install -U pip
    pip install -r requirements.txt
    ) 2>&1 | tee -a log_startup.txt
"
"""

install_additional_setup = """# Setup virtual env + install base required packages
tmux send "
    cd {remote_dir}
    . env/bin/activate
    bash {extra_install_fname}
    "
"""

jax_tpu_build = """# Install jaxlib for TPU
tmux send "
    cd {remote_dir}
    . env/bin/activate
    PYTHON_VERSION=cp36  # Supported python versions: cp36, cp37, cp38
    pip install --upgrade --user https://storage.googleapis.com/jax-releases/tpu/jaxlib-0.1.55+tpu-$PYTHON_VERSION-none-manylinux2010_x86_64.whl
    pip install --upgrade --user jax
    "
"""

jax_gpu_build = """# Install jaxlib for GPU
tmux send "
    cd {remote_dir}
    . env/bin/activate
    pip install --upgrade jax jaxlib==0.1.64+cuda110 -f https://storage.googleapis.com/jax-releases/jax_releases.html
    "
"""

exec_python = """
tmux send "
(
  cd {remote_dir} &&
  . env/bin/activate &&
  python3 {filename} {cmd_line_arguments}
) 2>&1 | tee -a {remote_dir}/log.txt

echo WILL SHUT DOWN IN 5 MIN ...
sleep 100 && sudo shutdown now
"
"""

exec_bash = """
tmux send "
(
  cd {remote_dir} &&
  . env/bin/activate &&
  bash {filename} {cmd_line_arguments}
) 2>&1 | tee -a {remote_dir}/log.txt

echo WILL SHUT DOWN IN 5 MIN ...
sleep 100 && sudo shutdown now
"
"""

sync_results_from_dir = """
# Wait for experiment startup before continuous rsync
sleep 120
tmux split-window -h
tmux send "
while true; do
    gsutil rsync -x 'env' -r {remote_code_dir}/{experiment_dir} gs://{gcp_bucket_name}/{remote_code_dir}/{experiment_dir}
    sleep 10
done
" ENTER
"""
