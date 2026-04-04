import os
import sys
import csv
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np


def diagnose_lct_data(df):

    timestamps = pd.to_numeric(df.iloc[:, 0], errors="coerce")
    current_lane = df["currentLane"]
    target_lane = df["targetLane"]

    num_rows = len(df)
    num_invalid_time = timestamps.isna().sum()

    print("\n--- Diagnostics ---")
    print(f"Total rows: {num_rows}")
    print(f"Invalid timestamps: {num_invalid_time}")

    if num_invalid_time > 0:
        print("⚠️ Warning: Found non-numeric timestamps")

    # Time progression
    time_diffs = timestamps.diff()

    num_negative_dt = (time_diffs < 0).sum()
    num_zero_dt = (time_diffs == 0).sum()

    print(f"Negative time steps: {num_negative_dt}")
    print(f"Zero time steps: {num_zero_dt}")

    # Total duration
    if timestamps.notna().any():
        t_valid = timestamps.dropna()
        total_time = float(t_valid.iloc[-1]) - float(t_valid.iloc[0])
    else:
        total_time = float("nan")

    print(f"Total duration: {total_time:.6f} s")

    if total_time <= 0 or pd.isna(total_time):
        print("⚠️ Warning: Invalid or zero total duration")

    # Lane sanity
    num_lane_mismatch = (current_lane != target_lane).sum()
    print(f"Total wrong-lane samples: {num_lane_mismatch}")

    if num_lane_mismatch == 0:
        print("⚠️ Warning: Driver never deviates from target lane (unexpected?)")

    print("--- End Diagnostics ---\n")

# -------------------------------------------------
#--------------------Main program
# -------------------------------------------------

#Set filepaths
input_csv = sys.argv[1]
input_dir = os.path.dirname(os.path.abspath(input_csv))
base_name = os.path.splitext(os.path.basename(input_csv))[0]
output_dir = os.path.join(input_dir, "..\graphs")
os.makedirs(output_dir, exist_ok=True)

# Validate input file
if not os.path.isfile(input_csv):
    print(f"Error: File not found -> {input_csv}")
    sys.exit(1)

#Find header row and check valid
expected_cols = ["Meters", "LateralPos", "currentLane", "targetLane"]
header_row_idx = None

with open(input_csv, "r", encoding="utf-8", errors="replace") as f:
    reader = csv.reader(f)
    for i, row in enumerate(reader):
        # Ensure enough columns
        if len(row) >= 5:
            # Compare columns 2–5 (index 1–4)
            if [col.strip() for col in row[1:5]] == expected_cols:
                header_row_idx = i
                break

if header_row_idx is None:
    raise ValueError("Could not find header row based on expected columns")

# Read file, skip rows before valid header
df = pd.read_csv(input_csv, skiprows=header_row_idx, header=0)

#Add Timestamp title for first column
df.columns = ["Timestamp", "Meters", "LateralPos", "currentLane", "targetLane"]

# Convert to numeric
for col in df.columns:
    df[col] = pd.to_numeric(df[col], errors="coerce")

# Drop invalid rows
df = df.dropna()
df = df.sort_values("Meters").reset_index(drop=True)

# --------------------------------------------------
# --- LCT performance metrics ---
# --------------------------------------------------

# --- LCT lane-change metrics (simple & robust) ---

timestamps = df.iloc[:, 0]
current_lane = df["currentLane"]
target_lane = df["targetLane"]

#Check data
diagnose_lct_data(df)

missed_lane_changes = 0
lane_change_times = []
wrong_lane_time = 0.0

# 1) Time spent in wrong lane
for i in range(1, len(df)):
    t_prev = float(timestamps.iloc[i - 1])
    t_now = float(timestamps.iloc[i])
    dt = t_now - t_prev

    if current_lane.iloc[i - 1] != target_lane.iloc[i - 1]:
        wrong_lane_time += dt

total_time = float(timestamps.iloc[-1]) - float(timestamps.iloc[0])
wrong_lane_pct = 100.0 * wrong_lane_time / total_time if total_time > 0 else float("nan")

# 2) Lane change detection
for i in range(1, len(df)):

    # Detect when a new lane is requested
    if target_lane.iloc[i] != target_lane.iloc[i - 1]:

        new_target = target_lane.iloc[i]
        start_time = float(timestamps.iloc[i])

        # IMPORTANT: only count if driver is NOT already in that lane
        if current_lane.iloc[i] == new_target:
            continue

        reached = False

        # Search forward
        for j in range(i + 1, len(df)):

            # Stop if another command occurs
            if target_lane.iloc[j] != target_lane.iloc[j - 1]:
                break

            # Detect when driver actually reaches the lane
            if current_lane.iloc[j] == new_target:
                end_time = float(timestamps.iloc[j])
                lane_change_times.append(end_time - start_time)
                reached = True
                break

        if not reached:
            missed_lane_changes += 1

