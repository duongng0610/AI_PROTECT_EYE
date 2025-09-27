# calibrate_save.py
import cv2
import mediapipe as mp
import numpy as np
import time
import yaml
import os
from datetime import datetime

CFG_PATH = "config.yaml"

mpfm = mp.solutions.face_mesh.FaceMesh(refine_landmarks=True, min_detection_confidence=0.5, min_tracking_confidence=0.5)

LEFT_EYE_IDX = [33, 160, 158, 133, 153, 144]
RIGHT_EYE_IDX = [362, 385, 387, 263, 373, 380]

def eye_aspect_ratio(landmarks, eye_idx, w, h):
    pts = [(int(landmarks[i].x * w), int(landmarks[i].y * h)) for i in eye_idx]
    p1,p2,p3,p4,p5,p6 = pts[0],pts[1],pts[2],pts[3],pts[4],pts[5]
    A = np.linalg.norm(np.array(p2)-np.array(p6))
    B = np.linalg.norm(np.array(p3)-np.array(p5))
    C = np.linalg.norm(np.array(p1)-np.array(p4))
    return (A + B) / (2.0 * (C + 1e-6))

def collect_ears(cap, duration, prompt):
    print(prompt)
    time.sleep(1)
    start = time.time()
    ears = []
    while time.time() - start < duration:
        ret, frame = cap.read()
        if not ret:
            break
        h,w,_ = frame.shape
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        res = mpfm.process(rgb)
        if res.multi_face_landmarks:
            lm = res.multi_face_landmarks[0].landmark
            left = eye_aspect_ratio(lm, LEFT_EYE_IDX, w, h)
            right = eye_aspect_ratio(lm, RIGHT_EYE_IDX, w, h)
            ears.append((left+right)/2.0)
        cv2.putText(frame, prompt, (10,30), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255,255,255), 2)
        cv2.imshow("Calibrate (press ESC to cancel)", frame)
        if cv2.waitKey(1) & 0xFF == 27:
            break
    return ears

def load_config(path=CFG_PATH):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}

def save_config(cfg, path=CFG_PATH):
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(cfg, f, sort_keys=False, allow_unicode=True)
    print("Updated", path)

def main():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Cannot open camera"); return
    try:
        open_ears = collect_ears(cap, 5, "KEEP EYES OPEN (5s) - look at camera")
        time.sleep(0.5)
        closed_ears = collect_ears(cap, 4, "KEEP EYES CLOSED (4s) - close your eyes")
    finally:
        cap.release()
        cv2.destroyAllWindows()

    if not open_ears or not closed_ears:
        print("Failed to collect ears. Try again (ensure face visible and good lighting).")
        return
    avg_open = float(np.mean(open_ears))
    avg_closed = float(np.mean(closed_ears))
    threshold = float((avg_open + avg_closed) / 2.0)
    print(f"Open mean: {avg_open:.4f}, Closed mean: {avg_closed:.4f}, Threshold: {threshold:.4f}")

    cfg = load_config()
    # ensure structure
    if "eye_detection" not in cfg or not isinstance(cfg["eye_detection"], dict):
        cfg["eye_detection"] = {}
    cfg["eye_detection"]["ear_threshold"] = float(round(threshold, 4))
    # optionally set consec_frames if not present
    if "consec_frames" not in cfg:
        cfg["consec_frames"] = 3
    save_config(cfg)

if __name__ == "__main__":
    main()
