#!/usr/bin/env python3
"""
tail_logs.py

- Tail-based log collection from /var/log (and friends).
- Every minute, reads ONLY NEW DATA added to log files since last run.
- New data is appended into a timestamped file inside "tailed_logs".
- File offsets are tracked in ".log_offsets.json" next to this script.
"""

import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict

# Directories to scan for logs
LOG_DIRS = [Path("/var/log")]

# Extra log-like files that might not end with .log
EXTRA_LOG_BASENAMES = {"wtmp", "btmp", "lastlog"}


def discover_log_files() -> Dict[str, Path]:
    """
    Auto-discover log-like files under LOG_DIRS.
    Returns a dict of {logical_name: Path}.
    """
    log_files: Dict[str, Path] = {}

    for base_dir in LOG_DIRS:
        if not base_dir.exists():
            continue

        for path in base_dir.rglob("*"):
            if not path.is_file():
                continue

            name = path.name

            is_logish = (
                name.endswith(".log")
                or ".log." in name            # e.g., syslog.1, syslog.2.gz
                or name in EXTRA_LOG_BASENAMES
            )

            if not is_logish:
                continue

            try:
                rel = path.relative_to(base_dir)
                logical_name = f"{base_dir.name}__{str(rel).replace(os.sep, '_')}"
            except ValueError:
                logical_name = name

            log_files[logical_name] = path

    return log_files


def load_offsets(state_file: Path) -> Dict[str, int]:
    """
    Load previous file offsets from JSON. Returns dict {str(path): offset}.
    """
    if not state_file.exists():
        return {}

    try:
        with state_file.open("r", encoding="utf-8") as f:
            data = json.load(f)
        # Ensure keys are strings and values are ints
        return {str(k): int(v) for k, v in data.items()}
    except Exception as e:
        print(f"[state] Failed to load offsets: {e}")
        return {}


def save_offsets(state_file: Path, offsets: Dict[str, int]) -> None:
    """
    Save current offsets to JSON.
    """
    try:
        with state_file.open("w", encoding="utf-8") as f:
            json.dump(offsets, f, indent=2, sort_keys=True)
    except Exception as e:
        print(f"[state] Failed to save offsets: {e}")


def tail_once(
    log_files: Dict[str, Path],
    offsets: Dict[str, int],
    dest_dir: Path,
) -> None:
    """
    Perform one 'tick':
    - read new data from each log file (if any)
    - write to a single timestamped file in dest_dir
    - update offsets in-place
    """
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest_file = dest_dir / f"logs_{ts}.log"

    any_data_written = False

    with dest_file.open("w", encoding="utf-8", errors="replace") as out:
        for logical_name, path in log_files.items():
            if not path.exists():
                # File disappeared or doesn't exist; skip it
                continue

            key = str(path.resolve())
            prev_offset = offsets.get(key, 0)

            try:
                size = path.stat().st_size
            except OSError as e:
                print(f"[skip] {logical_name}: stat failed ({e})")
                continue

            # If file shrank, assume rotation/truncation -> start from 0
            if prev_offset > size:
                print(f"[rot]  {logical_name}: file shrank (rotation?), resetting offset")
                prev_offset = 0

            if prev_offset == size:
                # No new data
                continue

            # Read from prev_offset to EOF
            try:
                with path.open("rb") as f:
                    f.seek(prev_offset)
                    new_data = f.read()
            except OSError as e:
                print(f"[err]  {logical_name}: failed to read new data ({e})")
                continue

            if not new_data:
                # Nothing to write
                offsets[key] = size
                continue

            # Write a header then the new content (decoded as UTF-8 with replacement)
            header = f"\n===== {logical_name} ({path}) @ {ts} =====\n"
            out.write(header)
            try:
                out.write(new_data.decode("utf-8", errors="replace"))
            except Exception as e:
                out.write(f"[decode-error] Could not decode bytes: {e}\n")

            offsets[key] = size
            any_data_written = True
            print(f"[ok]   {logical_name}: wrote new data from offset {prev_offset} to {size}")

    if not any_data_written:
        # No new data at all; remove the empty file
        try:
            dest_file.unlink()
            print("[tick] No new log data; deleted empty snapshot file.")
        except FileNotFoundError:
            pass
    else:
        print(f"[tick] New log data written to {dest_file}")


def main():
    script_dir = Path(__file__).resolve().parent
    dest_dir = script_dir / "tailed_logs"
    dest_dir.mkdir(exist_ok=True)

    state_file = script_dir / ".log_offsets.json"

    print(f"[init] Tailed logs directory: {dest_dir}")
    print(f"[init] State file: {state_file}")

    # Initial discovery and state load
    log_files = discover_log_files()
    print(f"[init] Discovered {len(log_files)} log file(s) under /var/log")
    offsets = load_offsets(state_file)

    # Main loop: run forever, every minute
    while True:
        try:
            print("\n[loop] Starting tail tick...")
            tail_once(log_files, offsets, dest_dir)
            save_offsets(state_file, offsets)
            print("[loop] Sleeping 60 seconds...\n")
            time.sleep(60)
        except KeyboardInterrupt:
            print("\n[exit] KeyboardInterrupt received, exiting gracefully.")
            break
        except Exception as e:
            print(f"[loop] Unexpected error in main loop: {e}")
            # You can decide whether to break or continue
            time.sleep(60)


if __name__ == "__main__":
    main()
