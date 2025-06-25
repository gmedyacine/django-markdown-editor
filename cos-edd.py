#!/usr/bin/env python3
"""cos_sync.py

Synchronise a local folder with selected objects from an IBM Cloud Object Storage (COS) bucket.
Designed for cron‑based, **one‑way** sync (COS ➜ local dataset).

Key features
------------
* **Incremental** – downloads only new / updated objects.
* **Selective**   – you can provide an explicit list of objects to fetch.
* **Prefix**      – or restrict to a common prefix (default behaviour).
* **Progress bar** with *tqdm*.

Environment variables expected
------------------------------
Required
^^^^^^^^
* `COS_ENDPOINT`              – e.g. `https://s3.eu-de.cloud-object-storage.appdomain.cloud`
* `COS_ACCESS_KEY_ID`         – HMAC access key
* `COS_SECRET_ACCESS_KEY`     – HMAC secret key
* `COS_BUCKET_NAME`           – Name of the bucket to sync from

Selection (choose ONE method)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
* `COS_OBJECT_KEYS`           – Comma‑separated list of object keys to fetch
      *or*
* `COS_KEYS_FILE`             – Path to a text file containing one key per line
      *or*
* `COS_PREFIX`                – Restrict sync to objects starting with this prefix (default="")

Miscellaneous
^^^^^^^^^^^^^
* `DATASET_DIR`               – Local target directory (default: `/mnt/dataset/XXX`)

Install requirements (once):
    pip install ibm-cos-sdk==2.* tqdm

Cron example (sync every hour):
    0 * * * * COS_ENDPOINT=… COS_ACCESS_KEY_ID=… COS_SECRET_ACCESS_KEY=… COS_BUCKET_NAME=… COS_KEYS_FILE=/opt/scripts/my_keys.txt /usr/bin/env python3 /opt/scripts/cos_sync.py >> /var/log/cos_sync.log 2>&1
"""

from __future__ import annotations

import os
import sys
import logging
from pathlib import Path
from datetime import timezone
from typing import Dict, Any, Iterable, List

import ibm_boto3
from ibm_botocore.client import Config
from ibm_botocore.exceptions import ClientError
from tqdm import tqdm

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
LOGGER = logging.getLogger("cos_sync")

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def getenv(name: str, default: str | None = None, *, required: bool = False) -> str | None:
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


def read_key_list() -> list[str] | None:
    """Return an explicit list of object keys if provided, otherwise None."""
    csv_env = getenv("COS_OBJECT_KEYS")
    file_env = getenv("COS_KEYS_FILE")

    if csv_env and file_env:
        LOGGER.error("Specify only one of COS_OBJECT_KEYS or COS_KEYS_FILE, not both.")
        sys.exit(1)

    if csv_env:
        return [k.strip() for k in csv_env.split(",") if k.strip()]

    if file_env:
        path = Path(file_env).expanduser()
        if not path.is_file():
            LOGGER.error("COS_KEYS_FILE %s not found", path)
            sys.exit(1)
        return [line.strip() for line in path.read_text().splitlines() if line.strip()]

    return None  # fall back to prefix walk


def object_needs_download(remote_ts: float, local_path: Path) -> bool:
    """Return True if object is absent locally or remote is newer."""
    if not local_path.exists():
        return True
    local_ts = local_path.stat().st_mtime
    return remote_ts > local_ts + 1  # allow 1‑second margin

# ---------------------------------------------------------------------------
# Main sync logic
# ---------------------------------------------------------------------------

def download_object(client, bucket: str, key: str, target: Path) -> bool:
    """Download a single object if necessary. Returns True if downloaded."""
    try:
        meta = client.head_object(Bucket=bucket, Key=key)
    except ClientError as err:
        LOGGER.error("Failed head_object for %s: %s", key, err)
        return False

    remote_size = meta["ContentLength"]
    remote_ts = meta["LastModified"].astimezone(timezone.utc).timestamp()

    if not object_needs_download(remote_ts, target):
        return False  # already up‑to‑date

    LOGGER.info("Downloading %s (%d bytes)", key, remote_size)
    target.parent.mkdir(parents=True, exist_ok=True)

    with tqdm(total=remote_size, unit="B", unit_scale=True, desc=key, leave=False) as bar:
        client.download_file(
            Bucket=bucket,
            Key=key,
            Filename=str(target),
            Callback=bar.update,
        )

    os.utime(target, (remote_ts, remote_ts))
    return True


def paginator_keys(client, bucket: str, prefix: str) -> Iterable[str]:
    paginator = client.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get("Contents", []):
            key = obj["Key"]
            if key.endswith("/"):
                continue
            yield key


def sync_bucket():
    bucket = getenv("COS_BUCKET_NAME", required=True)
    prefix = getenv("COS_PREFIX", "")
    dest_dir = Path(getenv("DATASET_DIR", "/mnt/dataset/XXX")).expanduser()
    dest_dir.mkdir(parents=True, exist_ok=True)

    selected_keys = read_key_list()

    client = create_cos_client()

    if selected_keys is None:
        LOGGER.info("Sync mode: prefix walk (prefix='%s')", prefix)
        keys_iter: Iterable[str] = paginator_keys(client, bucket, prefix)
    else:
        LOGGER.info("Sync mode: explicit list (%d keys)", len(selected_keys))
        keys_iter = selected_keys

    downloads = 0
    for key in keys_iter:
        target = dest_dir / key
        if download_object(client, bucket, key, target):
            downloads += 1

    LOGGER.info("Sync finished – %d object(s) updated", downloads)


if __name__ == "__main__":
    try:
        sync_bucket()
    except KeyboardInterrupt:
        LOGGER.warning("Interrupted by user")
