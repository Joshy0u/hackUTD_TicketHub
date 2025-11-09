#!/usr/bin/env python3
"""
central_logger.py

A simple central logging server that accepts log snapshot uploads
from tail_common_logs.py clients.

- Endpoint: POST /upload
- Expects multipart/form-data with:
    - file: the log file
    - hostname: the sender's hostname
    - timestamp: client-side timestamp (YYYYMMDD_HHMMSS)
- Saves files under ./received_logs/
"""

import os
from datetime import datetime
from pathlib import Path

from flask import Flask, request, jsonify, abort

app = Flask(__name__)

# Directory to store incoming log files
BASE_DIR = Path(__file__).resolve().parent
RECEIVED_DIR = BASE_DIR / "received_logs"
RECEIVED_DIR.mkdir(exist_ok=True)


@app.route("/upload", methods=["POST"])
def upload_logs():
    # Check file
    if "file" not in request.files:
        return jsonify({"error": "missing file field"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "empty filename"}), 400

    # Metadata from client
    hostname = request.form.get("hostname", "unknown_host")
    timestamp = request.form.get("timestamp", "")
    if not timestamp:
        # fallback to server-side time if client didn't send it
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

    # Basic sanitization for filesystem
    safe_hostname = (
        hostname.replace(" ", "_")
        .replace("/", "_")
        .replace("\\", "_")
        .replace("..", "_")
    )
    safe_timestamp = timestamp.replace(" ", "_").replace(":", "").replace("/", "_")

    # Build filename: hostname_timestamp_originalname
    original_name = Path(file.filename).name
    out_name = f"{safe_hostname}_{safe_timestamp}_{original_name}"
    out_path = RECEIVED_DIR / out_name

    # Save file
    file.save(out_path)

    # Log to console for visibility
    size = out_path.stat().st_size
    print(f"[recv] {out_name} ({size} bytes) from {hostname}")

    return jsonify({"status": "ok", "saved_as": out_name}), 200


if __name__ == "__main__":
    # Run on all interfaces, port 8000 by default
    app.run(host="0.0.0.0", port=8000)
