#!/usr/bin/env python3
"""network_test.py

Run connectivity diagnostics (ping, traceroute, telnet/nc, netstat) from a Domino workspace
and log all outputs to *response.log*.

Features
========
* Verifies that required tools are available; installs them via *dnf/yum* (RHEL/CentOS) or *apt* (Debian/Ubuntu) if missing.
* Accepts a list of target hosts/ports via CLI or environment variable.
* Executes, timestamps and captures the output of:
  - `ping -c 4`  (ICMP reachability)
  - `traceroute` (path)
  - `nc -vz` or `telnet` (TCP port test)
  - `netstat -rn` (routing table) + `ip addr` (interfaces)
* Writes a consolidated **response.log** in the current directory.

Usage
-----
```
python3 network_test.py --targets bu002104645.svc-np.paas.echonet:4202 bu002104644.svc-np.paas.echonet:4201
```
If --targets is omitted, the script reads `TARGETS` env var (comma‑separated host[:port]).

The tool uses *sudo* (if available) to install missing packages; if the workspace is
non‑privileged, installation steps are skipped with a warning.
"""
from __future__ import annotations
import argparse, subprocess, shutil, sys, os, datetime, platform, logging
from pathlib import Path

LOG_FILE = Path("response.log")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("nettest")

# ---------------------- utility helpers ------------------------------------

def run(cmd: list[str], label: str):
    logger.info("=== %s : %s ===", label, " ".join(cmd))
    try:
        out = subprocess.check_output(cmd, stderr=subprocess.STDOUT, text=True, timeout=60)
        logger.info(out)
    except subprocess.CalledProcessError as e:
        logger.error("Command failed with code %s", e.returncode)
        logger.error(e.output)
    except FileNotFoundError:
        logger.error("%s not found", cmd[0])
    except subprocess.TimeoutExpired:
        logger.error("Command %s timed out", cmd[0])


def which_or_install(name: str, packages: list[str]):
    if shutil.which(name):
        return
    logger.warning("%s not installed; attempting automatic install…", name)
    installer = None
    if shutil.which("apt-get"):
        installer = ["sudo", "apt-get", "update"], ["sudo", "apt-get", "-y", "install"] + packages
    elif shutil.which("dnf"):
        installer = ["sudo", "dnf", "-y", "install"] + packages,
    elif shutil.which("yum"):
        installer = ["sudo", "yum", "-y", "install"] + packages,
    else:
        logger.error("No package manager found – install %s manually", ", ".join(packages))
        return
    for cmd in installer:
        try:
            subprocess.check_call(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception as e:
            logger.error("Auto‑install failed: %s", e)
            break

# --------------------------- main logic ------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Connectivity test")
    parser.add_argument("--targets", nargs="*", help="host or host:port list")
    args = parser.parse_args()

    targets = args.targets or os.getenv("TARGETS", "").split(",")
    targets = [t.strip() for t in targets if t.strip()]
    if not targets:
        logger.error("No targets provided. Use --targets or export TARGETS.")
        sys.exit(1)

    # Ensure tools
    which_or_install("ping", ["iputils-ping", "inetutils-ping"])
    which_or_install("traceroute", ["traceroute"])
    # Prefer nc over telnet
    if shutil.which("nc") is None and shutil.which("telnet") is None:
        which_or_install("nc", ["nmap-ncat", "netcat"])
    which_or_install("netstat", ["net-tools"])  # on newer distro, ss may replace netstat

    logger.info("Starting connectivity checks")

    for target in targets:
        host, _, port = target.partition(":")
        logger.info("\n----- Testing %s -----", target)

        run(["ping", "-c", "4", host], label=f"Ping {host}")
        run(["traceroute", "-n", "-w", "2", "-m", "20", host], label=f"Traceroute {host}")

        if port:
            if shutil.which("nc"):
                run(["nc", "-vz", host, port], label=f"nc {host}:{port}")
            elif shutil.which("telnet"):
                run(["telnet", host, port], label=f"telnet {host} {port}")
            else:
                logger.error("Neither nc nor telnet available for TCP test")

    # General network status
    run(["netstat", "-rn"], label="Routing table (netstat -rn)")
    if shutil.which("ip"):
        run(["ip", "addr"], label="IP interfaces (ip addr)")

    logger.info("\nDiagnostics complete – log saved to %s", LOG_FILE.resolve())


if __name__ == "__main__":
    main()