avg_lane_change_time = (
    sum(lane_change_times) / len(lane_change_times)
    if lane_change_times else float("nan")
)

print(f"Missed lane changes: {missed_lane_changes}")
print(f"Wrong-lane time: {wrong_lane_time:.3f} s")
print(f"Percentage of time in wrong lane: {wrong_lane_pct:.2f}%")
print(f"Average lane-change time: {avg_lane_change_time:.3f} s")

# --------------------------------------------------
# 1. Lane → meter mapping (reference positions)
# --------------------------------------------------

def lane_to_meters(lane):
    if lane == -1:
        return -8.2
    elif lane == 0:
        return 0.0
    elif lane == 1:
        return 8.2
    else:
        return np.nan

df["target_pos_m"] = df["targetLane"].apply(lane_to_meters)

# --------------------------------------------------
# 2. Sigmoid smoothing parameters
# --------------------------------------------------

LANE_CHANGE_DURATION = 3.0   # seconds
SIGMOID_STEEPNESS = 10       # shape of transition

# --------------------------------------------------
# 3. Build smooth reference trajectory
# --------------------------------------------------

df["target_pos_smooth"] = df["target_pos_m"].copy()

change_indices = df.index[df["targetLane"].diff() != 0].tolist()

for idx in change_indices:
    if idx == 0:
        continue

    start_pos = df.loc[idx - 1, "target_pos_m"]
    end_pos = df.loc[idx, "target_pos_m"]

    start_time = df.loc[idx, "Timestamp"]
    end_time = start_time + LANE_CHANGE_DURATION

    mask = (df["Timestamp"] >= start_time) & (df["Timestamp"] <= end_time)

    if mask.sum() == 0:
        continue

    t = df.loc[mask, "Timestamp"]

    # Normalize time to [0,1]
    t_norm = (t - start_time) / LANE_CHANGE_DURATION

    # Sigmoid
    sigmoid = 1 / (1 + np.exp(-SIGMOID_STEEPNESS * (t_norm - 0.5)))

    df.loc[mask, "target_pos_smooth"] = start_pos + sigmoid * (end_pos - start_pos)

# --------------------------------------------------
# 4. Compute deviation
# --------------------------------------------------

df["deviation_m"] = abs(df["LateralPos"] - df["target_pos_smooth"])

# --------------------------------------------------
# 5. Compute mdev (distance-weighted)
# --------------------------------------------------

df["delta_x"] = df["Meters"].diff()
df = df.dropna()

total_distance = df["delta_x"].sum()
weighted_deviation = (df["deviation_m"] * df["delta_x"]).sum()

mdev = weighted_deviation / total_distance

print(f"\nTotal distance: {total_distance:.2f} m")
print(f"Total mdev: {mdev:.4f} m")

# --------------------------------------------------
# 6. Plot
# --------------------------------------------------

fig, ax1 = plt.subplots(figsize=(12,4))

# Driver (real data)
ax1.plot(
    df["Timestamp"],
    df["LateralPos"],
    label="Driver Lateral Position (m)"
)

# Smoothed reference
ax1.plot(
    df["Timestamp"],
    df["target_pos_smooth"],
    linestyle="--",
    label="Target Position (Smooth)"
)

ax1.set_xlabel("Time (seconds)")
ax1.set_ylabel("Lateral Position (m)")
ax1.grid(True, alpha=0.3)

# Deviation
"""ax2 = ax1.twinx()

ax2.plot(
    df["Timestamp"],
    df["deviation_m"],
    linestyle=":",
    label="Deviation (m)"
)

ax2.set_ylabel("Deviation (m)") """

# Legend
lines_1, labels_1 = ax1.get_legend_handles_labels()
#lines_2, labels_2 = ax2.get_legend_handles_labels()

#ax1.legend(lines_1 + lines_2, labels_1 + labels_2)
ax1.legend(loc="upper center", bbox_to_anchor=(0.5, -0.15), ncol=2)

plt.yticks([-8.2,0,8.2], ["Left","Center","Right"])

plt.title(f"LCT Analysis: {base_name} (mdev = {mdev:.3f} m)")

#Add metrics box
metrics_text = (
    f"Missed: {missed_lane_changes}\n"
    f"Wrong lane: {wrong_lane_pct:.2f}%\n"
    f"Avg lane change: {avg_lane_change_time:.2f} s"
)

ax1.text(
    0.02, 0.95,
    metrics_text,
    transform=ax1.transAxes,
    fontsize=10,
    verticalalignment='top',
    bbox=dict(boxstyle="round", facecolor="white", alpha=0.7)
)

#Write to file
output_filename = f"{base_name}_graph.png"
output_path = os.path.join(output_dir, output_filename)
plt.tight_layout()
plt.savefig(output_path,  bbox_inches="tight", dpi=300)
print(f"Wrote file to: {output_path}")

#Display
plt.show()

