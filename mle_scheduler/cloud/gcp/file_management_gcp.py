import os
import glob
import logging


try:
    from google.cloud import storage
except ModuleNotFoundError as err:
    raise ModuleNotFoundError(
        f"{err}. You need to"
        "install `google-cloud-storage` to use "
        "the `mle_launcher.cloud` module."
    )


def delete_gcs_dir(
    gcs_path: str,
    gcp_project_name: str,
    gcp_bucket_name: str,
    number_of_connect_tries: int = 5,
):
    """Delete a directory in a GCS bucket."""
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    for i in range(number_of_connect_tries):
        try:
            client = storage.Client(gcp_project_name)
            bucket = client.get_bucket(gcp_bucket_name, timeout=20)
        except Exception:
            logger.info(
                f"Attempt {i+1}/{number_of_connect_tries}"
                " - Failed sending to GCloud Storage"
            )

    # Delete all files in directory
    blobs = bucket.list_blobs(prefix=gcs_path)
    for blob in blobs:
        try:
            blob.delete()
        except Exception:
            pass


def upload_local_dir_to_gcs(
    local_path: str,
    gcs_path: str,
    gcp_project_name: str,
    gcp_bucket_name: str,
    number_of_connect_tries: int = 5,
):
    """Send entire dir (recursively) to Google Cloud Storage Bucket."""
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    for i in range(number_of_connect_tries):
        try:
            client = storage.Client(gcp_project_name)
            bucket = client.get_bucket(gcp_bucket_name, timeout=20)
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

    upload_single_file(local_path, gcs_path, bucket)


def download_gcs_dir(
    gcs_path: str,
    gcp_project_name: str,
    gcp_bucket_name: str,
    local_path: str = "",
    number_of_connect_tries: int = 5,
):
    """Download entire dir (recursively) from Google Cloud Storage Bucket."""
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    for i in range(number_of_connect_tries):
        try:
            client = storage.Client(gcp_project_name)
            bucket = client.get_bucket(gcp_bucket_name, timeout=20)
        except Exception:
            logger.info(
                f"Attempt {i+1}/{number_of_connect_tries}"
                f" - Failed sending to GCloud Storage"
            )

    blobs = bucket.list_blobs(prefix=gcs_path)  # Get list of files
    blobs = list(blobs)

    # Recursively download the folder structure
    if len(blobs) > 1:
        local_path = os.path.expanduser(local_path)
        if not os.path.exists(local_path):
            os.makedirs(local_path)
        for blob in blobs:
            filename = blob.name[len(gcs_path) :]
            local_f_path = os.path.join(local_path, filename)
            dir_path = os.path.dirname(local_f_path)

            if not os.path.exists(dir_path):
                try:
                    os.makedirs(dir_path)
                except Exception:
                    pass
            blob.download_to_filename(os.path.join(local_path, filename))
    # Only download single file - e.g. zip compressed experiment
    else:
        for blob in blobs:
            filename = blob.name.split("/")[1]
            blob.download_to_filename(filename)
