import os
import sys
import csv
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import numpy as np
from pathlib import Path


LANE_CHANGE_DURATION = 4.0
SIGMOID_STEEPNESS = 8
LANE_HALF_WIDTH = 4.2
POSITION_COLUMNS = ["Timestamp", "Meters", "LateralPos", "currentLane", "targetLane"]


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


def analyze_lct_data(raw_df, position_df, run_diagnostics=True):
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

    total_distance = position_df["delta_x"].sum()
    weighted_deviation = (position_df["deviation_m"] * position_df["delta_x"]).sum()
    mdev = weighted_deviation / total_distance if total_distance > 0 else float("nan")

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

    # Summarize deviation overall during active/inactive periods and by active shape depth.
    active = position_df[position_df["shape_active"] == 1]["deviation_m"]
    inactive = position_df[position_df["shape_active"] == 0]["deviation_m"]

    shape_active_df = position_df[position_df["shape_active"] == 1]
    mdev_by_shape = (
        shape_active_df.groupby("shape_depth")
        .apply(
            lambda g: ((g["deviation_m"] * g["delta_x"]).sum() / g["delta_x"].sum())
            if g["delta_x"].sum() > 0 else np.nan
        )
        .reset_index(name="mdev")
    )
    mdev_by_shape["mdev"] = mdev_by_shape["mdev"].round(4)

    cols_to_round = ["Timestamp", "Meters", "LateralPos", "target_pos_smooth", "deviation_m"]
    position_df[cols_to_round] = position_df[cols_to_round].round(4)

    summary = {
        "missed_lane_changes": missed_lane_changes,
        "avg_lane_change_time": avg_lane_change_time,
        "wrong_lane_time": wrong_lane_time,
        "wrong_lane_pct": wrong_lane_pct,
        "mdev": mdev,
        "shape_intervals": shape_intervals,
        "active_mean": active.mean(),
        "inactive_mean": inactive.mean(),
        "mdev_by_shape": mdev_by_shape,
    }

    return position_df, summary


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
    ax.set_title(f"LCT Analysis: {base_name} (mdev = {summary['mdev']:.3f} m)", fontsize=title_fs)

    metrics_text = (
        f"Missed: {summary['missed_lane_changes']}\n"
        f"Wrong lane: {summary['wrong_lane_pct']:.2f}%\n"
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
        f"Total mdev: {summary['mdev']:.4f} metres\n"
        f"Missed lane changes: {summary['missed_lane_changes']}\n"
        f"Wrong-lane time: {summary['wrong_lane_time']:.3f} s\n"
        f"Percentage of time in wrong lane: {summary['wrong_lane_pct']:.2f}%\n"
        f"Average lane-change time: {summary['avg_lane_change_time']:.3f} s\n"
        f"Active mean: {summary['active_mean']:.3f}\n"
        f"Inactive mean: {summary['inactive_mean']:.3f}\n"
        f"mdev by shape depth:\n{summary['mdev_by_shape'].to_string(index=False)}"
    )

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
        plot_pos.y0,
        plot_pos.width - 0.08,
        plot_pos.height
    ])

    return fig


def write_csv_png(input_csv, position_df, summary, png_fig, figures_output_dir, processed_output_dir):
    input_dir = os.path.dirname(os.path.abspath(input_csv))
    base_name = os.path.splitext(os.path.basename(input_csv))[0]

    output_csv_path = os.path.join(processed_output_dir,"cleaned", f"{base_name}_clean.csv")
    position_df.to_csv(output_csv_path, index=False)
    print(f"Wrote CSV file to: {output_csv_path}")

    png_output_path = os.path.join(figures_output_dir, f"{base_name}_graph.png")
    png_fig.savefig(png_output_path, bbox_inches="tight", dpi=300)
    print(f"Wrote PNG file to: {png_output_path}")

def print_statistics(summary):
    print(f"Total mdev: {summary['mdev']:.4f} m")
    print(f"Missed lane changes: {summary['missed_lane_changes']}")
    print(f"Wrong-lane time: {summary['wrong_lane_time']:.3f} s")
    print(f"Percentage of time in wrong lane: {summary['wrong_lane_pct']:.2f}%")
    print(f"Average lane-change time: {summary['avg_lane_change_time']:.3f} s")
    print(f"Active mean: {summary['active_mean']:.3f}")
    print(f"Inactive mean: {summary['inactive_mean']:.3f}")
    print("mdev by shape depth:")
    print(summary["mdev_by_shape"].to_string(index=False))

    print("Shape detection intervals:")
    for i, (start, end) in enumerate(summary["shape_intervals"], start=1):
        print(f"Interval {i}: {start} -> {end}")

##################################################
################### Main program #################
##################################################

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python graph_with_lanepos.py <..\data\P_ID")
        sys.exit(1)

    #Set input/output filepaths
    input_dir = Path(os.path.normpath(os.path.join(sys.argv[1], "processed")))
    print("input_dir: ", input_dir)

    figures_output_dir = os.path.normpath(os.path.join(input_dir, "..", "figures"))
    processed_output_dir = os.path.normpath(os.path.join(input_dir, "..", "processed"))
    cleaned_output_dir = os.path.normpath(os.path.join(processed_output_dir, "cleaned"))

    os.makedirs(figures_output_dir, exist_ok=True)
    os.makedirs(processed_output_dir, exist_ok=True)
    os.makedirs(cleaned_output_dir, exist_ok=True)

    #Get matching files
    pattern = "*.csv"
    input_files = sorted(input_dir.glob(pattern))
   
    #Process all files for the participant, store summary with graphs in single PDF
    pdf_output_path = os.path.normpath(os.path.join(sys.argv[1], "Summary.pdf"))
    
    with PdfPages(pdf_output_path) as pdf:
        for input_file in input_files:
            print("Process file: ", input_file)
            base_name = os.path.splitext(os.path.basename(input_file))[0]
            #print("Base name: ", base_name)
            
            raw_df, position_df = load_lct_data(input_file)
            position_df, summary = analyze_lct_data(raw_df, position_df, run_diagnostics=True)
            #print_statistics(summary)

            png_fig = build_plot_figure(position_df, summary, base_name, pdf_layout=False)
            pdf_fig = build_plot_figure(position_df, summary, base_name, pdf_layout=True)
            write_csv_png(input_file, position_df, summary, png_fig, figures_output_dir, processed_output_dir)

            print(f"Added PDF page for: {base_name}")
            pdf.savefig(pdf_fig)
            plt.close(png_fig)
            plt.close(pdf_fig)

    print(f"Wrote combined PDF file to: {pdf_output_path}")

