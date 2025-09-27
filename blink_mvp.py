import os
import sys
import time
import csv
import math
import json
import collections
import datetime
import platform
import subprocess

import yaml
import cv2
import numpy as np
import mediapipe as mp

# try import uploader (optional)
try:
    from uploader import upload_summary
except Exception:
    upload_summary = None

ROOT = os.path.abspath(os.path.dirname(__file__))
CONFIG_PATH = os.path.join(ROOT, "config.yaml")
LOGS_DIR = os.path.join(ROOT, "logs")
os.makedirs(LOGS_DIR, exist_ok=True)

DEFAULT_CONFIG = {
    "camera": {"index": 0, "width": 640, "height": 480, "fps": 30},
    "metrics": {"ear_threshold": 0.22, "consec_frames": 3, "perclos_window_seconds": 60},
    "alert": {"perclos_warn_threshold": 0.25, "blink_rate_warn_bpm": 6.0},
    "user": {"user_hash": "anonymous", "opt_in_upload": False},
    "server": {
        "enabled": False,
        "url": "http://127.0.0.1:5000/upload_metrics",
        "use_api_key": False,
        "api_key_env_var": "SERVER_API_KEY"
    }
}

# ------------------------- CONFIG -------------------------
def load_config(path=CONFIG_PATH):
    cfg = {}
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                cfg = yaml.safe_load(f) or {}
        except Exception as e:
            print("Warning: failed to read config.yaml:", e)
            cfg = {}

    merged = DEFAULT_CONFIG.copy()
    for k, v in (cfg or {}).items():
        if isinstance(v, dict) and k in merged and isinstance(merged[k], dict):
            merged[k].update(v)
        else:
            merged[k] = v

    # backward compat
    if cfg.get("consec_frames") is not None and merged.get("metrics", {}).get("consec_frames") is None:
        try:
            merged["metrics"]["consec_frames"] = int(cfg.get("consec_frames"))
        except Exception:
            pass
    ed = cfg.get("eye_detection", {})
    if isinstance(ed, dict):
        if merged["metrics"].get("ear_threshold") is None:
            if ed.get("ear_threshold") is not None:
                merged["metrics"]["ear_threshold"] = float(ed.get("ear_threshold"))
            elif ed.get("blink_threshold") is not None:
                merged["metrics"]["ear_threshold"] = float(ed.get("blink_threshold"))
    return merged

# ------------------------- EAR UTILS -------------------------
LEFT_EYE_IDX = [33, 160, 158, 133, 153, 144]
RIGHT_EYE_IDX = [263, 387, 385, 362, 380, 373]
mp_face = mp.solutions.face_mesh

def landmarks_to_points(landmarks, idxs, w, h):
    return [(int(landmarks[i].x * w), int(landmarks[i].y * h)) for i in idxs]

def euclidean(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])

def compute_ear(eye_pts):
    if not eye_pts or len(eye_pts) != 6:
        return None
    p1, p2, p3, p4, p5, p6 = eye_pts
    C = euclidean(p1, p4)
    if C == 0: return None
    return (euclidean(p2, p6) + euclidean(p3, p5)) / (2.0 * C)

# ------------------------- LOGGING -------------------------
def make_log_writer(user_hash):
    ts = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    fname = f"logs_{user_hash}_{ts}.csv"
    path = os.path.join(LOGS_DIR, fname)
    f = open(path, "w", newline="", encoding="utf-8")
    writer = csv.writer(f)
    writer.writerow(["timestamp_utc", "frame_idx", "ear", "is_eye_closed", "perclos", "blink_count"])
    return f, writer, path

# robust read for opt-in file
def read_opt_in_file(path):
    try:
        with open(path, "r", encoding="utf-8-sig") as f:
            return f.read().strip()
    except UnicodeDecodeError:
        try:
            b = open(path, "rb").read()
            return b.decode("utf-8", errors="ignore").strip()
        except Exception:
            return ""
    except FileNotFoundError:
        return ""

