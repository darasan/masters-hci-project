import os
import sys
import csv
import re
import textwrap
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import numpy as np
import statistics
from pathlib import Path


LANE_CHANGE_DURATION = 4.0
SIGMOID_STEEPNESS = 8
LANE_HALF_WIDTH = 4.2
ISO_SYMBOL_APPEARS_BEFORE_SIGN_M = 40.0
ISO_REFERENCE_START_BEFORE_SIGN_M = 30.0
ISO_REFERENCE_END_BEFORE_SIGN_M = 20.0
POSITION_COLUMNS = ["Timestamp", "Meters", "LateralPos", "currentLane", "targetLane"]
SIGN_POSITION_LOG_LABEL = "Created signal at x ="


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
        print("Warning: Found non-numeric timestamps")

    time_diffs = timestamps.diff()
    num_negative_dt = (time_diffs < 0).sum()
    num_zero_dt = (time_diffs == 0).sum()

    print(f"Negative time steps: {num_negative_dt}")
    print(f"Zero time steps: {num_zero_dt}")

    if not timestamps.empty:
        total_time = float(timestamps.iloc[-1]) - float(timestamps.iloc[0])
    else:
        total_time = float("nan")

    print(f"Total duration: {total_time:.6f} s")

    if total_time <= 0 or pd.isna(total_time):
        print("Warning: Invalid or zero total duration")

    num_lane_mismatch = (current_lane != target_lane).sum()
    print(f"Total wrong-lane samples: {num_lane_mismatch}")

    if num_lane_mismatch == 0:
        print("Warning: Driver never deviates from target lane (unexpected?)")

    print("--- End Diagnostics ---\n")


def lane_to_meters(lane):
    if lane == -1:
        return -8.4
    if lane == 0:
        return 0.0
    if lane == 1:
        return 8.4
    return np.nan


def load_lct_data(input_csv):
    if not os.path.isfile(input_csv):
        raise FileNotFoundError(f"File not found -> {input_csv}")

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

    raw_df = pd.read_csv(
        input_csv,
        skiprows=header_row_idx,
        header=0,
        dtype=str
    )

    raw_df.columns = ["Timestamp", "Col2", "Col3", "Col4", "Col5"]

    for col in raw_df.columns:
        raw_df[col] = raw_df[col].astype("string").str.strip()

    raw_df = raw_df.dropna(subset=["Timestamp"])
    raw_df = raw_df[raw_df["Timestamp"] != ""]
    raw_df["Timestamp"] = pd.to_numeric(raw_df["Timestamp"], errors="coerce")
    raw_df = raw_df.dropna(subset=["Timestamp"]).sort_values("Timestamp").reset_index(drop=True)

    position_df = raw_df.copy()
    for col in ["Col2", "Col3", "Col4", "Col5"]:
        position_df[col] = pd.to_numeric(position_df[col], errors="coerce")

    position_df = position_df.dropna(subset=["Col2", "Col3", "Col4", "Col5"]).reset_index(drop=True)
    position_df = position_df.rename(columns={
        "Col2": "Meters",
        "Col3": "LateralPos",
        "Col4": "currentLane",
        "Col5": "targetLane"
    })
    position_df = position_df[POSITION_COLUMNS].copy()

    return raw_df, position_df


def extract_sign_positions(raw_df, debug=True):
    sign_rows = raw_df[raw_df["Col2"] == SIGN_POSITION_LOG_LABEL].copy()
    sign_rows["raw_sign_position_m"] = pd.to_numeric(sign_rows["Col3"], errors="coerce")

    invalid_rows = sign_rows[sign_rows["raw_sign_position_m"].isna()]
    sign_positions = (
        sign_rows
        .dropna(subset=["raw_sign_position_m"])
        [["Timestamp", "raw_sign_position_m"]]
        .reset_index(drop=True)
    )

    #Apply offset for negative starting values
    sign_offset_m = (
        sign_positions["raw_sign_position_m"].iloc[0]
        if not sign_positions.empty else 0.0
    )
    sign_positions["sign_position_m"] = sign_positions["raw_sign_position_m"] - sign_offset_m

    if debug:
        raw_positions = sign_positions["raw_sign_position_m"].round(4).tolist()
        positions = sign_positions["sign_position_m"].round(4).tolist()
        print("\n--- Sign position parsing ---")
        print(f"Rows matching '{SIGN_POSITION_LOG_LABEL}': {len(sign_rows)}")
        print(f"Parsed sign positions: {len(sign_positions)}")
        print(f"Sign position offset applied (m): {sign_offset_m:.4f}")
        print(f"Raw sign positions (m): {raw_positions}")
        print(f"Normalized sign positions (m): {positions}")

        if not invalid_rows.empty:
            print("Warning: Some sign position rows could not be parsed:")
            print(invalid_rows[["Timestamp", "Col3"]].to_string(index=False))

        if len(sign_positions) > 1:
            spacing = sign_positions["sign_position_m"].diff().dropna()
            print(
                "Sign spacing (m): "
                f"min={spacing.min():.4f}, mean={spacing.mean():.4f}, max={spacing.max():.4f}"
            )

        print("--- End sign position parsing ---\n")

    return sign_positions

