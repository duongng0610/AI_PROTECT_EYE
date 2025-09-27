# analyze_metrics.py
import pandas as pd
import matplotlib.pyplot as plt

# Đọc file CSV
df = pd.read_csv("server_data/metrics.csv", parse_dates=["received_at_utc", "session_started", "session_ended"])

print("📊 Tổng số phiên ghi nhận:", len(df))
print("👤 Số người dùng khác nhau:", df['user_hash'].nunique())
print("\n--- Một vài dòng dữ liệu ---")
print(df.head())

# 📈 Phân tích tổng quan blink
print("\n📈 Trung bình số blink mỗi phiên:", df['total_blinks'].mean())
print("📉 Trung bình thời lượng mỗi phiên (phút):", df['duration_seconds'].mean() / 60)
print("😴 Trung bình PERCLOS:", df['avg_perclos'].mean())

# Vẽ biểu đồ tổng số blink theo thời gian
df = df.sort_values("session_started")

plt.figure(figsize=(10,5))
plt.plot(df['session_started'], df['total_blinks'], marker='o')
plt.title("📈 Tổng số blink theo thời gian")
plt.xlabel("Thời điểm bắt đầu phiên")
plt.ylabel("Tổng số blink")
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()

# Vẽ phân bố chỉ số mệt mỏi (PERCLOS)
plt.figure(figsize=(8,4))
plt.hist(df['avg_perclos'], bins=10, color='orange', edgecolor='black')
plt.title("😴 Phân bố chỉ số mệt mỏi (PERCLOS)")
plt.xlabel("PERCLOS")
plt.ylabel("Số phiên")
plt.tight_layout()
plt.show()
