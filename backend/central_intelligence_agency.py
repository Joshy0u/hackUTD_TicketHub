#!/usr/bin/env python3
"""
central_logger.py

A simple central logging server using Flask.

- Endpoint: POST /upload
- Expects multipart/form-data with:
    - file: the log file
    - hostname: the sender's hostname
    - timestamp: client-side timestamp (YYYYMMDD_HHMMSS)
- Saves files under ./received_logs/
"""

from datetime import datetime
from pathlib import Path

from flask import Flask, request, jsonify

app = Flask(__name__)

BASE_DIR = Path(__file__).resolve().parent
RECEIVED_DIR = BASE_DIR / "received_logs"
RECEIVED_DIR.mkdir(exist_ok=True)


@app.route("/upload", methods=["POST"])
def upload_logs():
    # Check file part
    if "file" not in request.files:
        return jsonify({"error": "missing file field"}), 400

    uploaded_file = request.files["file"]
    if uploaded_file.filename == "":
        return jsonify({"error": "empty filename"}), 400

    # Metadata from client
    hostname = request.form.get("hostname", "unknown_host")
    timestamp = request.form.get(
        "timestamp",
        datetime.utcnow().strftime("%Y%m%d_%H%M%S"),
    )

    # Basic sanitization for filesystem
    safe_hostname = (
        hostname.replace(" ", "_")
        .replace("/", "_")
        .replace("\\", "_")
        .replace("..", "_")
    )
    safe_timestamp = (
        timestamp.replace(" ", "_")
        .replace(":", "")
        .replace("/", "_")
    )

    # Original client-side filename (e.g., logs_host_ts.log)
    original_name = Path(uploaded_file.filename).name
    out_name = f"{safe_hostname}_{safe_timestamp}_{original_name}"
    out_path = RECEIVED_DIR / out_name

    # Save file
    uploaded_file.save(out_path)

    size = out_path.stat().st_size
    print(f"[recv] {out_name} ({size} bytes) from {hostname}")

    return jsonify({"status": "ok", "saved_as": out_name}), 200


if __name__ == "__main__":
    # Listen on all interfaces, port 8000
    # debug=False so it’s not too noisy
    app.run(host="0.0.0.0", port=8000, debug=False)