def calculate_mdev(df):
    total_distance = df["delta_x"].sum()
    if total_distance <= 0:
        return float("nan")

    return (df["deviation_m"] * df["delta_x"]).sum() / total_distance

#Keep only the final reversal value used when a shape is detected, to avoid intermediary values polluting the data
def filter_reversal_events(shape_events):
    outcome_events = {"Detected", "Not detected"}
    filtered_events = []

    for i, event in enumerate(shape_events):
        status, _, _ = event
        if status != "Change current reversal to":
            filtered_events.append(event)
            continue

        following_events = shape_events[i + 1:]
        next_outcome_idx = next(
            (
                j
                for j, following_event in enumerate(following_events)
                if following_event[0] in outcome_events
            ),
            None
        )

        if next_outcome_idx is None:
            continue

        events_before_outcome = following_events[:next_outcome_idx]
        has_later_reversal = any(
            following_event[0] == "Change current reversal to"
            for following_event in events_before_outcome
        )

        if not has_later_reversal:
            filtered_events.append(event)

    return filtered_events


def get_shape_detection_duration(timestamp, shape_intervals):
    for start, end in shape_intervals:
        if start <= timestamp <= end:
            return round((timestamp - start), 4)
    return None


def extract_shape_detection_events(raw_df, shape_intervals):
    shape_events = []

    for _, row in raw_df.iterrows():
        if row["Col2"] == "Confirmed that detected shape:":
            detection_duration = get_shape_detection_duration(row["Timestamp"], shape_intervals)
            shape_events.append(("Detected", row["Col3"], detection_duration))
        elif row["Col2"] == "Could not detect shape:":
            shape_events.append(("Not detected", row["Col3"], None))
        elif row["Col2"] == "Change current shape to:":
            shape_events.append(("Change current shape to", row["Col3"], None))
        elif row["Col2"] == "Change current reversal to:":
            shape_events.append(("Change current reversal to", row["Col3"], None))

    return filter_reversal_events(shape_events)


def extract_shape_depth_mm(shape_value):
    match = re.search(r"(\d+(?:\.\d+)?)\s*mm", str(shape_value))
    if not match:
        return None

    depth_text = match.group(1)
    depth_value = float(depth_text)
    return depth_value if "." in depth_text else depth_value / 100


def calculate_reversal_thresholds(shape_detection, expected_reversals=8):
    thresholds_by_reversal = {}
    last_detected_shape = None
    current_reversal = None

    for status, shape_value, _ in shape_detection:
        if status == "Change current reversal to":
            current_reversal = shape_value
        elif status == "Detected":
            last_detected_shape = shape_value
        elif status == "Not detected" and current_reversal is not None and last_detected_shape is not None:
            reversal_match = re.search(r"\d+", str(current_reversal))
            if not reversal_match:
                continue

            reversal_number = int(reversal_match.group(0))
            threshold_value = extract_shape_depth_mm(last_detected_shape)
            if (
                threshold_value is None
                or reversal_number < 1
                or reversal_number > expected_reversals
                or reversal_number in thresholds_by_reversal
            ):
                continue

            thresholds_by_reversal[reversal_number] = {
                "shape": last_detected_shape,
                "threshold_mm": threshold_value,
            }

    threshold_values = [
        thresholds_by_reversal[reversal_number]["threshold_mm"]
        for reversal_number in range(1, expected_reversals + 1)
        if reversal_number in thresholds_by_reversal
    ]
    mean_threshold = statistics.mean(threshold_values) if threshold_values else None

    return thresholds_by_reversal, mean_threshold


