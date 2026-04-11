import os
import sys
import csv
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np


def diagnose_lct_data(df):

    timestamps = pd.to_numeric(df["Timestamp"], errors="coerce").dropna().reset_index(drop=True)
    current_lane = df["currentLane"]
    target_lane = df["targetLane"]

    num_rows = len(df)
    num_invalid_time = df["Timestamp"].isna().sum()

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
    if not timestamps.empty:
        total_time = float(timestamps.iloc[-1]) - float(timestamps.iloc[0])
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

# Set filepaths
input_csv = sys.argv[1]
input_dir = os.path.dirname(os.path.abspath(input_csv))
base_name = os.path.splitext(os.path.basename(input_csv))[0]
output_dir = os.path.normpath(os.path.join(input_dir, "..", "graphs"))
os.makedirs(output_dir, exist_ok=True)

# Validate input file
if not os.path.isfile(input_csv):
    print(f"Error: File not found -> {input_csv}")
    sys.exit(1)

# Find header row by matching the fixed columns 2-5
expected_cols = ["Meters", "LateralPos", "currentLane", "targetLane"]
header_row_idx = None

with open(input_csv, "r", encoding="utf-8", errors="replace", newline="") as f:
    reader = csv.reader(f)
    for i, row in enumerate(reader):
        if len(row) >= 5 and [cell.strip() for cell in row[1:5]] == expected_cols:
            header_row_idx = i
            break

if header_row_idx is None:
    raise ValueError("Could not find header row based on expected columns")

# Read raw event log without forcing numeric conversion
df = pd.read_csv(
    input_csv,
    skiprows=header_row_idx,
    header=0,
    dtype=str
)

# Give stable generic names that work for mixed event types
df.columns = ["Timestamp", "Col2", "Col3", "Col4", "Col5"]

# Basic cleanup only
for col in df.columns:
    df[col] = df[col].astype("string").str.strip()

# Drop rows with no timestamp at all
df = df.dropna(subset=["Timestamp"])
df = df[df["Timestamp"] != ""]

# Convert timestamp only, because all event types should have it
df["Timestamp"] = pd.to_numeric(df["Timestamp"], errors="coerce")
df = df.dropna(subset=["Timestamp"]).sort_values("Timestamp").reset_index(drop=True)

print("Loaded rows:", len(df))
print(df.head(10).to_string())

# Drop invalid rows
#df = df.dropna(subset=[df.columns[0]]) #drop if timestamp missing
#df = df.sort_values("Timestamp").reset_index(drop=True)

# --------------------------------------------------
# --- LCT performance metrics ---
# --------------------------------------------------

position_df = df.copy()

for col in ["Col2", "Col3", "Col4", "Col5"]:
    position_df[col] = pd.to_numeric(position_df[col], errors="coerce")

position_df = position_df.dropna(subset=["Col2", "Col3", "Col4", "Col5"]).reset_index(drop=True)

position_df = position_df.rename(columns={
    "Col2": "Meters",
    "Col3": "LateralPos",
    "Col4": "currentLane",
    "Col5": "targetLane"
})

timestamps = position_df.iloc[:, 0]
current_lane = position_df["currentLane"]
target_lane = position_df["targetLane"]

#Check data
diagnose_lct_data(position_df)

missed_lane_changes = 0
lane_change_times = []

# 2) Lane change detection
for i in range(1, len(position_df)):

    # Detect when a new lane is requested
    if target_lane.iloc[i] != target_lane.iloc[i - 1]:

        new_target = target_lane.iloc[i]
        start_time = float(timestamps.iloc[i])

        # IMPORTANT: only count if driver is NOT already in that lane
        if current_lane.iloc[i] == new_target:
            continue

        reached = False

        # Search forward
        for j in range(i + 1, len(position_df)):

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

# --------------------------------------------------
# 1. Lane → meter mapping (reference positions)
# --------------------------------------------------

def lane_to_meters(lane):
    if lane == -1:
        return -8.4 #centre of lane, limit is -4.2
    elif lane == 0:
        return 0.0
    elif lane == 1:
        return 8.4  #centre of lane, limit is 4.2
    else:
        return np.nan

position_df["target_pos_m"] = position_df["targetLane"].apply(lane_to_meters)

# --------------------------------------------------
# 2. Sigmoid smoothing parameters
# --------------------------------------------------

LANE_CHANGE_DURATION = 4.0   # seconds
SIGMOID_STEEPNESS = 8       # shape of transition

# --------------------------------------------------
# 3. Build smooth reference trajectory
# --------------------------------------------------

position_df["target_pos_smooth"] = position_df["target_pos_m"].copy()

change_indices = position_df.index[position_df["targetLane"].diff() != 0].tolist()

for idx in change_indices:
    if idx == 0:
        continue

    start_pos = position_df.loc[idx - 1, "target_pos_m"]
    end_pos = position_df.loc[idx, "target_pos_m"]

    start_time = position_df.loc[idx, "Timestamp"]
    end_time = start_time + LANE_CHANGE_DURATION

    mask = (position_df["Timestamp"] >= start_time) & (position_df["Timestamp"] <= end_time)

    if mask.sum() == 0:
        continue

    t = position_df.loc[mask, "Timestamp"]

    # Normalize time to [0,1]
    t_norm = (t - start_time) / LANE_CHANGE_DURATION

    # Sigmoid
    sigmoid = 1 / (1 + np.exp(-SIGMOID_STEEPNESS * (t_norm - 0.5)))

    position_df.loc[mask, "target_pos_smooth"] = start_pos + sigmoid * (end_pos - start_pos)

