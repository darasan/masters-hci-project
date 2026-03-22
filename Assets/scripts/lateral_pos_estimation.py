import sys
import os
import pandas as pd
import numpy as np

# -------------------------------
# Parameters (tune as needed)
# -------------------------------
REACTION_TIME = 0.5
LANE_CHANGE_DURATION = 3.0
SIGMOID_STEEPNESS = 10

# Lane mapping (meters)
LANE_MAP = {
    -1: -8.2,
     0:  0.0,
     1:  8.2
}

# -------------------------------
# Load data
# -------------------------------
input_file = sys.argv[1]

df = pd.read_csv(input_file)
df.columns = ["timestamp", "meters", "currentLane", "targetLane"]

# Convert to numeric
for col in df.columns:
    df[col] = pd.to_numeric(df[col], errors="coerce")

# Clean + sort
df = df.dropna()
df = df.sort_values("timestamp").reset_index(drop=True)

# Enforce integer lane values
df["currentLane"] = df["currentLane"].round().astype(int)
df["targetLane"] = df["targetLane"].round().astype(int)

# -------------------------------
# Output path
# -------------------------------
input_dir = os.path.dirname(input_file)
base_name = os.path.basename(input_file)
name, ext = os.path.splitext(base_name)

output_file = os.path.join(input_dir, f"{name}_with_approx{ext}")

# -------------------------------
# Helper: sigmoid
# -------------------------------
def sigmoid(x, k=SIGMOID_STEEPNESS):
    return 1 / (1 + np.exp(-k * (x - 0.5)))

# -------------------------------
# Main loop
# -------------------------------
approx_pos = []

current_pos = LANE_MAP[df.loc[0, "currentLane"]]

transition_positions = []
in_transition = False
transition_start_time = 0.0

for i in range(len(df)):

    t = df.loc[i, "timestamp"]

    current_lane = int(df.loc[i, "targetLane"])
    target_pos = LANE_MAP[current_lane]

    # Detect new maneuver
    if i > 0 and df.loc[i, "currentLane"] != df.loc[i - 1, "currentLane"]:

        start_lane = int(df.loc[i - 1, "currentLane"])
        end_lane = current_lane

        # Build symmetric lane sequence
        step = 1 if end_lane > start_lane else -1
        lane_sequence = list(range(start_lane, end_lane + step, step))

        transition_positions = [LANE_MAP[l] for l in lane_sequence]

        in_transition = True
        transition_start_time = t

    # -------------------------------
    # Apply transition model
    # -------------------------------
    if in_transition:

        dt = t - transition_start_time

        # Reaction delay (only once)
        if dt >= REACTION_TIME:

            movement_dt = dt - REACTION_TIME

            step_time = LANE_CHANGE_DURATION
            step_index = int(movement_dt // step_time)

            # End of transition
            if step_index >= len(transition_positions) - 1:
                current_pos = transition_positions[-1]
                in_transition = False

            else:
                t_step = (movement_dt % step_time) / step_time
                s = sigmoid(t_step)

                start_pos = transition_positions[step_index]
                end_pos = transition_positions[step_index + 1]

                current_pos = start_pos + s * (end_pos - start_pos)

    approx_pos.append(round(current_pos, 2))

# -------------------------------
# Save results
# -------------------------------
df["approxLateralPos"] = approx_pos

cols = df.columns.tolist()

# Move "approxLateralPos" to be the third column (index 2)
cols.insert(2, cols.pop(cols.index("approxLateralPos")))

df = df[cols]

df.to_csv(output_file, index=False)

print(f"Output written to: {output_file}")