def build_reversal_threshold_lines(shape_detection, expected_reversals=8):
    threshold_lines = []
    thresholds_by_reversal, mean_threshold = calculate_reversal_thresholds(
        shape_detection,
        expected_reversals=expected_reversals,
    )

    for reversal_number in range(1, expected_reversals + 1):
        threshold_info = thresholds_by_reversal.get(reversal_number)
        if threshold_info is not None:
            threshold_lines.append(
                f"Reversal {reversal_number} threshold: {threshold_info['shape']}"
            )

    if mean_threshold is not None:
        threshold_lines.append(
            (
                f"\nMean detection threshold across {len(thresholds_by_reversal)}/{expected_reversals} reversals: "
                f"{mean_threshold:.4f} mm",
                True,
            )
        )

        print(
            f"\n\nMean detection threshold across "
            f"{len(thresholds_by_reversal)}/{expected_reversals} reversals: {mean_threshold:.4f}mm"
        )

    return threshold_lines


def build_mdev_by_shape_summary(all_summaries):
    mdev_by_shape_dfs = [
        summary["mdev_by_shape"]
        for summary in all_summaries
        if "mdev_by_shape" in summary and not summary["mdev_by_shape"].empty
    ]

    if not mdev_by_shape_dfs:
        return pd.DataFrame(columns=["shape_depth", "mdev"])

    all_mdev_by_shape = pd.concat(mdev_by_shape_dfs, ignore_index=True)
    all_mdev_by_shape["mdev"] = pd.to_numeric(all_mdev_by_shape["mdev"], errors="coerce")

    mean_mdev_by_shape = (
        all_mdev_by_shape
        .dropna(subset=["mdev"])
        .groupby("shape_depth", as_index=False)
        .agg(mdev=("mdev", "mean"))
    )

    mean_mdev_by_shape["shape_depth_mm"] = mean_mdev_by_shape["shape_depth"].apply(extract_shape_depth_mm)
    mean_mdev_by_shape = (
        mean_mdev_by_shape
        .sort_values(["shape_depth_mm", "shape_depth"], na_position="last")
        .drop(columns="shape_depth_mm")
        .reset_index(drop=True)
    )
    mean_mdev_by_shape["mdev"] = mean_mdev_by_shape["mdev"].round(4)

    return mean_mdev_by_shape


def build_detection_times_by_shape(shape_detection):
    detected_rows = [
        {
            "shape_depth": shape_depth,
            "avg_detection_time": detection_duration,
        }
        for status, shape_depth, detection_duration in shape_detection
        if status == "Detected" and detection_duration is not None
    ]

    if not detected_rows:
        return pd.DataFrame(columns=["shape_depth", "avg_detection_time", "num_detections"])

    detection_times_df = pd.DataFrame(detected_rows)
    detection_times_by_shape = (
        detection_times_df
        .groupby("shape_depth", as_index=False)
        .agg(
            avg_detection_time=("avg_detection_time", "mean"),
            num_detections=("avg_detection_time", "count"),
        )
    )

    return detection_times_by_shape


def build_statistics_by_shape_depth(shape_detection, all_summaries):
    mean_mdev_by_shape = build_mdev_by_shape_summary(all_summaries)
    detection_times_by_shape = build_detection_times_by_shape(shape_detection)

    statistics_by_shape_depth = pd.merge(
        mean_mdev_by_shape,
        detection_times_by_shape,
        on="shape_depth",
        how="outer",
    )

    if statistics_by_shape_depth.empty:
        return pd.DataFrame(columns=["shape_depth", "mdev", "avg_detection_time", "num_detections"])

    statistics_by_shape_depth["shape_depth_mm"] = statistics_by_shape_depth["shape_depth"].apply(extract_shape_depth_mm)
    statistics_by_shape_depth = (
        statistics_by_shape_depth
        .sort_values(["shape_depth_mm", "shape_depth"], na_position="last")
        .drop(columns="shape_depth_mm")
        .reset_index(drop=True)
    )

    for col in ["mdev", "avg_detection_time"]:
        statistics_by_shape_depth[col] = pd.to_numeric(
            statistics_by_shape_depth[col],
            errors="coerce",
        ).round(4)

    statistics_by_shape_depth["num_detections"] = pd.to_numeric(
        statistics_by_shape_depth["num_detections"],
        errors="coerce",
    ).fillna(0).astype("Int64")

    return statistics_by_shape_depth


