#!/usr/bin/env python3
"""
collect_logs.py

- Checks for a set of common Linux log files.
- If a log file exists on this system, copies it into a "collected_logs"
  directory that lives in the same directory as this script.
- Each run creates timestamped copies so you can keep snapshots over time.
"""

import os
import shutil
from datetime import datetime
from pathlib import Path

# =========================
# Log files to collect
# =========================
LOG_FILES = {
    # --- Core system logs ---
    "syslog": "/var/log/syslog",             # Ubuntu/Debian general system log
    "messages": "/var/log/messages",         # RHEL/CentOS general system log
    "dmesg": "/var/log/dmesg",               # Kernel/hardware events
    "auth": "/var/log/auth.log",             # SSH logins, sudo attempts, auth failures
    "secure": "/var/log/secure",             # RHEL/CentOS security log (SSH, sudo)
    "cron": "/var/log/cron.log",             # Debian/Ubuntu cron log (if present)
    "cron_alt": "/var/log/cron",             # RHEL/CentOS cron log
    "boot": "/var/log/boot.log",             # Boot-time service issues

    # --- Data & application logs (examples, adjust for your setup) ---
    "etl": "/var/log/etl.log",               # Your ETL / data pipeline jobs
    "db_backup": "/var/log/db_backup.log",   # Database or file backup jobs
    "app_main": "/opt/myapp/logs/app.log",   # Custom application logs (change path)

    # --- Database logs ---
    "mysql": "/var/log/mysql/error.log",                     # MySQL / MariaDB errors
    "postgresql": "/var/log/postgresql/postgresql.log",      # PostgreSQL server logs

    # --- Security & network logs ---
    "ufw": "/var/log/ufw.log",               # Ubuntu UFW firewall events
    "firewalld": "/var/log/firewalld",       # firewalld log (varies by distro)
    "fail2ban": "/var/log/fail2ban.log",     # Banned IPs / brute-force protection

    # --- Storage & hardware ---
    "smartd": "/var/log/smartd.log",         # Disk SMART health monitoring
    "disk_monitor": "/var/log/disk_monitor.log",  # Custom disk-space monitor scripts
}

def main():
    # Directory where this script lives
    script_dir = Path(__file__).resolve().parent

    # Directory where we’ll drop collected log snapshots
    dest_dir = script_dir / "collected_logs"
    dest_dir.mkdir(exist_ok=True)

    # Timestamp to append to copied filenames
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    print(f"[collector] Saving logs into: {dest_dir}")
    print(f"[collector] Timestamp: {ts}")

    for log_name, log_path in LOG_FILES.items():
        src = Path(log_path)

        if not src.exists():
            print(f"[skip] {log_name}: {src} (does not exist on this system)")
            continue

        # Choose an extension: keep original suffix if present, else ".log"
        suffix = src.suffix if src.suffix else ".log"
        dest_filename = f"{log_name}_{ts}{suffix}"
        dest = dest_dir / dest_filename

        try:
            shutil.copy2(src, dest)
            print(f"[ok]   {log_name}: copied {src} -> {dest}")
        except PermissionError as e:
            print(f"[err]  {log_name}: permission denied reading {src}: {e}")
        except Exception as e:
            print(f"[err]  {log_name}: failed to copy {src}: {e}")

    print("[collector] Done.")


if __name__ == "__main__":
    main()
