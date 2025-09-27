# analyze_logs.py
import sys
import pandas as pd
import matplotlib.pyplot as plt
from datetime import timedelta

def load_logs(path="logs.csv"):
    df = pd.read_csv(path, parse_dates=["timestamp"])
    df = df.sort_values("timestamp").reset_index(drop=True)
    return df

def blinks_per_minute(df):
    df = df.copy()
    df["minute"] = df["timestamp"].dt.floor("T")
    per_min = df.groupby("minute")["total_blinks"].max().fillna(0)
    blinks = per_min.diff().fillna(per_min.iloc[0]).astype(int)
    blinks.index = blinks.index.astype(str)
    return blinks

def plot_perclos(df, window_seconds=60, out="perclos_plot.png"):
    plt.figure(figsize=(10,3))
    plt.plot(df["timestamp"], df["perclos"], marker=".", linewidth=1)
    plt.title(f"PERCLOS over time (window={window_seconds}s)")
    plt.xlabel("time"); plt.ylabel("perclos")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(out)
    print("Saved", out)
    plt.show()

def plot_blinks_per_min(blinks_series, out="blinks_per_min.png"):
    plt.figure(figsize=(8,3))
    blinks_series.plot(kind="bar")
    plt.title("Blinks per minute")
    plt.xlabel("minute"); plt.ylabel("blinks")
    plt.tight_layout()
    plt.savefig(out)
    print("Saved", out)
    plt.show()

def summary(df):
    dur = df["timestamp"].iloc[-1] - df["timestamp"].iloc[0]
    total_blinks = int(df["total_blinks"].max())
    avg_ear = df["ear"].mean()
    avg_perclos = df["perclos"].mean()
    blinks_per_min_avg = total_blinks / (dur.total_seconds()/60) if dur.total_seconds()>0 else float(total_blinks)
    print("==== Session summary ====")
    print("Duration:", str(dur))
    print("Total blinks:", total_blinks)
    print("Avg EAR:", round(avg_ear,3))
    print("Avg PERCLOS:", round(avg_perclos,3))
    print("Avg blinks/min:", round(blinks_per_min_avg,3))
    print("=========================")

def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "logs.csv"
    try:
        df = load_logs(path)
    except Exception as e:
        print("Failed to load", path, ":", e)
        return
    if df.empty:
        print("No data in", path); return
    summary(df)
    blinks = blinks_per_minute(df)
    print("\nBlinks per minute (sample):")
    print(blinks.to_string())
    # save numeric summary to CSV
    stats = {
        "duration": [str(df["timestamp"].iloc[-1] - df["timestamp"].iloc[0])],
        "total_blinks": [int(df["total_blinks"].max())],
        "avg_ear": [round(df["ear"].mean(),4)],
        "avg_perclos": [round(df["perclos"].mean(),4)],
        "avg_blinks_per_min": [round(int(df["total_blinks"].max()) / ((df["timestamp"].iloc[-1] - df["timestamp"].iloc[0]).total_seconds()/60) if (df["timestamp"].iloc[-1] - df["timestamp"].iloc[0]).total_seconds()>0 else int(df["total_blinks"].max()),4)]
    }
    pd.DataFrame(stats).to_csv("logs_summary.csv", index=False)
    print("Saved logs_summary.csv")
    # plots
    try:
        plot_perclos(df)
        plot_blinks_per_min(blinks)
    except Exception as e:
        print("Plot failed (maybe headless environment):", e)

if __name__ == "__main__":
    main()