def add_reference_trajectory(position_df):
    position_df["target_pos_m"] = position_df["targetLane"].apply(lane_to_meters)
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
        t_norm = (t - start_time) / LANE_CHANGE_DURATION
        sigmoid = 1 / (1 + np.exp(-SIGMOID_STEEPNESS * (t_norm - 0.5)))
        position_df.loc[mask, "target_pos_smooth"] = start_pos + sigmoid * (end_pos - start_pos)

    return position_df


def add_iso_reference_trajectory(position_df):
    position_df["target_pos_m"] = position_df["targetLane"].apply(lane_to_meters)
    position_df["target_pos_iso"] = position_df["target_pos_m"].copy()

    change_indices = position_df.index[position_df["targetLane"].diff() != 0].tolist()
    for idx in change_indices:
        if idx == 0:
            continue

        start_pos = position_df.loc[idx - 1, "target_pos_m"]
        end_pos = position_df.loc[idx, "target_pos_m"]

        symbol_appears_m = position_df.loc[idx, "Meters"]
        sign_position_m = symbol_appears_m + ISO_SYMBOL_APPEARS_BEFORE_SIGN_M
        reference_start_m = sign_position_m - ISO_REFERENCE_START_BEFORE_SIGN_M
        reference_end_m = sign_position_m - ISO_REFERENCE_END_BEFORE_SIGN_M

        #print("ISO sign position:", sign_position_m)
        #TODO use stated sign positions once figure out how offset works, see extract_sign_positions above.
        # If not then inference from targetLane here is better for now

        # rows where the reference should stay in the old lane
        hold_mask = (
            (position_df["Meters"] >= symbol_appears_m)
            & (position_df["Meters"] < reference_start_m)
        )
        position_df.loc[hold_mask, "target_pos_iso"] = start_pos

        # rows where the reference should transition between lanes
        change_mask = (
            (position_df["Meters"] >= reference_start_m)
            & (position_df["Meters"] <= reference_end_m)
        )
        if change_mask.sum() == 0:
            continue

        progress = (
            (position_df.loc[change_mask, "Meters"] - reference_start_m)
            / (reference_end_m - reference_start_m)
        )
        position_df.loc[change_mask, "target_pos_iso"] = start_pos + progress * (end_pos - start_pos)

    position_df["target_pos_smooth"] = position_df["target_pos_iso"]
    return position_df


################# Start analyze_lct_data #################
########################################################

