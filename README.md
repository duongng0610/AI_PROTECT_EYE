# 👁️ Blink Detection & Eye Fatigue Monitoring System

Hệ thống theo dõi nhấp nháy mắt và phát hiện mệt mỏi real-time sử dụng Computer Vision và MediaPipe.

## ✨ Tính năng chính

- 🎯 **Theo dõi nhấp nháy mắt** real-time bằng MediaPipe Face Mesh
- 📊 **Tính toán PERCLOS** (Percentage of Eyelid Closure) - chỉ số mệt mỏi
- ⚠️ **Cảnh báo mệt mỏi** thông minh khi PERCLOS cao hoặc tần suất blink thấp
- 🔧 **Calibration tự động** để tối ưu threshold cho từng người dùng
- 📝 **Ghi log session** với CSV format
- ☁️ **Upload data lên server** (tùy chọn)
- 📈 **Phân tích dữ liệu** offline với charts và statistics

## 📁 Cấu trúc Project

### 🔥 Files Chính (Core)
- `blink_mvp.py` — **Ứng dụng chính**: theo dõi mắt, phát hiện blink, cảnh báo mệt mỏi. (⭐⭐⭐⭐⭐)
- `calibrate_save.py` — **Calibration tool**: tối ưu EAR threshold cho user. (⭐⭐⭐⭐)
- `requirements.txt` — **Dependencies** Python cần thiết. (⭐⭐⭐⭐⭐)

### 🛠️ Files Hỗ trợ (Utilities)
- `client_utils.py` — Helper functions: tạo user ID, quản lý config, summarize logs. (⭐⭐⭐)
- `uploader.py` — Upload session data lên Flask server. (⭐⭐⭐)
- `analyze_logs.py` — Phân tích logs offline: statistics, charts với matplotlib. (⭐⭐)

### 🤖 Files Model & Config
- `haarcascade_frontalface_default.xml` — OpenCV face detection model (backup cho MediaPipe). (⭐⭐⭐)
- `config.yaml` — **Cấu hình hệ thống** (camera, thresholds, server settings). (⭐⭐⭐⭐)
- `configs/` — Thư mục chứa user-specific configs. (⭐⭐)

### 🌐 Server Component
- `server/server_app.py` — **Flask server** nhận data từ clients. (⭐⭐⭐)
- `server/analyze_metrics.py` — Phân tích tổng hợp data từ nhiều users. (⭐⭐)
- `server/log_config.py` — Logging configuration cho server. (⭐⭐)
- `server/server_data/` — Database (CSV) lưu metrics từ clients. (⭐⭐⭐)

### 📊 Data & Logs
- `logs/` — Session logs của các lần chạy ứng dụng. (⭐⭐)
- `share_opt_in.txt` — File opt-in cho việc share data. (⭐)
- `.gitignore` — Git ignore rules. (⭐⭐)

## 🔧 Yêu cầu hệ thống

### **Phần cứng**
- 🎥 **Webcam** (camera tích hợp hoặc external)
- 💻 **CPU**: Tối thiểu Intel i3 hoặc tương đương
- 🧠 **RAM**: Tối thiểu 4GB (khuyến nghị 8GB+)
- 💾 **Storage**: ~500MB cho dependencies

### **Phần mềm**
- 🐍 **Python 3.8+** (khuyến nghị Python 3.10+)
- 🖥️ **OS**: Windows 10+, macOS 10.15+, Linux Ubuntu 18.04+
- 📷 **Camera drivers** tương thích với OpenCV

### **Thư viện Python (Dependencies)**
```
mediapipe>=0.10.0     # Face mesh detection
opencv-python         # Computer vision
numpy                 # Numerical computations
pandas                # Data analysis
pyyaml                # Config file handling
flask                 # Web server
requests              # HTTP client
python-dotenv         # Environment variables
matplotlib            # Data visualization
streamlit             # Web UI (optional)
```

## 🚀 Hướng dẫn cài đặt và chạy

### **Bước 1: Chuẩn bị môi trường**

```bash
# Clone hoặc download project về máy
cd your-project-folder

# Tạo virtual environment (khuyến nghị)
python -m venv .venv

# Kích hoạt virtual environment
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# Cài đặt dependencies
pip install -r requirements.txt
```

### **Bước 2: Thiết lập cấu hình (Tùy chọn)**

```bash
# Kiểm tra file config.yaml
# Điều chỉnh camera index, thresholds nếu cần
notepad config.yaml  # Windows
nano config.yaml     # Linux/macOS
```

### **Bước 3: Chạy Calibration (Khuyến nghị - Bước quan trọng!)**

```bash
# Chạy calibration để tối ưu threshold cho mắt của bạn
python calibrate_save.py
```

