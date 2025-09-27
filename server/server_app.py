import os
import csv
import datetime
import json
import logging
from logging.handlers import RotatingFileHandler

from flask import Flask, request, jsonify
from dotenv import load_dotenv

# --- Load env ---
basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, ".env"))

# --- Configuration ---
DATA_DIR = os.path.join(basedir, "server_data")
LOG_DIR = os.path.join(basedir, "logs")
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

OUT_CSV = os.path.join(DATA_DIR, "metrics.csv")
SERVER_API_KEY = os.environ.get("SERVER_API_KEY", "").strip()  # if empty -> no auth

# CSV header (ensure matches payload fields you want to store)
CSV_HEADER = [
    "received_at_utc",
    "user_hash",
    "session_started",
    "session_ended",
    "duration_seconds",
    "total_blinks",
    "avg_ear",
    "avg_perclos",
    "device_json",
    "raw_payload"
]

# --- Logging setup ---
LOG_FILE = os.path.join(LOG_DIR, "server.log")
logger = logging.getLogger("blink_server")
logger.setLevel(logging.INFO)

# Rotating file handler
fh = RotatingFileHandler(LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8")
fh.setLevel(logging.INFO)
fmt = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
fh.setFormatter(fmt)
logger.addHandler(fh)

# Console handler
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
ch.setFormatter(fmt)
logger.addHandler(ch)

logger.info("Starting blink metrics server (PID=%s)", os.getpid())

# Ensure CSV has header
if not os.path.exists(OUT_CSV):
    try:
        with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(CSV_HEADER)
        logger.info("Created metrics CSV at %s", OUT_CSV)
    except Exception as e:
        logger.exception("Failed to create CSV file: %s", e)

app = Flask(__name__)


@app.route("/health", methods=["GET"])
def health():
    """Simple health check"""
    return jsonify({"status": "ok", "time": datetime.datetime.utcnow().isoformat()}), 200


def _check_api_key(req):
    """Return (True, None) if OK, else (False, error_response)"""
    if not SERVER_API_KEY:
        return True, None
    key = req.headers.get("X-API-KEY", "")
    if key != SERVER_API_KEY:
        logger.warning("Unauthorized access attempt from %s", request.remote_addr)
        return False, (jsonify({"error": "unauthorized"}), 401)
    return True, None


def _safe_get_summary(payload):
    """
    Accept either:
      - payload is a dict containing "summary" key (the client sends {user_hash, device, summary})
      - or payload itself is the summary dict (flat)
    Returns the tuple (user_hash, device, summary_dict)
    """
    if not isinstance(payload, dict):
        return None, None, None

    user_hash = payload.get("user_hash", "anonymous")
    device = payload.get("device", {})

    if "summary" in payload and isinstance(payload["summary"], dict):
        summary = payload["summary"]
    else:
        # assume payload *is* the summary (flat)
        # user_hash/device may be missing in this case
        summary = payload

    return user_hash, device, summary


@app.route("/upload_metrics", methods=["POST"])
def upload_metrics():
    # API key check
    ok, err = _check_api_key(request)
    if not ok:
        return err

    # Parse JSON
    try:
        data = request.get_json(force=True)
    except Exception as e:
        logger.warning("Invalid JSON from %s: %s", request.remote_addr, e)
        return jsonify({"error": "invalid_json"}), 400

    if not data:
        logger.warning("Empty payload from %s", request.remote_addr)
        return jsonify({"error": "empty_payload"}), 400

    user_hash, device, summary = _safe_get_summary(data)
    if summary is None:
        logger.warning("Malformed payload (no summary) from %s: %s", request.remote_addr, str(data)[:200])
        return jsonify({"error": "invalid_payload"}), 400

    # Minimal validation - require session_started or duration_seconds (adjust as needed)
    if "session_started" not in summary and "duration_seconds" not in summary:
        logger.warning("Missing required summary fields from %s: %s", request.remote_addr, str(summary)[:200])
        return jsonify({"error": "missing_summary_fields"}), 400

    # Prepare row values with safe defaults
    row = [
        datetime.datetime.utcnow().isoformat(),
        user_hash,
        summary.get("session_started", ""),
        summary.get("session_ended", ""),
        summary.get("duration_seconds", ""),
        summary.get("total_blinks", ""),
        summary.get("avg_ear", ""),
        summary.get("avg_perclos", ""),
        json.dumps(device, ensure_ascii=False),
        json.dumps(data, ensure_ascii=False),
    ]

    # Write to CSV
    try:
        with open(OUT_CSV, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(row)
        logger.info("Saved metrics for user=%s (session_started=%s)", user_hash, summary.get("session_started", ""))
    except Exception as e:
        logger.exception("Failed to write metrics to CSV: %s", e)
        return jsonify({"error": "write_failed", "msg": str(e)}), 500

    return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
    # Development launcher. For production use gunicorn/waitress.
    host = "0.0.0.0"
    port = int(os.environ.get("PORT", "5000"))
    debug_mode = os.environ.get("FLASK_DEBUG", "0") == "1"
    logger.info("Launching Flask app on %s:%s (debug=%s)", host, port, debug_mode)
    app.run(host=host, port=port, debug=debug_mode)