def analyze_lct_data(raw_df, position_df,shape_detection, run_diagnostics=True):
    position_df = position_df.copy()

    if run_diagnostics:
        diagnose_lct_data(position_df)

    # Pull out the core lane-tracking series used throughout the analysis.
    timestamps = position_df["Timestamp"]
    current_lane = position_df["currentLane"]
    target_lane = position_df["targetLane"]

    # Measure how long commanded lane changes take and count any that are missed.
    missed_lane_changes = 0
    lane_change_times = []

    for i in range(1, len(position_df)):
        if target_lane.iloc[i] != target_lane.iloc[i - 1]:
            new_target = target_lane.iloc[i]
            start_time = float(timestamps.iloc[i])

            if current_lane.iloc[i] == new_target:
                continue

            reached = False
            for j in range(i + 1, len(position_df)):
                if target_lane.iloc[j] != target_lane.iloc[j - 1]:
                    break

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

    # Convert discrete target lanes into lateral positions and smooth transitions over time.
    #position_df = add_reference_trajectory(position_df)

    #ISO version - compute based on distance from sign
    position_df = add_iso_reference_trajectory(position_df)

    # Compare the driver's lateral position to the smooth reference trajectory.
    position_df["deviation_m"] = abs(position_df["LateralPos"] - position_df["target_pos_smooth"])

    # Accumulate time spent outside the target lane corridor.
    wrong_lane_time = 0.0
    for i in range(1, len(position_df)):
        t_prev = float(position_df.loc[i - 1, "Timestamp"])
        t_now = float(position_df.loc[i, "Timestamp"])
        dt = t_now - t_prev

        if position_df.loc[i - 1, "deviation_m"] > LANE_HALF_WIDTH:
            wrong_lane_time += dt

    total_time = float(raw_df["Timestamp"].iloc[-1]) - float(raw_df["Timestamp"].iloc[0])
    wrong_lane_pct = 100.0 * wrong_lane_time / total_time if total_time > 0 else float("nan")

    # Compute distance-weighted mean deviation so longer travelled segments contribute more.
    position_df["delta_x"] = position_df["Meters"].diff().abs()
    position_df = position_df.dropna().reset_index(drop=True)

    mdev = calculate_mdev(position_df)

    # Mark intervals where the shape task is active and attach the current shape depth to each sample.
    shape_intervals = []
    start_time = None
    current_shape = None

    position_df["shape_active"] = 0
    position_df["shape_depth"] = ""

    for _, row in raw_df.iterrows():
        if row["Col2"] == "Detect shape prompt by spacebar:":
            shape_text = row["Col4"] if pd.notna(row["Col4"]) else ""
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

    # Compute distance-weighted mean deviation during active shape-task periods.
    active_df = position_df[position_df["shape_active"] == 1]
    mdev_active = calculate_mdev(active_df)

    #Compute mdev for each shape depth for comparison
    mdev_rows = []

    for shape_depth, group in active_df.groupby("shape_depth"):
        mdev_rows.append({
            "shape_depth": shape_depth,
            "mdev": calculate_mdev(group)
        })

    mdev_by_shape = pd.DataFrame(mdev_rows, columns=["shape_depth", "mdev"])

    if not mdev_by_shape.empty:
        mdev_by_shape["mdev"] = mdev_by_shape["mdev"].round(4)

    shape_detection.extend(extract_shape_detection_events(raw_df, shape_intervals))
            
    print("Detected shapes: ",shape_detection)

    #Round all numeric data
    cols_to_round = ["Timestamp", "Meters", "LateralPos", "target_pos_smooth", "deviation_m"]
    position_df[cols_to_round] = position_df[cols_to_round].round(4)

    summary = {
        "missed_lane_changes": missed_lane_changes,
        "avg_lane_change_time": avg_lane_change_time,
        "wrong_lane_time": wrong_lane_time,
        "wrong_lane_pct": wrong_lane_pct,
        "mdev": mdev,
        "mdev_active": mdev_active,
        "shape_intervals": shape_intervals,
        "mdev_by_shape": mdev_by_shape,
    }

    return position_df, summary
    ################# End analyze_lct_data #################
    ########################################################

def draw_lct_plot(ax, position_df, summary, base_name, label_fs=10, tick_fs=10, title_fs=12, legend_fs=10, metrics_fs=10, show_metrics=True):
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

    for i, (start, end) in enumerate(summary["shape_intervals"]):
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
    ax.set_title(f"LCT Analysis: {base_name} (active mdev = {summary['mdev_active']:.3f} m)", fontsize=title_fs)

    metrics_text = (
        f"Missed: {summary['missed_lane_changes']}\n"
        f"Wrong lane: {summary['wrong_lane_pct']:.2f}%\n"
        f"Total mdev: {summary['mdev']:.3f} m\n"
        f"Avg lane change: {summary['avg_lane_change_time']:.2f} s"
    )

    if show_metrics:
        ax.text(
            0.02, 0.95,
            metrics_text,
            transform=ax.transAxes,
            fontsize=metrics_fs,
            verticalalignment="top",
            bbox=dict(boxstyle="round", facecolor="white", alpha=0.7)
        )


def build_plot_figure(position_df, summary, base_name, pdf_layout=False):
    if not pdf_layout:
        fig, ax = plt.subplots(figsize=(12, 4))
        draw_lct_plot(ax, position_df, summary, base_name)
        fig.tight_layout()
        return fig

    fig, (ax_text, ax_plot) = plt.subplots(
        2,
        1,
        figsize=(8.27, 11.69),
        gridspec_kw={"height_ratios": [0.8, 1.2]}
    )

    fig.subplots_adjust(hspace=0.45, top=0.95, bottom=0.45)

    summary_text = (
        f"\n\n"
        f"Total mdev: {summary['mdev']:.4f} metres\n"
        f"Active mdev: {summary['mdev_active']:.4f} metres\n"
        f"Missed lane changes: {summary['missed_lane_changes']}\n"
        f"Wrong-lane time: {summary['wrong_lane_time']:.3f} s\n"
        f"Percentage of time in wrong lane: {summary['wrong_lane_pct']:.2f}%\n"
        f"Average lane-change time: {summary['avg_lane_change_time']:.3f} s\n"
        f"\nmdev by shape depth:\n\n{summary['mdev_by_shape'].to_string(index=False)}\n\n"
    )

    ax_text.axis("off")
    ax_text.text(
        0.0, 0.95,
        f"Summary:    {base_name}\n",
        fontsize=14,
        fontweight="bold",
        ha="left",
        va="top",
        transform=ax_text.transAxes
    )

    ax_text.text(
        0.0, 0.82,
        summary_text,
        fontsize=12,
        ha="left",
        va="top",
        multialignment="left",
        transform=ax_text.transAxes
    )

    draw_lct_plot(
        ax_plot,
        position_df,
        summary,
        base_name,
        label_fs=8,
        tick_fs=7,
        title_fs=10,
        legend_fs=8,
        metrics_fs=8,
        show_metrics=False,
    )

    plot_pos = ax_plot.get_position()
    ax_plot.set_position([
        plot_pos.x0 + 0.04,
        plot_pos.y0 - 0.08,
        plot_pos.width - 0.08,
        plot_pos.height
    ])

    return fig