# ------------------------- MAIN -------------------------
def main():
    cfg = load_config()
    cam_idx = cfg["camera"]["index"]
    cam_w = cfg["camera"]["width"]
    cam_h = cfg["camera"]["height"]

    EAR_THRESHOLD = float(cfg["metrics"]["ear_threshold"])
    CONSEC_FRAMES = int(cfg["metrics"]["consec_frames"])
    PERCLOS_WINDOW = int(cfg["metrics"]["perclos_window_seconds"])

    PERCLOS_WARN = float(cfg["alert"]["perclos_warn_threshold"])
    BLINK_RATE_WARN = float(cfg["alert"]["blink_rate_warn_bpm"])

    user_hash = cfg["user"]["user_hash"]
    config_opt_in = bool(cfg["user"]["opt_in_upload"])

    print(f"📸 Starting Blink MVP | EAR={EAR_THRESHOLD:.4f} consec={CONSEC_FRAMES} perclos_win={PERCLOS_WINDOW}s")

    # ✅ Nếu đang dùng ngưỡng EAR mặc định, gợi ý người dùng calibrate
    is_default_thresh = abs(EAR_THRESHOLD - DEFAULT_CONFIG["metrics"]["ear_threshold"]) < 1e-6
    if is_default_thresh:
        print("\n⚠️  EAR threshold đang dùng là mặc định. Bạn nên chạy calibrate_save.py để tăng độ chính xác.")
        try:
            ans = input("👉 Bạn có muốn chạy calibrate ngay không? (y/N): ").strip().lower()
        except Exception:
            ans = "n"
        if ans == "y":
            script = os.path.join(ROOT, "calibrate_save.py")
            if os.path.exists(script):
                subprocess.call([sys.executable, script])
                cfg = load_config()  # reload config sau calibrate
                EAR_THRESHOLD = float(cfg["metrics"].get("ear_threshold", EAR_THRESHOLD))
                print(f"✅ EAR threshold mới đã tải: {EAR_THRESHOLD:.4f}")
            else:
                print("❌ Không tìm thấy calibrate_save.py – vui lòng chạy thủ công.")


    # open camera
    cap = cv2.VideoCapture(cam_idx, cv2.CAP_DSHOW if platform.system() == "Windows" else 0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, cam_w)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, cam_h)
    if not cap.isOpened():
        print("❌ Cannot open camera.")
        return

    logfile_fh, csv_writer, log_path = make_log_writer(user_hash)
    session_start = datetime.datetime.utcnow().isoformat()

    face_mesh = mp_face.FaceMesh(
        static_image_mode=False,
        max_num_faces=1,
        refine_landmarks=True,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
    )

    frame_idx = 0
    consec_counter = 0
    blink_count = 0
    frame_history = collections.deque()

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("⚠️ Empty frame.")
                break

            frame_idx += 1
            h, w = frame.shape[:2]
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = face_mesh.process(rgb)

            ear_val = None
            is_closed = False

            if results.multi_face_landmarks:
                lm = results.multi_face_landmarks[0].landmark
                left_pts = landmarks_to_points(lm, LEFT_EYE_IDX, w, h)
                right_pts = landmarks_to_points(lm, RIGHT_EYE_IDX, w, h)
                left_ear = compute_ear(left_pts)
                right_ear = compute_ear(right_pts)
                if left_ear is not None and right_ear is not None:
                    ear_val = (left_ear + right_ear) / 2.0
                    cv2.putText(frame, f"EAR:{ear_val:.3f}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,0), 2)
                    for (x, y) in left_pts + right_pts:
                        cv2.circle(frame, (x, y), 1, (0, 255, 255), -1)
            else:
                cv2.putText(frame, "No face detected", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

            if ear_val is not None:
                if ear_val < EAR_THRESHOLD:
                    consec_counter += 1
                else:
                    if consec_counter >= CONSEC_FRAMES:
                        blink_count += 1
                    consec_counter = 0
                is_closed = ear_val < EAR_THRESHOLD
            else:
                consec_counter = 0

            now = time.time()
            frame_history.append((now, 1 if is_closed else 0))
            while frame_history and (now - frame_history[0][0]) > PERCLOS_WINDOW:
                frame_history.popleft()
            perclos = (sum(x[1] for x in frame_history) / len(frame_history)) if frame_history else 0.0

            cv2.putText(frame, f"PERCLOS:{perclos:.3f}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 200, 0), 2)
            cv2.putText(frame, f"Blinks:{blink_count}", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (200, 200, 200), 2)

            alert_text = ""
            if perclos >= PERCLOS_WARN:
                alert_text = "🚨 TAKE A BREAK - PERCLOS high"
            else:
                elapsed_min = max(1e-6, (now - frame_history[0][0]) / 60.0 if frame_history else 0)
                blink_rate_bpm = blink_count / elapsed_min if elapsed_min > 0 else 0.0
                if blink_rate_bpm < BLINK_RATE_WARN:
                    alert_text = "⚠️ LOW BLINK RATE"
            if alert_text:
                cv2.putText(frame, alert_text, (10, frame.shape[0] - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

            csv_writer.writerow([
                datetime.datetime.utcnow().isoformat(),
                frame_idx,
                f"{ear_val:.4f}" if ear_val is not None else "",
                int(is_closed),
                f"{perclos:.4f}",
                blink_count
            ])

            cv2.imshow("Blink MVP", frame)
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q') or key == 27:
                print("🔚 Quit pressed - stopping session...")
                break
            if key == ord('s'):
                snap = f"snapshot_{user_hash}_{datetime.datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}.png"
                cv2.imwrite(os.path.join(LOGS_DIR, snap), frame)
                print("📸 Saved snapshot:", snap)

    except KeyboardInterrupt:
        print("⏹ Interrupted by user (CTRL+C)")
    finally:
        cap.release()
        cv2.destroyAllWindows()
        logfile_fh.close()

    # === SUMMARY ===
    session_end = datetime.datetime.utcnow().isoformat()
    duration_seconds = int(time.time() - (frame_history[0][0] if frame_history else time.time()))
    avg_ear, avg_perclos = "", 0.0
    try:
        import pandas as pd
        df = pd.read_csv(log_path)
        if "ear" in df.columns:
            df["ear"] = pd.to_numeric(df["ear"], errors="coerce")
            avg_ear = float(df["ear"].dropna().mean())
        if "perclos" in df.columns:
            avg_perclos = float(df["perclos"].dropna().mean())
    except Exception:
        pass

    summary = {
        "session_started": session_start,
        "session_ended": session_end,
        "duration_seconds": duration_seconds,
        "total_blinks": blink_count,
        "avg_ear": avg_ear,
        "avg_perclos": avg_perclos,
    }
    print("\n📊 Session summary:", json.dumps(summary, indent=2))

    # === UPLOAD ===
    do_upload = config_opt_in
    opt_in_file = os.path.join(ROOT, "share_opt_in.txt")
    if os.path.exists(opt_in_file):
        content = read_opt_in_file(opt_in_file)
        if content == "1":
            do_upload = True

    if do_upload and upload_summary:
        print("☁️ Uploading summary...")
        device_info = {"os": platform.system(), "python": platform.python_version()}
        try:
            ok = upload_summary(log_path, user_id=user_hash, device_info=device_info)
            print("✅ Upload OK" if ok else "❌ Upload failed")
        except Exception as e:
            print("❌ Upload exception:", e)
    else:
        print("📁 Upload skipped (opt-in not set or uploader missing).")

    print("📄 Log saved to:", log_path)
    print("✅ Done.")

if __name__ == "__main__":
    main()
