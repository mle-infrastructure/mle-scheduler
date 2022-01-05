import os
import glob
import time
import logging
from rich.logging import RichHandler
import getpass
from typing import Union
from .local import submit_local, submit_venv, submit_conda
from .ssh import submit_ssh, monitor_ssh
from .cluster import submit_sge, monitor_sge, submit_slurm, monitor_slurm
from .cloud import submit_gcp, monitor_gcp, clean_up_gcp


# Overview of implemented remote resources in addition to local processes
cluster_resources = ["sge-cluster", "slurm-cluster"]
cloud_resources = ["gcp-cloud"]
other_resources = ["ssh-node", "local"]


class MLEJob(object):
    """
    Basic Job Class - Everything builds on this!

    This class defines, executes & monitors an individual job that can
    either be run locally, on a sungrid-engine (SGE) or SLURM cluster.

    Args:
        resource_to_run (str): Compute resource to execute job on.

        job_filename (str): filepath to .py script to be executed for job.

        config_filename (str): filepath to .json file specifying configuration
            of experiment to be executed in this job.

        job_arguments (dict): ressources required for this specific job.

        experiment_dir (str): set path for logging & unique storage of results.

        cmd_line_input (dict): provides standardized cmd input to .py file in
            job submission. Includes -config, -exp_dir, -seed.

        extra_cmd_line_input (dict): provides additional cmd input .py file
            in job submission. Dictionary should be structured so that input
            are passed as -<key> <value>.

        logger_level (str): control logger verbosity of individual experiment.

    Methods:
        run: Executes job, logs it & returns status if job done
        schedule: Schedules job locally or remotely
        schedule_local: Schedules job locally on your machine
        schedule_cluster: Schedules job remotely on SGE/Slurm clusters
        monitor: Monitors job locally or remotely
        monitor_local: Monitors job locally on your machine
        monitor_cluster: Monitors job remotely on SGE/Slurm clusters
    """

    def __init__(
        self,
        resource_to_run: str,
        job_filename: str,
        job_arguments: dict = {},
        config_filename: Union[None, str] = None,
        experiment_dir: Union[None, str] = None,
        seed_id: Union[None, int] = None,
        extra_cmd_line_input: Union[None, dict] = None,
        delete_config: bool = False,
        debug_mode: bool = False,
        cloud_settings: Union[dict, None] = None,
        ssh_settings: Union[dict, None] = None,
        logger_level: int = logging.WARNING,
    ):
        # Init job class with relevant info
        self.resource_to_run = resource_to_run  # compute resource for job
        self.job_filename = job_filename  # path to train script
        self.config_filename = config_filename  # path to config json
        self.job_arguments = job_arguments.copy()  # Job resource configuration
        self.experiment_dir = experiment_dir  # main results dir (create)
        self.seed_id = seed_id  # random seed to be passed as cmd-line arg
        self.delete_config = delete_config  # Option to delete config file after run
        self.debug_mode = debug_mode  # Pipe stdout and stderr to files
        self.user_name = getpass.getuser()

        # Create command line arguments for job to schedule (passed to .py)
        self.cmd_line_args = self.generate_cmd_line_args()
        # Add additional cmd line args if extra ones are specified
        if extra_cmd_line_input is not None:
            self.cmd_line_args = self.generate_extra_cmd_line_args(
                self.cmd_line_args, extra_cmd_line_input.copy()
            )

        # GCP/SSH configurations
        if self.resource_to_run in cloud_resources:
            assert cloud_settings is not None
        self.cloud_settings = cloud_settings

        if self.resource_to_run == "ssh-node":
            assert ssh_settings is not None
        self.ssh_settings = ssh_settings

        # Instantiate/connect a logger
        FORMAT = "%(message)s"
        logging.basicConfig(
            level=logger_level, format=FORMAT, datefmt="[%X]", handlers=[RichHandler()]
        )

        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logger_level)

    def run(self) -> bool:
        """Schedule experiment, monitor and clean up afterwards."""
        # Schedule job, create success boolean and job identifier
        job_id = self.schedule()
        # Monitor status of job based on identifier
        status_out = self.monitor(job_id, continuous=True)
        # If they exist - remove log & error file
        self.clean_up(job_id)
        return status_out

    def schedule(self) -> str:
        """Schedule job on cluster (sge/slurm), cloud (gcp) or locally."""
        if self.resource_to_run in cluster_resources:
            job_id = self.schedule_cluster()
            if self.job_status == 1:
                self.logger.info(
                    f"Job ID: {job_id} - Cluster job scheduled"
                    f" - {self.config_filename}"
                )
            else:
                self.logger.info(
                    f"Job ID: {job_id} - Error when scheduling "
                    f"cluster job - {self.config_filename}"
                )
        elif self.resource_to_run in cloud_resources:
            job_id = self.schedule_cloud()
            if self.job_status == 1:
                self.logger.info(
                    f"VM Name: {job_id} - Cloud job scheduled"
                    f" - {self.config_filename}"
                )
            else:
                self.logger.info(
                    f"VM Name: {job_id} - Error when scheduling "
                    f"cloud job - {self.config_filename}"
                )
        elif self.resource_to_run == "local":
            job_id = self.schedule_local()
            if self.job_status == 1:
                self.logger.info(
                    f"PID: {job_id.pid} - Local job scheduled "
                    f"- {self.config_filename}"
                )
            else:
                self.logger.info(
                    f"PID: {job_id.pid} - Error when scheduling "
                    f"local job - {self.config_filename}"
                )
        elif self.resource_to_run == "ssh-node":
            job_id = self.schedule_ssh()
            if self.job_status == 1:
                self.logger.info(
                    f"PID: {job_id} - SSH job scheduled " f"- {self.config_filename}"
                )
            else:
                self.logger.info(
                    f"PID: {job_id.pid} - Error when scheduling "
                    f"SSH job - {self.config_filename}"
                )
        else:
            raise ValueError(f"{self.resource_to_run} is not implemented.")
        # Return sge/slurm - job_id (qstat/squeue), gcp - vm_name, ssh/local - proc
        return job_id

    def monitor(self, job_id: str, continuous: bool = True) -> bool:
        """
        Monitor on cluster (sge/slurm), cloud (gcp) or locally via id.
        If 'continuous' bool is true, then monitor until experiment status 0.
        """
        if self.resource_to_run in cluster_resources:
            if continuous:
                self.logger.info(
                    f"Job ID: {job_id} - Started monitoring - {self.config_filename}"
                )
            status_out = self.monitor_cluster(job_id, continuous)
            if status_out == 0:
                self.logger.info(
                    f"Job ID: {job_id} - Cluster job completed - {self.config_filename}"
                )
        elif self.resource_to_run in cloud_resources:
            if continuous:
                self.logger.info(
                    f"VM Name: {job_id} - Started monitoring - {self.config_filename}"
                )
            status_out = self.monitor_cloud(job_id, continuous)
            if status_out == 0:
                self.logger.info(
                    f"VM Name: {job_id} - Cloud job completed - {self.config_filename}"
                )
        elif self.resource_to_run == "ssh-node":
            if continuous:
                self.logger.info(
                    f"SSH PID: {job_id} - Started monitoring - {self.config_filename}"
                )
            status_out = self.monitor_ssh(job_id, continuous)
            if status_out == 0:
                self.logger.info(
                    f"SSH PID: {job_id} - SSH job completed - {self.config_filename}"
                )
        elif self.resource_to_run == "local":
            if continuous:
                self.logger.info(
                    f"PID: {job_id.pid} - Started monitoring - {self.config_filename}"
                )
            status_out = self.monitor_local(job_id, continuous)
            if status_out == 0:
                self.logger.info(
                    f"PID: {job_id.pid} - Local job completed - { self.config_filename}"
                )
        return status_out

    def schedule_local(self):
        """Schedules job locally on your machine."""
        if "use_conda_venv" in self.job_arguments.keys():
            if self.job_arguments["use_conda_venv"]:
                proc = submit_conda(
                    self.job_filename,
                    self.cmd_line_args,
                    self.job_arguments,
                    self.debug_mode,
                )
            else:
                proc = submit_local(
                    self.job_filename, self.cmd_line_args, self.debug_mode
                )
        elif "use_venv_venv" in self.job_arguments.keys():
            if self.job_arguments["use_venv_venv"]:
                proc = submit_venv(
                    self.job_filename,
                    self.cmd_line_args,
                    self.job_arguments,
                    self.debug_mode,
                )
            else:
                proc = submit_local(
                    self.job_filename, self.cmd_line_args, self.debug_mode
                )
        else:
            proc = submit_local(self.job_filename, self.cmd_line_args, self.debug_mode)
        self.job_status = 1
        return proc

    def schedule_ssh(self):
        """Schedules job on SSH servers."""
        proc = submit_ssh(
            self.job_filename,
            self.cmd_line_args,
            self.job_arguments,
            self.ssh_settings,
            self.debug_mode,
        )
        self.job_status = 1
        return proc

    def schedule_cluster(self) -> int:
        """Schedules job to run remotely on SGE or Slurm clusters."""
        if self.resource_to_run == "sge-cluster":
            job_id = submit_sge(
                self.job_filename,
                self.cmd_line_args,
                self.job_arguments,
                self.user_name,
                self.debug_mode,
                clean_up=True,
            )
        elif self.resource_to_run == "slurm-cluster":
            job_id = submit_slurm(
                self.job_filename,
                self.cmd_line_args,
                self.job_arguments,
                self.user_name,
                self.debug_mode,
                clean_up=True,
            )
        if job_id == -1:
            self.job_status = 0
        else:
            self.job_status = 1
        return job_id

    def schedule_cloud(self) -> int:
        """Schedules job to run remotely on GCP cloud."""
        if self.resource_to_run == "gcp-cloud":
            # Submit VM Creation + Startup exec
            job_id = submit_gcp(
                self.job_filename,
                self.cmd_line_args,
                self.experiment_dir,
                self.job_arguments,
                self.debug_mode,
                self.cloud_settings,
            )
        if job_id == -1:
            self.job_status = 0
        else:
            self.job_status = 1
        return job_id

    def monitor_local(self, proc, continuous: bool = True) -> int:
        """Monitors job locally on your machine."""
        # Poll status of local process & change status when done
        if continuous:
            while self.job_status:
                poll = proc.poll()
                if poll is None:
                    continue
                else:
                    self.job_status = 0
                # Sleep until next status check
                time.sleep(1)

            # Get output & error messages (if there is an error)
            out, err = proc.communicate()
            # Return -1 if job failed & 0 otherwise
            if proc.returncode != 0:
                print(out, err)
                return -1
            else:
                return 0
        else:
            poll = proc.poll()

            # Get output & error messages (if there is an error)
            out, err = proc.communicate()
            if poll is None:
                return 1
            else:
                return 0

    def monitor_ssh(self, proc, continuous: bool = True) -> int:
        """Monitors job remotely on SSH server."""
        # Poll status of local process & change status when done
        if continuous:
            while self.job_status:
                self.job_status = monitor_ssh(proc, self.ssh_settings)
                # Sleep until next status check
                time.sleep(1)
            return 0
        else:
            return monitor_ssh(proc, self.ssh_settings)

    def monitor_cluster(self, job_id: str, continuous: bool = True) -> int:
        """Monitors job remotely on SGE or Slurm clusters."""
        if continuous:
            while self.job_status:
                if self.resource_to_run == "sge-cluster":
                    self.job_status = monitor_sge(job_id, self.user_name)
                elif self.resource_to_run == "slurm-cluster":
                    self.job_status = monitor_slurm(job_id, self.user_name)
                time.sleep(1)
            return 0
        else:
            if self.resource_to_run == "sge-cluster":
                return monitor_sge(job_id, self.user_name)
            elif self.resource_to_run == "slurm-cluster":
                return monitor_slurm(job_id, self.user_name)

    def monitor_cloud(self, job_id: str, continuous: bool = True) -> int:
        """Monitors job remotely on GCP cloud."""
        if continuous:
            while self.job_status:
                if self.resource_to_run == "gcp-cloud":
                    self.job_status = monitor_gcp(job_id, self.job_arguments)
                time.sleep(10)
            return 0
        else:
            if self.resource_to_run == "gcp-cloud":
                return monitor_gcp(job_id, self.job_arguments)

    def clean_up(self, job_id: str) -> None:
        """Remove error and log files at end of training."""
        if self.resource_to_run in cluster_resources:
            for filename in glob.glob("err.err"):
                try:
                    os.remove(filename)
                except Exception:
                    pass
            for filename in glob.glob("log.txt"):
                try:
                    os.remove(filename)
                except Exception:
                    pass
            self.logger.info("Cleaned up log, error, results files")

        # Delete VM instance and code directory stored in data bucket
        if self.resource_to_run == "gcp-cloud":
            clean_up_gcp(
                job_id, self.job_arguments, self.experiment_dir, self.cloud_settings
            )
            self.logger.info(f"VM Name: {job_id} - Delete VM - {self.config_filename}")

        # If desired also delete configuration files
        if self.delete_config:
            os.remove(self.config_filename)

    def generate_cmd_line_args(self) -> str:
        """Generate cmd line args for .py -> get_train_configs_ready"""
        cmd_line_args = ""
        if self.experiment_dir is not None:
            cmd_line_args += " -exp_dir " + self.experiment_dir

        if self.config_filename is not None:
            cmd_line_args += " -config " + self.config_filename

        if self.seed_id is not None:
            cmd_line_args += " -seed " + str(self.seed_id)
            # Update the job argument details with the seed-job-id
            if "job_name" in self.job_arguments.keys():
                self.job_arguments["job_name"] += "-" + str(self.seed_id)
            else:
                self.job_arguments["job_name"] = str(self.seed_id)
        return cmd_line_args

    def generate_extra_cmd_line_args(
        self, cmd_line_args: str, extra_cmd_line_input: Union[None, dict] = None
    ) -> str:
        """Generate extra cmd line args for .py -> e.g. for postproc"""
        full_cmd_line_args = (cmd_line_args + ".")[:-1]
        if extra_cmd_line_input is not None:
            for k, v in extra_cmd_line_input.items():
                full_cmd_line_args += " -" + k + " " + str(v)
        return full_cmd_line_args