def build_pdf_summary_pages(shape_detection, statistics_by_shape_depth=None, include_reversal_thresholds=True):
    summary_lines = []

    def add_summary_line(line_text, bold=False):
        wrapped_lines = textwrap.wrap(
            line_text,
            width=100,
            subsequent_indent="    ",
            break_long_words=True,
            break_on_hyphens=False,
        )
        for wrapped_line in wrapped_lines or [line_text]:
            summary_lines.append((wrapped_line, bold))

    for detected, depth, duration in shape_detection:
        if duration is None:
            event_text = f"{detected}: {depth}"
        else:
            event_text = f"{detected}: {depth} ({duration:.2f}s)"

        add_summary_line(event_text)

    if include_reversal_thresholds:
        reversal_threshold_lines = build_reversal_threshold_lines(shape_detection)
        if reversal_threshold_lines:
            add_summary_line("")
            add_summary_line("Reversal Thresholds:", bold=True)
            for threshold_line in reversal_threshold_lines:
                if isinstance(threshold_line, tuple):
                    line_text, bold = threshold_line
                    add_summary_line(line_text, bold=bold)
                else:
                    add_summary_line(threshold_line)

    if not summary_lines:
        summary_lines = [("No shape detection events.", False)]

    lines_per_page = 58
    summary_chunks = [
        summary_lines[i:i + lines_per_page]
        for i in range(0, len(summary_lines), lines_per_page)
    ]
    summary_pages = []
    total_summary_pages = len(summary_chunks)

    for page_num, summary_chunk in enumerate(summary_chunks, start=1):
        summary_fig = plt.figure(figsize=(8.27, 11.69))
        page_title = "Staircase Method Summary"
        if total_summary_pages > 1:
            page_title = f"{page_title} ({page_num}/{total_summary_pages})"

        summary_fig.text(0.05, 0.95, page_title, fontsize=14, fontweight="bold", ha="left", va="top")
        line_height = 0.014
        for line_idx, (line_text, bold) in enumerate(summary_chunk):
            summary_fig.text(
                0.05,
                0.90 - (line_idx * line_height),
                line_text,
                ha="left",
                va="top",
                fontsize=8.5,
                family="monospace",
                fontweight="bold" if bold else "normal",
            )
        summary_pages.append(summary_fig)

    #List of depths detected during the run. TODO move to other analysis? 
    detected_depths = []
    prefix = "Square"
    for detected, depth, duration in shape_detection:
        if detected == "Detected" and depth.startswith(prefix):
            #Extract the depth value from the string in the log
            detected_depths.append(int(depth[len(prefix):len(prefix)+2]))
    
    mean_detected_depth = round(statistics.mean(detected_depths), 4) if detected_depths else None
    #TODO not really true though? Should be based on reversals otherwise skewed with first detections from 7 - 5. Threshold is the one above the reversal (if cant detect 2 then its 3 etc). Do later
    
    print("detected_depths: ", detected_depths)
    print("Mean detected depth: ", mean_detected_depth)

    detection_times_fig = plt.figure(figsize=(8.27, 11.69))
    detection_times_fig.text(0.05, 0.95, "Statistics by Shape Depth", fontsize=14, fontweight="bold", ha="left", va="top")

    if statistics_by_shape_depth is not None and not statistics_by_shape_depth.empty:
        statistics_by_shape_text = statistics_by_shape_depth.to_string(index=False)
    else:
        statistics_by_shape_text = "No statistics by shape depth data."

    detection_times_fig.text(0.05, 0.85, statistics_by_shape_text, ha="left", va="top", fontsize=9, family="monospace")
    mean_detected_depth_text = (
        f"Mean detected depth: {mean_detected_depth} mm"
        if mean_detected_depth is not None
        else "Mean detected depth: N/A"
    )
    detection_times_fig.text(0.05, 0.60, mean_detected_depth_text, fontweight="bold", ha="left", va="top")

    return *summary_pages, detection_times_fig

