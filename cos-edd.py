#!/usr/bin/env python3
"""cos_sync.py

Synchronise a local folder with a single IBM Cloud Object Storage (COS) bucket.
Only new or updated objects are downloaded. Intended to be triggered via cron
for one‑way sync (COS ➜ local dataset).

Environment variables expected:
  • COS_ENDPOINT              – e.g. "https://s3.eu-de.cloud-object-storage.appdomain.cloud"
  • COS_ACCESS_KEY_ID         – HMAC access key
  • COS_SECRET_ACCESS_KEY     – HMAC secret key
  • COS_BUCKET_NAME           – Bucket to sync from
  • COS_PREFIX          (opt) – Restrict sync to objects starting with this prefix
  • DATASET_DIR         (opt) – Local directory for download (default: /mnt/dataset/XXX)

Install requirements (once):
    pip install ibm-cos-sdk==2.* tqdm

Add to crontab, e.g. every hour:
    0 * * * * /usr/bin/env python3 /opt/scripts/cos_sync.py >> /var/log/cos_sync.log 2>&1
"""

import os
import sys
import logging
from pathlib import Path
from datetime import timezone
from typing import Dict, Any

import ibm_boto3
from ibm_botocore.client import Config
from ibm_botocore.exceptions import ClientError
from tqdm import tqdm

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
LOGGER = logging.getLogger("cos_sync")

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def getenv(name: str, default: str | None = None, required: bool = False) -> str:
    value = os.getenv(name, default)
    if required and not value:
        LOGGER.error("Environment variable %s is required", name)
        sys.exit(1)
    return value


def create_cos_client():
    endpoint = getenv("COS_ENDPOINT", required=True)
    access_key = getenv("COS_ACCESS_KEY_ID", required=True)
    secret_key = getenv("COS_SECRET_ACCESS_KEY", required=True)

    return ibm_boto3.client(
        "s3",
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        config=Config(signature_version="hmac"),
        endpoint_url=endpoint,
    )


def object_needs_download(obj: Dict[str, Any], local_path: Path) -> bool:
    """Return True if object is absent locally or newer than local copy."""
    if not local_path.exists():
        return True
    # Compare modification timestamps (seconds precision is enough).
    remote_ts = obj["LastModified"].astimezone(timezone.utc).timestamp()
    local_ts = local_path.stat().st_mtime
    return remote_ts > local_ts + 1  # small margin

# ---------------------------------------------------------------------------
# Main sync routine
# ---------------------------------------------------------------------------

def sync_bucket():
    bucket = getenv("COS_BUCKET_NAME", required=True)
    prefix = getenv("COS_PREFIX", "")
    dest_dir = Path(getenv("DATASET_DIR", "/mnt/dataset/XXX")).expanduser()
    dest_dir.mkdir(parents=True, exist_ok=True)

    client = create_cos_client()
    paginator = client.get_paginator("list_objects_v2")

    LOGGER.info("Starting sync from bucket '%s' (prefix '%s') to '%s'", bucket, prefix, dest_dir)

    total_downloaded = 0
    try:
        for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
            for obj in page.get("Contents", []):
                key = obj["Key"]
                if key.endswith("/"):  # skip folders (zero‑byte placeholders)
                    continue
                # Build local path mirroring the key structure
                target = dest_dir / key
                target.parent.mkdir(parents=True, exist_ok=True)

                if object_needs_download(obj, target):
                    LOGGER.info("Downloading %s -> %s", key, target)
                    with tqdm(total=obj["Size"], unit="B", unit_scale=True, desc=key, leave=False) as bar:
                        def _callback(bytes_amount):
                            bar.update(bytes_amount)

                        client.download_file(
                            Bucket=bucket,
                            Key=key,
                            Filename=str(target),
                            Callback=_callback,
                        )
                    # Preserve mtime to the object timestamp
                    mtime = obj["LastModified"].astimezone(timezone.utc).timestamp()
                    os.utime(target, (mtime, mtime))
                    total_downloaded += 1
    except ClientError as err:
        LOGGER.error("IBM COS ClientError: %s", err)
        sys.exit(2)

    LOGGER.info("Sync completed – %d object(s) updated", total_downloaded)


if __name__ == "__main__":
    sync_bucket()
