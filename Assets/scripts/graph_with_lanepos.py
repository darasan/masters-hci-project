import os
import sys
import csv
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
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
figures_output_dir = os.path.normpath(os.path.join(input_dir, "..", "figures"))
processed_output_dir = os.path.normpath(os.path.join(input_dir, "..\..", "data\processed")) #check on Mac or set dir directly

#Create output directories
os.makedirs(figures_output_dir, exist_ok=True)
os.makedirs(processed_output_dir, exist_ok=True)

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

#print("Loaded rows:", len(df))
#print(df.head(10).to_string())

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
current_shape = None

#Add column for shape_active
position_df["shape_active"] = 0

#Add column for shape depth
position_df["shape_depth"] = ""

for _, row in df.iterrows():
    if row["Col2"] == "Detect shape prompt by spacebar:":
        shape_text = row["Col4"] if pd.notna(row["Col4"]) else ""
        #Extract current shape depth
        prefix = "Current shape: "
        if shape_text.startswith(prefix):
            current_shape = shape_text[len(prefix):]
        else:
            current_shape = shape_text

        if row["Col3"] == "True":
            start_time = row["Timestamp"]
        elif row["Col3"] == "False" and start_time is not None:
            shape_intervals.append((start_time, row["Timestamp"]))
            mask = (position_df["Timestamp"] >= start_time) & (position_df["Timestamp"] <= row["Timestamp"])
            position_df.loc[mask, "shape_active"] = 1
            position_df.loc[mask, "shape_depth"] = current_shape
            start_time = None
            current_shape = None

#print(f"shape_active column: ")
#print(position_df.iloc[100:201]["shape_active"])

#Compare mdev when active vs not
active = position_df[position_df["shape_active"] == 1]["deviation_m"]
inactive = position_df[position_df["shape_active"] == 0]["deviation_m"]

# --------------------------------------------------
# 7. Print results
# --------------------------------------------------

#Round all numbers to 4 places
cols_to_round = ["Timestamp", "Meters", "LateralPos", "target_pos_smooth", "deviation_m"]
position_df[cols_to_round] = position_df[cols_to_round].round(4)

print(f"Total mdev: {mdev:.4f} m")
print(f"Missed lane changes: {missed_lane_changes}")
print(f"Wrong-lane time: {wrong_lane_time:.3f} s")
print(f"Percentage of time in wrong lane: {wrong_lane_pct:.2f}%")
print(f"Average lane-change time: {avg_lane_change_time:.3f} s")
print(f"Active mean: {active.mean():.3f}")
print(f"Inactive mean: {inactive.mean():.3f}")

#Shape detection intervals
print(f"Shape detection intervals: ")
for i, (start, end) in enumerate(shape_intervals, start=1):
    print(f"Interval {i}: {start} -> {end}")

#Print test rows
#print(f"All position_df columns: ")
#print(position_df.columns.tolist())

#Print rows in range
#print(position_df.iloc[10:400].to_string())

#Print everything
#print(position_df.to_string())

#Dump position dataframe to CSV (cleaned data)
output_csv_path = os.path.join(processed_output_dir, f"{base_name}_clean.csv")
position_df.to_csv(output_csv_path, index=False)
print(f"Wrote CSV file to: {output_csv_path}")


# --------------------------------------------------
# 8. Plot results
# --------------------------------------------------

