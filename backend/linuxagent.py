#!/usr/bin/env python3
"""
tail_common_logs.py

Tails only the most common Linux log files (not recursive).
Reads new lines every minute and writes them to timestamped snapshots.

Behavior:
- On FIRST run (no .log_offsets.json): starts from the END of each existing log,
  so it only captures NEW lines that appear after the script starts.
- On later runs: resumes from saved offsets like before.
- Output files contain ONLY raw new log lines (no headers).
- Snapshot filenames include the machine's hostname and timestamp.
- Each non-empty snapshot is sent to a central logging server via HTTP POST.
"""

import json
import time
import socket
from datetime import datetime
from pathlib import Path

import requests  # pip install requests

# === Central logging config ===
CENTRAL_LOG_SERVER_URL = "http://54.237.154.70/upload"  # <-- change this

# === Common logs across most Linux distros ===
LOG_FILES = [
    "/var/log/syslog",
    "/var/log/messages",
    "/var/log/dmesg",
    "/var/log/auth.log",
    "/var/log/secure",
    "/var/log/ufw.log",
    "/var/log/fail2ban.log",
    "/var/log/cron.log",
    "/var/log/cron",
    "/var/log/boot.log",
    "/var/log/kern.log",
    "/var/log/mysql/error.log",
    "/var/log/postgresql/postgresql.log",
    "/var/log/nginx/error.log",
    "/var/log/apache2/error.log",
    "/var/log/smartd.log",
    "/var/log/dpkg.log",
    "/var/log/apt/history.log",
]

POLL_INTERVAL_SECS = 60  # how often to check logs


def get_hostname() -> str:
    """Return the system hostname, sanitized for use in filenames."""
    try:
        name = socket.gethostname()
        return name.replace(" ", "_").replace(".", "_")
    except Exception:
        return "unknown_host"


def load_offsets(state_file: Path) -> dict:
    """
    Load previously saved offsets if state file exists.
    If not, initialize offsets to EOF for all existing logs,
    so we only capture NEW lines written after this script starts.
    """
    if state_file.exists():
        try:
            with state_file.open("r", encoding="utf-8") as f:
                offsets = json.load(f)
                print("[init] Loaded previous offsets from state file.")
                return offsets
        except Exception as e:
            print(f"[warn] Could not load state file {state_file}: {e}")

    # First run or failed to load: start from end of current files
    print("[init] No valid prior state. Starting from end of existing logs.")
    offsets = {}
    for log_path in LOG_FILES:
        src = Path(log_path)
        if src.exists():
            try:
                size = src.stat().st_size
                offsets[str(src)] = size
            except OSError as e:
                print(f"[warn] Could not stat {log_path}: {e}")
                continue
    print(f"[init] Initialized {len(offsets)} log offsets at EOF.")
    return offsets


def save_offsets(state_file: Path, offsets: dict) -> None:
    try:
        with state_file.open("w", encoding="utf-8") as f:
            json.dump(offsets, f, indent=2, sort_keys=True)
    except Exception as e:
        print(f"[warn] Failed to save state to {state_file}: {e}")


def send_to_central_server(file_path: Path, hostname: str, ts: str) -> None:
    """Upload the snapshot file to the central logging server."""
    try:
        with file_path.open("rb") as fh:
            files = {"file": (file_path.name, fh, "text/plain")}
            data = {"hostname": hostname, "timestamp": ts}
            resp = requests.post(
                CENTRAL_LOG_SERVER_URL,
                data=data,
                files=files,
                timeout=10,
            )
        if resp.ok:
            print(f"[send] Uploaded {file_path} to central server ({resp.status_code}).")
        else:
            print(
                f"[send] Failed to upload {file_path}: "
                f"status={resp.status_code}, body={resp.text[:200]}"
            )
    except Exception as e:
        print(f"[send] Error uploading {file_path} to central server: {e}")


def tail_once(offsets: dict, dest_dir: Path, hostname: str) -> None:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest_file = dest_dir / f"logs_{hostname}_{ts}.log"

    written = False
    with dest_file.open("w", encoding="utf-8", errors="replace") as out:
        for log_path in LOG_FILES:
            src = Path(log_path)
            if not src.exists():
                continue

            key = str(src)
            old_off = offsets.get(key, 0)

            try:
                size = src.stat().st_size
            except OSError as e:
                print(f"[warn] Cannot stat {log_path}: {e}")
                continue

            # Handle rotation/truncate
            if size < old_off:
                print(f"[info] Detected rotation/truncate for {log_path}, resetting offset.")
                old_off = 0

            if size == old_off:
                continue  # no new data

            try:
                with src.open("rb") as f:
                    f.seek(old_off)
                    data = f.read()
            except Exception as e:
                print(f"[warn] Failed to read {log_path} from offset {old_off}: {e}")
                continue

            if not data:
                continue

            # Only write raw log data, no headers
            out.write(data.decode("utf-8", errors="replace"))
            offsets[key] = size
            written = True
            print(f"[ok] Collected {len(data)} bytes from {log_path}")

    if not written:
        dest_file.unlink(missing_ok=True)
        print("[tick] No new entries in any common logs.")
    else:
        print(f"[tick] New data written to {dest_file}")
        # Send to central logging server
        send_to_central_server(dest_file, hostname, ts)


def main():
    script_dir = Path(__file__).resolve().parent
    dest_dir = script_dir / "tailed_logs"
    dest_dir.mkdir(exist_ok=True)
    state_file = script_dir / ".log_offsets.json"

    hostname = get_hostname()
    print(f"[init] Hostname detected: {hostname}")

    offsets = load_offsets(state_file)
    print(f"[init] Watching {len(LOG_FILES)} common logs...")

    while True:
        try:
            tail_once(offsets, dest_dir, hostname)
            save_offsets(state_file, offsets)
            print(f"[loop] Sleeping {POLL_INTERVAL_SECS} seconds...\n")
            time.sleep(POLL_INTERVAL_SECS)
        except KeyboardInterrupt:
            print("Exiting.")
            break


if __name__ == "__main__":
    main()
