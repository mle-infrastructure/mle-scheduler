import os
import logging
import time
import datetime
from typing import Union, List
import numpy as np
from rich.logging import RichHandler
from rich.progress import (
    BarColumn,
    Progress,
    TextColumn,
    TimeElapsedColumn,
    SpinnerColumn,
)
from .job import MLEJob
from .ssh import send_dir_ssh, copy_dir_ssh, delete_dir_ssh
from .cloud.gcp import send_dir_gcp, copy_dir_gcp, delete_dir_gcp


class MLEQueue(object):
    """
    Multi-Seed Job Class: This is essentially a for-loop handler for
    the `Job` class when running multiple random seeds.
    """

    def __init__(
        self,
        resource_to_run: str,
        job_filename: str,
        config_filenames: Union[str, List[str]],
        job_arguments: dict = {},
        experiment_dir: str = "experiments/",
        num_seeds: int = 1,
        default_seed: int = 0,
        random_seeds: Union[None, List[int]] = None,
        max_running_jobs: int = 10,
        automerge_seeds: bool = False,
        cloud_settings: Union[dict, None] = None,
        ssh_settings: Union[dict, None] = None,
        slack_message_id: Union[str, None] = None,
        slack_user_name: Union[str, None] = None,
        slack_auth_token: Union[str, None] = None,
        logger_level: int = logging.WARNING,
    ):
        # Init experiment class with relevant info
        self.resource_to_run = resource_to_run  # compute resource for job
        self.job_filename = job_filename  # path to train script
        self.config_filenames = config_filenames  # path to config json
        self.experiment_dir = experiment_dir  # main results dir (create)
        self.job_arguments = job_arguments.copy()  # job-specific args
        self.num_seeds = num_seeds  # number seeds to run
        self.max_running_jobs = max_running_jobs  # number of sim running jobs

        # Slack Clusterbot Configuration
        self.slack_message_id = slack_message_id  # Message ts id for slack bot
        self.slack_user_name = slack_user_name  # Slack user name to send message to
        self.slack_auth_token = slack_auth_token  # Slack Authentication Token

        # Virtual environment usage & GCS code directory/SSH settings
        self.cloud_settings = cloud_settings
        self.ssh_settings = ssh_settings

        if resource_to_run == "ssh-node":
            if self.ssh_settings["start_up_copy_dir"]:
                send_dir_ssh(self.ssh_settings)

        if resource_to_run == "gcp-cloud":
            if self.cloud_settings["start_up_copy_dir"]:
                send_dir_gcp(self.cloud_settings)

        # Instantiate/connect a logger
        FORMAT = "%(message)s"
        logging.basicConfig(
            level=logger_level, format=FORMAT, datefmt="[%X]", handlers=[RichHandler()]
        )

        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logger_level)

        # Check whether enough seeds explicitly supplied
        if random_seeds is not None:
            self.random_seeds = random_seeds
            self.num_seeds = len(self.random_seeds)

        # Generate a list of dictionaries with different random seed cmd input
        if self.num_seeds > 1 and random_seeds is None:
            seeds_to_sample = np.arange(100000, 999999)
            self.random_seeds = np.random.choice(
                seeds_to_sample, self.num_seeds, replace=False
            ).tolist()
        elif self.num_seeds == 1 and random_seeds is None:
            self.random_seeds = [default_seed]
        self.automerge_seeds = automerge_seeds

        # Extract extra_cmd_line_input from job_arguments
        if self.job_arguments is not None:
            if "extra_cmd_line_input" in self.job_arguments.keys():
                self.extra_cmd_line_input = self.job_arguments["extra_cmd_line_input"]
                del self.job_arguments["extra_cmd_line_input"]
            else:
                self.extra_cmd_line_input = None

        # Make sure that config_filenames is list of strings to loop over
        if type(self.config_filenames) != list:
            self.config_filenames = list(self.config_filenames)

        # Generate a list of jobs to be queued/executed on the resource
        # Recreate directory in which the results are stored - later merge
        # 3 status types: -1 - not started yet; 0 - completed, 1 - running
        timestr = datetime.datetime.today().strftime("%Y-%m-%d")[2:] + "_"
        self.queue = []
        for config_fname in self.config_filenames:
            base_str = os.path.split(config_fname)[1].split(".")[0]
            for seed_id in self.random_seeds:
                self.queue.append(
                    {
                        "config_fname": config_fname,
                        "seed_id": seed_id,
                        "base_str": base_str,
                        "experiment_dir": os.path.join(
                            experiment_dir, timestr + base_str
                        ),
                        "log_dir": os.path.join(
                            experiment_dir, timestr + base_str + "/logs/"
                        ),
                        "status": -1,
                        "job": None,
                        "job_id": None,
                        "merged_logs": False,
                    }
                )

        self.queue_counter = 0  # Next job to schedule
        self.num_completed_jobs = 0  # No. already completed jobs
        self.num_running_jobs = 0  # No. of currently running jobs
        self.num_total_jobs = len(self.queue)

        self.logger.info(
            "Queued - {} random seeds - {} configs".format(
                self.num_seeds, len(self.config_filenames)
            )
        )

    def run(self) -> None:
        """Schedule -> Monitor -> Merge individual logs."""
        # 1. Spawn 1st batch of evals until limit of allowed usage is reached
        while self.num_running_jobs < min(self.max_running_jobs, self.num_total_jobs):
            job, job_id = self.launch(self.queue_counter)
            self.queue[self.queue_counter]["status"] = 1
            self.queue[self.queue_counter]["job"] = job
            self.queue[self.queue_counter]["job_id"] = job_id
            self.num_running_jobs += 1
            self.queue_counter += 1
            time.sleep(0.1)
        self.logger.info(
            "Launch - Set of {}/{} Jobs".format(
                self.num_running_jobs, self.num_total_jobs
            )
        )

        # 2. Set up Progress Bar Counter of completed jobs (& slack bot)
        progress = Progress(
            SpinnerColumn(),
            TextColumn(
                f"[bold blue]MLEQueue - {self.resource_to_run} •",
                justify="left",
            ),
            TextColumn(
                "{task.completed}/{task.total} Jobs",
                justify="left",
            ),
            BarColumn(bar_width=30, style="magenta"),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}% •"),
            TimeElapsedColumn(),
            TextColumn(":hourglass:", justify="right"),
        )

        if self.slack_user_name is not None and self.slack_auth_token is not None:
            try:
                from clusterbot import ClusterBot
            except ImportError:
                raise ImportError(
                    "You need to install & setup `slack-clusterbot` to "
                    "use status notifications."
                )
            logger = logging.getLogger("clusterbot")
            logger.setLevel(logging.WARNING)
            slackbot = ClusterBot(
                slack_token=self.slack_auth_token,
                user_name=self.slack_user_name,
            )
            if self.slack_message_id is None:
                self.slack_message_id = slackbot.send(
                    f":rocket: Start running {self.num_total_jobs} jobs :rocket:\n"
                    f"→ Compute resource: `{self.resource_to_run}`\n"
                    f"→ Bash execution file: `{self.job_filename}`\n"
                    f"→ Config .yaml: `{self.config_filenames}`\n"
                    f"→ Seeds: `{self.random_seeds}`",
                    user_name=self.slack_user_name,
                )
            slackbot.init_pbar(self.num_total_jobs, ts=self.slack_message_id)

        # 3. Monitor & launch new waiting jobs when resource available
        with progress:
            task = progress.add_task("queue", total=self.num_total_jobs)
            while self.num_completed_jobs < self.num_total_jobs:
                # Once budget is fully allocated - start monitor running jobs
                # Loop over all jobs in queue - check status of prev running
                for job in self.queue:
                    if job["status"] == 1:
                        status = self.monitor(job["job"], job["job_id"], False)
                        # If status changes to completed - update counters/state
                        if status == 0:
                            self.num_completed_jobs += 1
                            self.num_running_jobs -= 1
                            job["status"] = 0
                            progress.advance(task)
                            if (
                                self.slack_user_name is not None
                                and self.slack_auth_token is not None
                            ):
                                slackbot.update_pbar()

                            # Merge seeds of one eval/config if all jobs done!
                            completed_seeds = 0
                            for other_job in self.queue:
                                if other_job["config_fname"] == job["config_fname"]:
                                    if other_job["status"] == 0:
                                        completed_seeds += 1
                            if (
                                completed_seeds == self.num_seeds
                                and self.automerge_seeds
                            ):
                                self.merge_seeds(job["experiment_dir"], job["base_str"])
                    time.sleep(0.1)

                # Once budget becomes available again - fill up with new jobs
                while self.num_running_jobs < min(
                    self.max_running_jobs,
                    self.num_total_jobs
                    - self.num_completed_jobs
                    - self.num_running_jobs,
                ):
                    job, job_id = self.launch(self.queue_counter)
                    self.queue[self.queue_counter]["status"] = 1
                    self.queue[self.queue_counter]["job"] = job
                    self.queue[self.queue_counter]["job_id"] = job_id
                    self.num_running_jobs += 1
                    self.queue_counter += 1
                    time.sleep(0.1)

        self.logger.info(
            "Completed - Set of {}/{} Jobs".format(
                self.num_total_jobs, self.num_total_jobs
            )
        )

        if self.resource_to_run == "ssh-node":
            copy_dir_ssh(
                self.ssh_settings,
                remote_dir=os.path.join(
                    self.ssh_settings["remote_dir"], self.experiment_dir
                ),
            )
            self.logger.info(f"Pulled SSH results - {self.experiment_dir}")
            # Clean up the scp code directory
            if "clean_up_remote_dir" in self.ssh_settings.keys():
                if self.ssh_settings["clean_up_remote_dir"]:
                    delete_dir_ssh(self.ssh_settings)
                    self.logger.info(
                        f"Deleted SSH directory - {self.ssh_settings['remote_dr']}"
                    )

        elif self.resource_to_run == "gcp-cloud":
            copy_dir_gcp(
                self.cloud_settings,
                remote_dir=os.path.join(
                    self.cloud_settings["remote_dir"], self.experiment_dir
                ),
            )
            self.logger.info(f"Pulled cloud results - {self.experiment_dir}")
            # Clean up the scp code directory
            if "clean_up_remote_dir" in self.cloud_settings.keys():
                if self.cloud_settings["clean_up_remote_dir"]:
                    delete_dir_gcp(self.cloud_settings)
                    self.logger.info(
                        f"Deleted cloud directory - {self.ssh_settings['remote_dr']}"
                    )

    def launch(self, queue_counter):
        """Launch a set of jobs for one configuration - one for each seed."""
        # 1. Instantiate the experiment class and start a single seed
        job = MLEJob(
            self.resource_to_run,
            self.job_filename,
            self.queue[queue_counter]["config_fname"],
            self.job_arguments,
            self.experiment_dir,
            self.queue[queue_counter]["seed_id"],
            self.extra_cmd_line_input,
            self.cloud_settings,
            self.ssh_settings,
        )

        # 2. Launch a single experiment
        job_id = job.schedule()

        # 3. Return updated counter, `Job` instance & corresponding ID
        return job, job_id

    def monitor(self, job: MLEJob, job_id: str, continuous: bool = True):
        """Monitor all seed-specific jobs for one eval configuration."""
        if continuous:
            while True:
                status = job.monitor(job_id, False)
                if status == 0:
                    return 0
        else:
            status = job.monitor(job_id, False)
            return status

    def merge_seeds(self, experiment_dir: str, base_str: str) -> None:
        """Collect all seed-specific seeds into single <eval_id>.hdf5 file."""
        try:
            from mle_logging import merge_seed_logs
        except ModuleNotFoundError as err:
            raise ModuleNotFoundError(
                f"{err}. You need to install `mle_logging` "
                "to use the `merge_seeds` method."
            )

        # Only merge logs if job is based on python job!
        # Otherwise .hdf5 file system is not used and there is nothing to merge
        filename, file_extension = os.path.splitext(self.job_filename)
        if file_extension == ".py":
            merged_path = os.path.join(experiment_dir, "logs", base_str + ".hdf5")
            merge_seed_logs(merged_path, experiment_dir, self.num_seeds)
