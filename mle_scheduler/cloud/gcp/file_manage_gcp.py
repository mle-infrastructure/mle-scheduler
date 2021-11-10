import os
import glob
import logging
from typing import Union
from google.cloud import storage


def send_dir_gcp(
    cloud_settings: dict,
    local_dir: Union[str, None] = None,
    number_of_connect_tries: int = 5,
):
    """Send entire dir (recursively) to Google Cloud Storage Bucket."""
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    for i in range(number_of_connect_tries):
        try:
            client = storage.Client(cloud_settings["project_name"])
            bucket = client.get_bucket(cloud_settings["bucket_name"], timeout=20)
        except Exception:
            logger.info(
                f"Attempt {i+1}/{number_of_connect_tries}"
                " - Failed sending to GCloud Storage"
            )

    def upload_single_file(local_path, gcs_path, bucket):
        # Recursively upload the folder structure
        if os.path.isdir(local_path):
            for local_file in glob.glob(os.path.join(local_path, "**")):
                if not os.path.isfile(local_file):
                    upload_single_file(
                        local_file,
                        os.path.join(gcs_path, os.path.basename(local_file)),
                        bucket,
                    )
                else:
                    remote_path = os.path.join(
                        gcs_path, local_file[1 + len(local_path) :]
                    )
                    blob = bucket.blob(remote_path)
                    blob.upload_from_filename(local_file)
        # Only upload single file - e.g. zip compressed experiment
        else:
            remote_path = gcs_path
            blob = bucket.blob(remote_path)
            blob.upload_from_filename(local_path)

    if local_dir is None:
        local_dir = os.getcwd()
    upload_single_file(local_dir, cloud_settings["remote_dir"], bucket)


def copy_dir_gcp(
    cloud_settings: dict,
    remote_dir: str,
    local_dir: Union[str, None] = None,
    number_of_connect_tries: int = 5,
):
    """Download entire dir (recursively) from Google Cloud Storage Bucket."""
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    for i in range(number_of_connect_tries):
        try:
            client = storage.Client(cloud_settings["project_name"])
            bucket = client.get_bucket(cloud_settings["bucket_name"], timeout=20)
        except Exception:
            logger.info(
                f"Attempt {i+1}/{number_of_connect_tries}"
                f" - Failed sending to GCloud Storage"
            )

    blobs = bucket.list_blobs(prefix=remote_dir)  # Get list of files
    blobs = list(blobs)

    if local_dir is None:
        path = os.path.normpath(remote_dir)
        local_dir = path.split(os.sep)[-1]

    # Recursively download the folder structure
    if len(blobs) > 1:
        local_path = os.path.expanduser(local_dir)
        for blob in blobs:
            filename = blob.name[len(remote_dir) :]
            local_f_path = os.path.join(local_path, filename)
            dir_path = os.path.dirname(local_f_path)

            if not os.path.exists(dir_path):
                try:
                    os.makedirs(dir_path)
                except Exception:
                    pass
            temp_file = local_path + filename
            temp_dir = os.path.split(temp_file)[0]
            if not os.path.exists(temp_dir):
                os.makedirs(temp_dir)
            blob.download_to_filename(temp_file)
    # Only download single file - e.g. zip compressed experiment
    else:
        for blob in blobs:
            filename = blob.name.split("/")[1]
            blob.download_to_filename(filename)


def delete_dir_gcp(
    cloud_settings: dict,
    number_of_connect_tries: int = 5,
):
    """Delete a directory in a GCS bucket."""
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    for i in range(number_of_connect_tries):
        try:
            client = storage.Client(cloud_settings["project_name"])
            bucket = client.get_bucket(cloud_settings["bucket_name"], timeout=20)
        except Exception:
            logger.info(
                f"Attempt {i+1}/{number_of_connect_tries}"
                " - Failed sending to GCloud Storage"
            )

    # Delete all files in directory
    blobs = bucket.list_blobs(prefix=cloud_settings["remote_dir"])
    for blob in blobs:
        try:
            blob.delete()
        except Exception:
            pass
