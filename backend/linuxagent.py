#!/usr/bin/env python3
"""
tail_common_logs.py

Tails only the most common Linux log files (not recursive).
Reads new lines every minute and writes them to timestamped snapshots.
"""

import os
import json
import time
from datetime import datetime
from pathlib import Path

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

def load_offsets(state_file: Path):
    if not state_file.exists():
        return {}
    try:
        with state_file.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save_offsets(state_file: Path, offsets: dict):
    with state_file.open("w", encoding="utf-8") as f:
        json.dump(offsets, f, indent=2, sort_keys=True)

def tail_once(offsets, dest_dir):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest_file = dest_dir / f"logs_{ts}.log"

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
            except OSError:
                continue

            # Handle rotation/truncate
            if size < old_off:
                old_off = 0

            if size == old_off:
                continue  # no new data

            try:
                with src.open("rb") as f:
                    f.seek(old_off)
                    data = f.read()
            except Exception:
                continue

            if not data:
                continue

            out.write(f"\n===== {log_path} @ {ts} =====\n")
            out.write(data.decode("utf-8", errors="replace"))
            offsets[key] = size
            written = True
            print(f"[ok] Collected new entries from {log_path}")

    if not written:
        dest_file.unlink(missing_ok=True)
        print("[tick] No new entries in any common logs.")
    else:
        print(f"[tick] New data written to {dest_file}")

def main():
    script_dir = Path(__file__).resolve().parent
    dest_dir = script_dir / "tailed_logs"
    dest_dir.mkdir(exist_ok=True)
    state_file = script_dir / ".log_offsets.json"

    offsets = load_offsets(state_file)
    print(f"[init] Watching {len(LOG_FILES)} common logs...")

    while True:
        try:
            tail_once(offsets, dest_dir)
            save_offsets(state_file, offsets)
            print("[loop] Sleeping 60 seconds...\n")
            time.sleep(60)
        except KeyboardInterrupt:
            print("Exiting.")
            break

if __name__ == "__main__":
    main()