def write_csv_png(input_csv, position_df, summary, png_fig, figures_output_dir, processed_output_dir):
    input_dir = os.path.dirname(os.path.abspath(input_csv))
    base_name = os.path.splitext(os.path.basename(input_csv))[0]

    #Cleaned files contain only position data, no other logged events
    output_csv_path = os.path.join(processed_output_dir,"cleaned_pos", f"{base_name}_pos_only.csv")
    position_df.to_csv(output_csv_path, index=False)
    print(f"Wrote CSV file to: {output_csv_path}")

    png_output_path = os.path.join(figures_output_dir, f"{base_name}_graph.png")

    #Debug to zoom in graphs
    #png_fig.show()
    #plt.pause(0.1)
    #input("Inspect the plot, then press Enter to save the PNG...")

    png_fig.savefig(png_output_path, bbox_inches="tight", dpi=300)
    print(f"Wrote PNG file to: {png_output_path}")

def print_statistics(summary):
    print(f"Total mdev: {summary['mdev']:.4f} m")
    print(f"Active mdev: {summary['mdev_active']:.4f} m")
    print(f"Missed lane changes: {summary['missed_lane_changes']}")
    print(f"Wrong-lane time: {summary['wrong_lane_time']:.3f} s")
    print(f"Percentage of time in wrong lane: {summary['wrong_lane_pct']:.2f}%")
    print(f"Average lane-change time: {summary['avg_lane_change_time']:.3f} s")
    print("mdev by shape depth:")
    print(summary["mdev_by_shape"].to_string(index=False))

    print("Shape detection intervals:")
    for i, (start, end) in enumerate(summary["shape_intervals"], start=1):
        print(f"Interval {i}: {start} -> {end}")

def write_summary_to_csv(all_summaries, summary_csv_output_path):

    summary_cols = [
        "missed_lane_changes",
        "wrong_lane_time",
        "wrong_lane_pct",
        "mdev",
        "mdev_active",
    ]
    #Create pandas dataframe from summary, keep specified columns only
    all_summaries_df = pd.DataFrame(all_summaries)[summary_cols]
    all_summaries_df[summary_cols] = all_summaries_df[summary_cols].apply(pd.to_numeric, errors="coerce").round(4)

    #Insert participant ID as first column
    all_summaries_df.insert(0, "participant_id", participant_id)

    #Write file
    all_summaries_df.to_csv(summary_csv_output_path, index=False)
    print("Wrote summary to CSV: ", summary_csv_output_path)

def write_statistics_by_shape_depth_to_csv(statistics_by_shape_depth, output_path):
    statistics_output_df = statistics_by_shape_depth.copy()
    statistics_output_df.insert(0, "participant_id", participant_id)
    statistics_output_df.to_csv(output_path, index=False, float_format="%.4f")
    print("Wrote statistics by shape depth to CSV: ", output_path)

def build_threshold_detection_summary_df(shape_detection, expected_reversals=8):
    thresholds_by_reversal, mean_threshold = calculate_reversal_thresholds(
        shape_detection,
        expected_reversals=expected_reversals,
    )
    columns = ["participant_id"] + [
        f"reversal_{reversal_number}"
        for reversal_number in range(1, expected_reversals + 1)
    ] + ["mean_threshold"]

    threshold_row = {"participant_id": participant_id}
    for reversal_number in range(1, expected_reversals + 1):
        column_name = f"reversal_{reversal_number}"
        threshold_info = thresholds_by_reversal.get(reversal_number)
        threshold_row[column_name] = (
            round(threshold_info["threshold_mm"], 4)
            if threshold_info is not None
            else np.nan
        )

    threshold_row["mean_threshold"] = round(mean_threshold, 4) if mean_threshold is not None else np.nan

    return pd.DataFrame([threshold_row], columns=columns)

