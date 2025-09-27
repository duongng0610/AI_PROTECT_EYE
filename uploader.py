#!/usr/bin/env python3
"""
uploader.py - env-aware uploader for session summary

Usage:
    python uploader.py <log_csv_path> [user_id]

Reads summary via client_utils.summarize_log_for_upload and POSTs to server.
Takes SERVER_URL and SERVER_API_KEY from environment (or defaults).
"""
import os
import time
import json
import requests

from client_utils import summarize_log_for_upload

SERVER_URL = os.environ.get("SERVER_URL", "http://127.0.0.1:5000/upload_metrics")
API_KEY = os.environ.get("SERVER_API_KEY", "").strip()

def upload_summary(log_csv_path, user_id=None, device_info=None, retries=2, backoff=1.0):
    summary = summarize_log_for_upload(log_csv_path)
    if summary is None:
        print("No data to upload.")
        return False

    payload = {
        "user_hash": user_id or "anonymous",
        "device": device_info or {},
        "summary": summary
    }
    headers = {"Content-Type": "application/json"}
    if API_KEY:
        headers["X-API-KEY"] = API_KEY

    attempt = 0
    while attempt <= retries:
        try:
            r = requests.post(SERVER_URL, json=payload, headers=headers, timeout=10)
            r.raise_for_status()
            print("Upload OK:", r.status_code, r.text)
            return True
        except requests.exceptions.RequestException as e:
            print(f"Upload attempt {attempt+1} failed:", e)
            attempt += 1
            time.sleep(backoff * attempt)

    print("Upload failed after retries.")
    return False

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python uploader.py <log_csv_path> [user_id]")
    else:
        upload_summary(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
