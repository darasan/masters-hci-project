import sys
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Load data
df = pd.read_csv(sys.argv[1])

print("Columns in file:", df.columns)

# Rename columns
df.columns = ["timestamp", "meters", "LateralPos", "currentLane", "targetLane"]

# Convert to numeric
for col in df.columns:
    df[col] = pd.to_numeric(df[col], errors="coerce")

# Drop invalid rows
df = df.dropna()
df = df.sort_values("meters").reset_index(drop=True)

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
# 2. Sigmoid smoothing parameters (TUNE THESE)
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

    start_time = df.loc[idx, "timestamp"]
    end_time = start_time + LANE_CHANGE_DURATION

    mask = (df["timestamp"] >= start_time) & (df["timestamp"] <= end_time)

    if mask.sum() == 0:
        continue

    t = df.loc[mask, "timestamp"]

    # Normalize time to [0,1]
    t_norm = (t - start_time) / LANE_CHANGE_DURATION

    # Sigmoid
    sigmoid = 1 / (1 + np.exp(-SIGMOID_STEEPNESS * (t_norm - 0.5)))

    df.loc[mask, "target_pos_smooth"] = start_pos + sigmoid * (end_pos - start_pos)

# --------------------------------------------------
# 4. Compute deviation (TRUE, continuous)
# --------------------------------------------------

df["deviation_m"] = abs(df["LateralPos"] - df["target_pos_smooth"])

# --------------------------------------------------
# 5. Compute mdev (distance-weighted)
# --------------------------------------------------

df["delta_x"] = df["meters"].diff()
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
    df["timestamp"],
    df["LateralPos"],
    label="Driver Lateral Position (m)"
)

# Smoothed reference
ax1.plot(
    df["timestamp"],
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
    df["timestamp"],
    df["deviation_m"],
    linestyle=":",
    label="Deviation (m)"
)

ax2.set_ylabel("Deviation (m)") """

# Legend
lines_1, labels_1 = ax1.get_legend_handles_labels()
#lines_2, labels_2 = ax2.get_legend_handles_labels()

#ax1.legend(lines_1 + lines_2, labels_1 + labels_2)
ax1.legend(lines_1, labels_1)

plt.yticks([-8.2,0,8.2], ["Left","Center","Right"])

plt.title(f"LCT Analysis (mdev = {mdev:.3f} m)")

plt.tight_layout()
plt.savefig("lct_smooth_reference.png", dpi=300)

plt.show()