def write_threshold_detection_summary(shape_detection, csv_output_path):
    threshold_summary_df = build_threshold_detection_summary_df(shape_detection)
    threshold_summary_df.to_csv(csv_output_path, index=False, float_format="%.4f")
    print("Wrote threshold detection summary to CSV: ", csv_output_path)

##################################################
################### Main program #################
##################################################

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python graph_with_lanepos.py < ..\data\P_ID >")
        sys.exit(1)

    #Set input/output filepaths
    input_dir = Path(os.path.normpath(os.path.join(sys.argv[1], "processed")))

    if not  Path(os.path.normpath(sys.argv[1])).is_dir():
        raise FileNotFoundError(f"Directory not found: {sys.argv[1]}")
    
    print("input_dir: ", input_dir)

    figures_output_dir = os.path.normpath(os.path.join(input_dir, "..", "figures"))
    processed_output_dir = os.path.normpath(os.path.join(input_dir, "..", "processed"))
    cleaned_output_dir = os.path.normpath(os.path.join(processed_output_dir, "cleaned_pos"))

    participant_id = os.path.splitext(os.path.basename(sys.argv[1]))[0]
    print("participant_id: ", participant_id)

    os.makedirs(figures_output_dir, exist_ok=True)
    os.makedirs(processed_output_dir, exist_ok=True)
    os.makedirs(cleaned_output_dir, exist_ok=True)

    #Store list of detected and undetected shapes for each run, to write to summary file
    shape_detection = []

    #Get matching files
    pattern = "*.csv"
    input_files = sorted(input_dir.glob(pattern))
   
    #Process all files for the participant, store summary with graphs in single PDF, CSV for statistics
    summary_pdf_output_path = os.path.normpath(os.path.join(sys.argv[1], "Summary_graphs.pdf"))
    summary_csv_output_path = os.path.normpath(os.path.join(sys.argv[1], "Summary_stats.csv"))
    statistics_by_shape_depth_output_path = os.path.normpath(os.path.join(sys.argv[1], "statistics_by_shape_depth.csv"))
    threshold_detection_summary_output_path = os.path.normpath(os.path.join(sys.argv[1], "threshold_detection_summary.csv"))

    #Store all statistics for each run to CSV. To compare for full participant group later
    summary_all_runs = []
    
    with PdfPages(summary_pdf_output_path) as pdf:
        for input_file in input_files:
            print("Process file: ", input_file)
            base_name = os.path.splitext(os.path.basename(input_file))[0]
            #print("Base name: ", base_name)
            
            raw_df, position_df = load_lct_data(input_file)
            sign_positions = extract_sign_positions(raw_df, debug=True)
            position_df, summary = analyze_lct_data(raw_df, position_df,shape_detection, run_diagnostics=True)
            summary_all_runs.append(summary)
            #print_statistics(summary)

            png_fig = build_plot_figure(position_df, summary, base_name, pdf_layout=False)
            pdf_fig = build_plot_figure(position_df, summary, base_name, pdf_layout=True)
            write_csv_png(input_file, position_df, summary, png_fig, figures_output_dir, processed_output_dir)

            print(f"Added PDF page for: {base_name}")
            pdf.savefig(pdf_fig)
            plt.close(png_fig)
        
        statistics_by_shape_depth = build_statistics_by_shape_depth(shape_detection, summary_all_runs)
        print("\nStatistics by shape depth:")
        if statistics_by_shape_depth.empty:
            print("No statistics by shape depth data.")
        else:
            print(statistics_by_shape_depth.to_string(index=False))

        #Write staircase summary pages
        sum_pages = build_pdf_summary_pages(shape_detection, statistics_by_shape_depth=statistics_by_shape_depth)
        for sum_page in sum_pages:
            pdf.savefig(sum_page)
            plt.close(sum_page)

        #Write summary of all runs to CSV
        write_summary_to_csv(summary_all_runs, summary_csv_output_path)
        write_statistics_by_shape_depth_to_csv(statistics_by_shape_depth, statistics_by_shape_depth_output_path)
        write_threshold_detection_summary(
            shape_detection,
            threshold_detection_summary_output_path,
        )

        #TODO write overall summary page (total mdev avg for active/inactive, detection thresh)
        plt.close(pdf_fig)
            
    #print("Detected shapes total: ")
    #for shape in shape_detection:
    #    print(str(shape))

    print(f"Wrote combined PDF file to: {summary_pdf_output_path}")


