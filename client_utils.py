# client_utils.py
import os, uuid, yaml, json, csv
from datetime import datetime

ROOT = os.path.abspath(os.path.dirname(__file__))
CONFIGS_DIR = os.path.join(ROOT, "configs")
LOGS_DIR = os.path.join(ROOT, "logs")
os.makedirs(CONFIGS_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)

def make_user_id():
    return str(uuid.uuid4())[:8]

def save_user_config(user_id, cfg):
    path = os.path.join(CONFIGS_DIR, f"config_user_{user_id}.yaml")
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(cfg, f, sort_keys=False, allow_unicode=True)
    return path

def user_config_path(user_id):
    return os.path.join(CONFIGS_DIR, f"config_user_{user_id}.yaml")

def make_session_log_filename(user_id):
    ts = datetime.now().strftime("%Y%m%dT%H%M%S")
    fname = f"logs_{user_id}_{ts}.csv"
    return os.path.join(LOGS_DIR, fname)

def summarize_log_for_upload(log_csv_path):
    import pandas as pd
    df = pd.read_csv(log_csv_path, parse_dates=["timestamp"])
    df = df.sort_values("timestamp").reset_index(drop=True)
    if df.empty:
        return None
    duration = (df["timestamp"].iloc[-1] - df["timestamp"].iloc[0]).total_seconds()
    total_blinks = int(df["total_blinks"].max())
    avg_ear = float(df["ear"].mean())
    avg_perclos = float(df["perclos"].mean())
    return {
        "session_started": df["timestamp"].iloc[0].isoformat(),
        "session_ended": df["timestamp"].iloc[-1].isoformat(),
        "duration_seconds": duration,
        "total_blinks": total_blinks,
        "avg_ear": round(avg_ear, 4),
        "avg_perclos": round(avg_perclos, 4)
    }
