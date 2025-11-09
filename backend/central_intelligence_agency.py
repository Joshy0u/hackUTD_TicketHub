#!/usr/bin/env python3
"""
central_logger.py

Flask server that:
- Accepts POST /upload with multipart file + hostname + timestamp
- Saves the incoming file
- Loads the trained model from log_reason_full.pkl
- Scans file line-by-line and classifies each line
- Appends any non-GOOD_LOG lines to non_good_logs.txt
"""

from datetime import datetime
from pathlib import Path
import pickle
import sys

from flask import Flask, request, jsonify

app = Flask(__name__)

BASE_DIR = Path(__file__).resolve().parent
RECEIVED_DIR = BASE_DIR / "received_logs"
RECEIVED_DIR.mkdir(exist_ok=True)

MODEL_PATH = BASE_DIR / "log_reason_full.pkl"
NON_GOOD_FILE = BASE_DIR / "non_good_logs.txt"

# Load model once at startup
print(f"[init] Loading model from {MODEL_PATH}")
try:
    with MODEL_PATH.open("rb") as f:
        model = pickle.load(f)
    print("[init] Model loaded successfully.")
except Exception as e:
    print(f"[error] Failed to load model: {e}", file=sys.stderr)
    model = None


def classify_line(line):
    """Predict label for a single line using the loaded model."""
    if model is None:
        return None
    try:
        return model.predict([line])[0]
    except Exception as e:
        print(f"[warn] Model prediction failed: {e}", file=sys.stderr)
        return None


@app.route("/upload", methods=["POST"])
def upload_logs():
    if "file" not in request.files:
        return jsonify({"error": "missing file field"}), 400

    uploaded_file = request.files["file"]
    if uploaded_file.filename == "":
        return jsonify({"error": "empty filename"}), 400

    hostname = request.form.get("hostname", "unknown_host")
    timestamp = request.form.get(
        "timestamp",
        datetime.utcnow().strftime("%Y%m%d_%H%M%S"),
    )

    safe_hostname = (
        hostname.replace(" ", "_")
        .replace("/", "_")
        .replace("\\", "_")
        .replace("..", "_")
    )
    safe_timestamp = timestamp.replace(" ", "_").replace(":", "").replace("/", "_")

    original_name = Path(uploaded_file.filename).name
    out_name = f"{safe_hostname}_{safe_timestamp}_{original_name}"
    out_path = RECEIVED_DIR / out_name

    # Save the uploaded snapshot
    uploaded_file.save(out_path)
    size = out_path.stat().st_size
    print(f"[recv] {out_name} ({size} bytes) from {hostname}")

    lines_scanned = 0
    non_good_count = 0

    with out_path.open("r", encoding="utf-8", errors="replace") as f_in, \
         NON_GOOD_FILE.open("a", encoding="utf-8", errors="replace") as f_out:

        for line in f_in:
            line = line.strip()
            if not line:
                continue

            lines_scanned += 1
            label = classify_line(line)

            # Anything NOT "GOOD_LOG" goes to non_good_logs.txt
            if not (isinstance(label, str) and label.upper().startswith("GOOD_LOG")):
                f_out.write(f"{timestamp} {hostname} {label}\t{line}\n")
                non_good_count += 1

    return jsonify({
        "received_file": out_name,
        "lines_scanned": lines_scanned,
        "non_good_count": non_good_count
    }), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=False)
