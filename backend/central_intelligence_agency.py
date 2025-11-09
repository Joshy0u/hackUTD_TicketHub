#!/usr/bin/env python3
"""
central_logger.py

Flask server that:
- Accepts POST /upload with multipart file + hostname + timestamp
- Saves the incoming file
- Loads the trained model from log_reason_full.pkl (via joblib)
- Scans file line-by-line and classifies each line using model.predict([line])[0]
- Writes NON-GOOD_LOG lines in non_good_logs.txt
- Prints every analyzed line and its label to the console
- Pushes NON-GOOD_LOG lines into an RDS PostgreSQL table bad_logs
"""

from datetime import datetime
from pathlib import Path
import sys
import os

from flask import Flask, request, jsonify
import joblib
import psycopg2

app = Flask(__name__)

# === Paths ===
BASE_DIR = Path(__file__).resolve().parent
RECEIVED_DIR = BASE_DIR / "received_logs"
RECEIVED_DIR.mkdir(exist_ok=True)

MODEL_PATH = BASE_DIR / "log_reason_full.pkl"
NON_GOOD_FILE = BASE_DIR / "non_good_logs.txt"

# === DB config (env vars override these defaults) ===
DB_HOST = os.environ.get("DB_HOST", "database-1.csfc6cuael0m.us-east-1.rds.amazonaws.com")
DB_PORT = int(os.environ.get("DB_PORT", "5432"))
DB_NAME = os.environ.get("DB_NAME", "postgres")
DB_USER = os.environ.get("DB_USER", "postgres")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "REDACT CREDS")

db_conn = None  # global connection handle


def get_db_connection():
    """Get or create a global PostgreSQL connection."""
    global db_conn

    if db_conn is not None:
        try:
            with db_conn.cursor() as cur:
                cur.execute("SELECT 1;")
            return db_conn
        except Exception:
            try:
                db_conn.close()
            except Exception:
                pass
            db_conn = None

    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            connect_timeout=5,
        )
        conn.autocommit = True
        db_conn = conn
        print("[db] Connected to PostgreSQL")
        return db_conn
    except Exception as e:
        print(f"[db-ERROR] Could not connect to PostgreSQL: {e}", file=sys.stderr)
        return None


def init_db():
    """
    Create bad_logs table and indexes if they don't exist.
    """
    conn = get_db_connection()
    if conn is None:
        print("[db-WARN] Cannot init DB (no connection).", file=sys.stderr)
        return

    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS bad_logs (
                    id          SERIAL PRIMARY KEY,
                    logged_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    upload_ts   TEXT,
                    hostname    TEXT,
                    label       TEXT,
                    log_line    TEXT
                );
                """
            )
            # Indexes to speed up queries by hostname and label
            cur.execute(
                "CREATE INDEX IF NOT EXISTS idx_badlogs_hostname ON bad_logs (hostname);"
            )
            cur.execute(
                "CREATE INDEX IF NOT EXISTS idx_badlogs_label ON bad_logs (label);"
            )
        print("[db] bad_logs table and indexes are ready.")
    except Exception as e:
        print(f"[db-WARN] Failed to init DB schema: {e}", file=sys.stderr)


def insert_bad_log(upload_ts, hostname, label, log_line):
    """Insert a single bad log line into the bad_logs table."""
    conn = get_db_connection()
    if conn is None:
        print("[db-WARN] Skipping DB insert (no connection).", file=sys.stderr)
        return

    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO bad_logs (upload_ts, hostname, label, log_line)
                VALUES (%s, %s, %s, %s);
                """,
                (upload_ts, hostname, label, log_line),
            )
    except Exception as e:
        print(f"[db-WARN] Failed to insert bad log: {e}", file=sys.stderr)


# === Load model ===
print(f"[init] Loading model from {MODEL_PATH}")
try:
    model = joblib.load(MODEL_PATH)
    print("[init] Model loaded successfully!")
except Exception as e:
    print(f"[ERROR] Failed to load model from {MODEL_PATH}: {e}", file=sys.stderr)
    model = None


def classify_line(line: str):
    """Predict tag for a single log line."""
    if model is None:
        return None
    try:
        pred = model.predict([line])[0]
        return pred
    except Exception as e:
        print(f"[WARN] Prediction failed for line: {e}", file=sys.stderr)
        return None


@app.route("/upload", methods=["POST"])
def upload_logs():
    if "file" not in request.files:
        return jsonify({"error": "missing file field"}), 400

    uploaded_file = request.files["file"]
    if uploaded_file.filename == "":
        return jsonify({"error": "empty filename"}), 400

    hostname = request.form.get("hostname", "unknown_host")
    timestamp = request.form.get("timestamp", datetime.utcnow().strftime("%Y%m%d_%H%M%S"))

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

    uploaded_file.save(out_path)
    print(f"[recv] {out_name} ({out_path.stat().st_size} bytes) from {hostname}")

    lines_scanned = 0
    non_good_count = 0

    # Process line-by-line
    with out_path.open("r", encoding="utf-8", errors="replace") as f_in, \
         NON_GOOD_FILE.open("a", encoding="utf-8", errors="replace") as f_out:

        for line in f_in:
            line = line.strip()
            if not line:
                continue

            lines_scanned += 1
            label = classify_line(line)
            if label is None:
                continue

            # Print every line analyzed
            print(f"[ANALYZE] {hostname} | {label} | {line}")

            # Skip GOOD logs
            if str(label).upper().startswith("GOOD_LOG"):
                continue

            # Write bad logs to local file
            f_out.write(f"{timestamp} {hostname} {label}\n{line}\n\n")
            non_good_count += 1

            # Insert bad log into RDS
            insert_bad_log(timestamp, hostname, str(label), line)

    print(f"[done] {lines_scanned} lines processed, {non_good_count} non-GOOD logs detected.")
    return jsonify({
        "received_file": out_name,
        "lines_scanned": lines_scanned,
        "non_good_count": non_good_count
    }), 200


if __name__ == "__main__":
    init_db()   # make sure table + indexes exist
    app.run(host="0.0.0.0", port=8000, debug=False)