def draw_lct_plot(ax, label_fs=10, tick_fs=10, title_fs=12, legend_fs=10, metrics_fs=10, show_metrics=True):
    ax.plot(
        position_df["Timestamp"],
        position_df["LateralPos"],
        label="Driver Lateral Position (m)"
    )

    ax.plot(
        position_df["Timestamp"],
        position_df["target_pos_smooth"],
        linestyle="--",
        label="Ideal Position"
    )

    for i, (start, end) in enumerate(shape_intervals):
        ax.axvspan(
            start,
            end,
            alpha=0.15,
            label="Shape prompt active" if i == 0 else None
        )

    ax.set_xlabel("Time (seconds)", fontsize=label_fs)
    ax.set_ylabel("Lateral Position (m)", fontsize=label_fs)
    ax.grid(True, alpha=0.3)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.3), ncol=2, fontsize=legend_fs)
    ax.set_yticks([-12.6, -8.4, -4.2, 0, 4.2, 8.4, 12.6])
    ax.set_yticklabels([
        "Lane R (limit)",
        "Lane R (center)",
        "Lane R (limit)",
        "Center lane",
        "Lane L (limit)",
        "Lane L (center)",
        "Lane L (limit)"
    ])
    ax.tick_params(axis="both", labelsize=tick_fs)
    ax.set_title(f"LCT Analysis: {base_name} (mdev = {mdev:.3f} m)", fontsize=title_fs)

    metrics_text = (
        f"Missed: {missed_lane_changes}\n"
        f"Wrong lane: {wrong_lane_pct:.2f}%\n"
        f"Avg lane change: {avg_lane_change_time:.2f} s"
    )

    if show_metrics:
        ax.text(
            0.02, 0.95,
            metrics_text,
            transform=ax.transAxes,
            fontsize=metrics_fs,
            verticalalignment='top',
            bbox=dict(boxstyle="round", facecolor="white", alpha=0.7)
        )


fig, ax1 = plt.subplots(figsize=(12, 4))
draw_lct_plot(ax1)

#Store plot as PNG file
png_output_filename = f"{base_name}_graph.png"
png_output_path = os.path.join(figures_output_dir, png_output_filename)
plt.tight_layout()
fig.savefig(png_output_path, bbox_inches="tight", dpi=300)
print(f"Wrote PNG file to: {png_output_path}")

# Build separate PDF figure and redraw the plot there so it stays vector.
text = (
    f"Total mdev: {mdev:.4f} metres\n"
    f"Missed lane changes: {missed_lane_changes}\n"
    f"Wrong-lane time: {wrong_lane_time:.3f} s\n"
    f"Percentage of time in wrong lane: {wrong_lane_pct:.2f}%\n"
    f"Average lane-change time: {avg_lane_change_time:.3f} s\n"
    f"Active mean: {active.mean():.3f}\n"
    f"Inactive mean: {inactive.mean():.3f}\n"
)

fig_pdf, (ax_text, ax_plot) = plt.subplots(
    2,
    1,
    figsize=(8.27, 11.69),
    gridspec_kw={"height_ratios": [0.8, 1.2]}
)

fig_pdf.subplots_adjust(hspace=0.45, top=0.95, bottom=0.45)

ax_text.axis("off")
ax_text.text(
    0.0, 0.95,
    "Summary",
    fontsize=14,
    fontweight="bold",
    ha="left",
    va="top",
    transform=ax_text.transAxes
)
ax_text.text(
    0.0, 0.82,
    text,
    fontsize=12,
    ha="left",
    va="top",
    multialignment="left",
    transform=ax_text.transAxes
)

draw_lct_plot(ax_plot, label_fs=8, tick_fs=7, title_fs=10, legend_fs=8, metrics_fs=8, show_metrics=False)

plot_pos = ax_plot.get_position()
ax_plot.set_position([
    plot_pos.x0 + 0.04,
    plot_pos.y0,
    plot_pos.width - 0.08,
    plot_pos.height
])

#Store to PDF
#pdf_path = "figures/subject_01_runs.pdf"
#print("Writing to:", output_path.resolve())

pdf_output_filename = f"{base_name}_summary.pdf"
pdf_output_path = os.path.join(figures_output_dir, pdf_output_filename)

with PdfPages(pdf_output_path) as pdf:
    pdf.savefig(fig_pdf)
    plt.close(fig_pdf)
    plt.close(fig)
print(f"Wrote PDF file to: {pdf_output_path}")

#Display
#plt.show()