# --------------------------------------------------
# 4. Compute deviation
# --------------------------------------------------

position_df["deviation_m"] = abs(position_df["LateralPos"] - position_df["target_pos_smooth"])

# Count time outside the smooth target corridor.
# Lane centers are 8.4 m apart, so half a lane is 4.2 m.
LANE_HALF_WIDTH = 4.2

wrong_lane_time = 0.0
for i in range(1, len(position_df)):
    t_prev = float(position_df.loc[i - 1, "Timestamp"])
    t_now = float(position_df.loc[i, "Timestamp"])
    dt = t_now - t_prev

    if position_df.loc[i - 1, "deviation_m"] > LANE_HALF_WIDTH:
        wrong_lane_time += dt

total_time = float(df["Timestamp"].iloc[-1]) - float(df["Timestamp"].iloc[0])
wrong_lane_pct = 100.0 * wrong_lane_time / total_time if total_time > 0 else float("nan")

# --------------------------------------------------
# 5. Compute mdev (distance-weighted)
# --------------------------------------------------

# Use traveled distance between consecutive timestamped samples.
# In timestamp order, track position can occasionally decrease, so use magnitude.
position_df["delta_x"] = position_df["Meters"].diff().abs()
position_df = position_df.dropna().reset_index(drop=True)

total_distance = position_df["delta_x"].sum()
weighted_deviation = (position_df["deviation_m"] * position_df["delta_x"]).sum()

mdev = weighted_deviation / total_distance if total_distance > 0 else float("nan")

# --------------------------------------------------
# 6. Plot timestamps where shape detection is active
# --------------------------------------------------
time_col = df.columns[0]
event_col = df.columns[1]
value_col = df.columns[2]

shape_intervals = []
start_time = None

for _, row in df.iterrows():
    if row["Col2"] == "Detect shape prompt by spacebar:":
        if row["Col3"] == "True":
            start_time = row["Timestamp"]
        elif row["Col3"] == "False" and start_time is not None:
            shape_intervals.append((start_time, row["Timestamp"]))
            start_time = None

#Add column for shape_active
position_df["shape_active"] = 0

for start, end in shape_intervals:
    mask = (position_df["Timestamp"] >= start) & (position_df["Timestamp"] <= end)
    position_df.loc[mask, "shape_active"] = 1

#print(f"shape_active column: ")
#print(position_df.iloc[100:201]["shape_active"])

#Compare mdev when active vs not
active = position_df[position_df["shape_active"] == 1]["deviation_m"]
inactive = position_df[position_df["shape_active"] == 0]["deviation_m"]

# --------------------------------------------------
# 7. Print results
# --------------------------------------------------

print(f"Total mdev: {mdev:.4f} m")
print(f"Missed lane changes: {missed_lane_changes}")
print(f"Wrong-lane time: {wrong_lane_time:.3f} s")
print(f"Percentage of time in wrong lane: {wrong_lane_pct:.2f}%")
print(f"Average lane-change time: {avg_lane_change_time:.3f} s")
print("Active mean:", active.mean())
print("Inactive mean:", inactive.mean())

#Shape detection intervals
print(f"Shape detection intervals: ")
for i, (start, end) in enumerate(shape_intervals, start=1):
    print(f"Interval {i}: {start} -> {end}")

#Print test rows
#print(f"All position_df columns: ")
#print(position_df.columns.tolist())

#Print rows in range
#print(position_df.iloc[10:400].to_string())
#print(position_df.to_string())

# --------------------------------------------------
# 8. Plot results
# --------------------------------------------------

fig, ax1 = plt.subplots(figsize=(12,4))

# Driver (real data)
ax1.plot(
    position_df["Timestamp"],
    position_df["LateralPos"],
    label="Driver Lateral Position (m)"
)

# Smoothed reference 
ax1.plot(
    position_df["Timestamp"],
    position_df["target_pos_smooth"],
    linestyle="--",
    label="Ideal Position"
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

#Plot shape detection intervals
for i, (start, end) in enumerate(shape_intervals):
    ax1.axvspan(
        start,
        end,
        alpha=0.15,
        label="Shape prompt active" if i == 0 else None
    )

# Legend
lines_1, labels_1 = ax1.get_legend_handles_labels()
#lines_2, labels_2 = ax2.get_legend_handles_labels()

#ax1.legend(lines_1 + lines_2, labels_1 + labels_2)
ax1.legend(loc="upper center", bbox_to_anchor=(0.5, -0.15), ncol=2)

#plt.yticks([-8.4,0,8.4], ["Left","Center","Right"])
plt.yticks([-12.6,-8.4,-4.2, 0, 4.2, 8.4, 12.6], ["Lane R (limit)", "Lane R (center)", "Lane R (limit)", "Center lane", "Lane L (limit)", "Lane L (center)", "Lane L (limit)"])

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
#plt.show()