**Hướng dẫn calibration:**
1. Nhìn thẳng vào camera, giữ mắt MỞ trong 5 giây
2. Nhắm mắt HOÀN TOÀN trong 4 giây  
3. Threshold tối ưu sẽ được tự động lưu vào `config.yaml`

### **Bước 4: Chạy ứng dụng chính**

```bash
# Chạy blink detection system
python blink_mvp.py
```

**Điều khiển trong ứng dụng:**
- `q` hoặc `ESC`: Thoát ứng dụng
- `s`: Chụp screenshot
- `Ctrl+C`: Dừng session khẩn cấp

### **Bước 5: Phân tích dữ liệu (Tùy chọn)**

```bash
# Phân tích log file gần nhất
python analyze_logs.py logs/your_log_file.csv

# Hoặc để script tự tìm file log mới nhất
python analyze_logs.py
```

## 🌐 Server Component (Tùy chọn - Dành cho multi-user)

**Lưu ý**: Server component là **TÙY CHỌN** - bạn hoàn toàn có thể sử dụng project mà không cần server!

### **Khi nào cần Server?**
- 👥 **Multi-user**: Nhiều người sử dụng, muốn tập trung dữ liệu
- 📊 **Team monitoring**: Theo dõi sức khỏe mắt của cả team
- 🔬 **Research**: Thu thập dữ liệu để nghiên cứu

### **Khởi động Server (nếu cần)**

```bash
# Điều hướng vào thư mục server
cd server

# Khởi động Flask server
python server_app.py
```

### **Cấu hình Client để upload (nếu cần)**

Chỉnh sửa `config.yaml`:
```yaml
server:
  enabled: true
  url: "http://127.0.0.1:5000/upload_metrics"

user:
  opt_in_upload: true  # bật upload
```

## 📊 Hiểu về các chỉ số

### **EAR (Eye Aspect Ratio)**
- Tỷ lệ chiều cao/chiều rộng của mắt
- Giá trị thấp = mắt nhắm
- Threshold điển hình: ~0.22 (tùy thuộc vào từng người)

### **PERCLOS (Percentage of Eyelid Closure)**
- Tỷ lệ phần trăm thời gian mắt nhắm trong 1 phút
- > 25%: Dấu hiệu mệt mỏi
- > 40%: Mệt mỏi nghiêm trọng

### **Blink Rate**
- Tần suất nhấp nháy (lần/phút)
- Bình thường: 12-20 lần/phút
- < 6 lần/phút: Có thể mệt mỏi hoặc tập trung quá mức

## ⚠️ Xử lý sự cố

### **Lỗi camera không detect được**
```bash
# Kiểm tra camera index
python -c "import cv2; cap = cv2.VideoCapture(0); print('Camera OK' if cap.isOpened() else 'Camera Failed'); cap.release()"

# Thử thay đổi camera index trong config.yaml
camera:
  index: 1  # hoặc 2, 3...
```

### **Lỗi MediaPipe không hoạt động**
```bash
# Reinstall MediaPipe
pip uninstall mediapipe
pip install mediapipe --upgrade
```

### **Performance không tốt**
- Giảm resolution camera trong `config.yaml`
- Tăng `min_detection_confidence` và `min_tracking_confidence`
- Đóng các ứng dụng khác đang sử dụng camera

### **Accuracy không cao**
- **BẮT BUỘC chạy calibration**: `python calibrate_save.py`
- Đảm bảo ánh sáng đủ và ổn định
- Ngồi cách camera 50-80cm
- Face nhìn thẳng camera

## 🎯 Workflow hoàn chỉnh

```bash
# 1. Cài đặt
pip install -r requirements.txt

# 2. Calibration (QUAN TRỌNG!)
python calibrate_save.py

# 3. Chạy ứng dụng chính
python blink_mvp.py

# 4. Phân tích kết quả (sau khi chạy xong)
python analyze_logs.py

# 5. Khởi động server (nếu cần)
cd server && python server_app.py
```

## 📝 Notes

- ✅ **Luôn chạy calibration trước** để có kết quả tốt nhất
- ✅ **Đảm bảo ánh sáng tốt** khi sử dụng
- ✅ **Session logs** được lưu tự động trong thư mục `logs/`
- ✅ **Config file** có thể chỉnh sửa để tùy chỉnh thresholds
- ⚠️ **Camera permission** cần được cấp cho Python

---

## 🆘 Support

Nếu gặp vấn đề, hãy:
1. Kiểm tra lại requirements và dependencies
2. Chạy calibration lại
3. Kiểm tra camera và ánh sáng
4. Xem log files để debug

**Happy Blinking! 👁️‍🗨️**
