#!/usr/bin/env python3
"""cos_sync.py

Synchronise a local dataset with **selected objects** from an IBM Cloud Object Storage
(COS) bucket *or* simply inspect the bucket hierarchy.

Main modes
~~~~~~~~~~
* **sync**  (default) – one‑way sync **COS ➜ local**; downloads only new/updated files.
* **tree**             – prints a pretty, indented tree of objects/prefixes.
* **map**              – prints a 2‑column list: `s3://bucket/key  →  /local/path`.

Choose the mode with the `--mode` CLI option (or via CRON by passing the flag).

Environment variables
---------------------
Required
^^^^^^^^
* `COS_ENDPOINT`              – e.g. `https://s3.eu-de.cloud-object-storage.appdomain.cloud`
* `COS_ACCESS_KEY_ID`         – HMAC access key
* `COS_SECRET_ACCESS_KEY`     – HMAC secret key
* `COS_BUCKET_NAME`           – Bucket to work with

Selection (pick ONE mechanism)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
* `COS_OBJECT_KEYS`           – Comma‑separated list of keys to process
  **or**
* `COS_KEYS_FILE`             – Text file with one key per line
  **or**
* `COS_PREFIX`                – Common prefix (default="")

Misc
^^^^
* `DATASET_DIR`               – Local target directory (default: `/mnt/dataset/XXX`)

Install requirements (once):
    pip install ibm-cos-sdk==2.* tqdm

Examples
~~~~~~~~
* **Tree view** of everything under `domino/`:
    ```bash
    export COS_PREFIX="domino/"
    python3 cos_sync.py --mode tree
    ```
* **Sync** explicit list:
    ```bash
    export COS_OBJECT_KEYS="domino/A.csv,domino/B.csv"
    python3 cos_sync.py --mode sync
    ```
* **Cron** every night at 02:00:
    ```cron
    0 2 * * * COS_ENDPOINT=… COS_ACCESS_KEY_ID=… COS_SECRET_ACCESS_KEY=… COS_BUCKET_NAME=… COS_PREFIX=domino/ /usr/bin/python3 /opt/scripts/cos_sync.py --mode sync >> /var/log/cos_sync.log 2>&1
    ```
"""
from __future__ import annotations

import argparse
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

# -------------------------- Selection helpers --------------------------------

def read_key_list() -> list[str] | None:
    """Return an explicit list of object keys, or None if we fall back to prefix."""
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

# ---------------------------- Tree utilities ---------------------------------

def build_tree(keys: Iterable[str]) -> dict:
    root: dict = {}
    for key in keys:
        parts = key.split("/")
        node = root
        for part in parts:
            node = node.setdefault(part, {})
    return root


def print_tree(node: dict, indent: str = "") -> None:
    entries = sorted(node.items())
    for idx, (name, subtree) in enumerate(entries):
        is_last = idx == len(entries) - 1
        branch = "└── " if is_last else "├── "
        print(indent + branch + name)
        if subtree:
            extension = "    " if is_last else "│   "
            print_tree(subtree, indent + extension)

# --------------------------- Sync helpers ------------------------------------

def object_needs_download(remote_ts: float, local_path: Path) -> bool:
    if not local_path.exists():
        return True
    return remote_ts > local_path.stat().st_mtime + 1


def download_object(client, bucket: str, key: str, target: Path) -> bool:
    try:
        meta = client.head_object(Bucket=bucket, Key=key)
    except ClientError as err:
        LOGGER.error("Failed head_object for %s: %s", key, err)
        return False

    remote_size = meta["ContentLength"]
    remote_ts = meta["LastModified"].astimezone(timezone.utc).timestamp()

    if not object_needs_download(remote_ts, target):
        return False

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


# --------------------------- Paginator wrapper --------------------------------

def paginator_keys(client, bucket: str, prefix: str) -> Iterable[str]:
    paginator = client.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get("Contents", []):
            key = obj["Key"]
            if key.endswith("/"):
                continue
            yield key

# ---------------------------------------------------------------------------
# Main routines: tree, map, sync
# ---------------------------------------------------------------------------

def run_tree(client, bucket: str, keys_iter: Iterable[str]):
    tree = build_tree(keys_iter)
    print_tree(tree)


def run_map(dest_dir: Path, keys_iter: Iterable[str]):
    for key in keys_iter:
        print(f"s3://{key} -> {dest_dir / key}")


def run_sync(client, bucket: str, dest_dir: Path, keys_iter: Iterable[str]):
    downloads = 0
    for key in keys_iter:
        if download_object(client, bucket, key, dest_dir / key):
            downloads += 1
    LOGGER.info("Sync complete – %d object(s) downloaded/updated", downloads)

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="COS sync & inspect tool")
    parser.add_argument("--mode", choices=["sync", "tree", "map"], default="sync",
                        help="Action to perform (default: sync)")
    args = parser.parse_args()

    bucket = getenv("COS_BUCKET_NAME", required=True)
    prefix = getenv("COS_PREFIX", "")
    dest_dir = Path(getenv("DATASET_DIR", "/mnt/dataset/XXX")).expanduser()
    dest_dir.mkdir(parents=True, exist_ok=True)

    explicit_keys = read_key_list()
    client = create_cos_client()

    if explicit_keys is None:
        keys_iter: Iterable[str] = paginator_keys(client, bucket, prefix)
    else:
        keys_iter = explicit_keys

    if args.mode == "tree":
        run_tree(client, bucket, keys_iter)
    elif args.mode == "map":
        run_map(dest_dir, keys_iter)
    elif args.mode == "sync":
        run_sync(client, bucket, dest_dir, keys_iter)
    else:
        parser.error("Unknown mode")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        LOGGER.warning("Interrupted by user")
