from pathlib import Path
import pandas as pd
import os
import sys
import re
import matplotlib.pyplot as plt
import scipy.stats as stats


def participant_sort_value(participant_id):
    match = re.search(r"\d+", str(participant_id))
    return int(match.group(0)) if match else float("inf")


def sort_by_participant_id(df):
    return (
        df
        .assign(_participant_sort=df["participant_id"].map(participant_sort_value))
        .sort_values(["_participant_sort", "participant_id"])
        .drop(columns="_participant_sort")
        .reset_index(drop=True)
    )


def shape_depth_sort_value(shape_depth):
    match = re.search(r"\d+(?:\.\d+)?", str(shape_depth))
    return float(match.group(0)) if match else float("inf")


def sort_by_shape_depth(df):
    return (
        df
        .assign(_shape_depth_sort=df["shape_depth"].map(shape_depth_sort_value))
        .sort_values(["_shape_depth_sort", "shape_depth"])
        .drop(columns="_shape_depth_sort")
        .reset_index(drop=True)
    )


def write_participant_active_inactive_plot(group_df, output_dir):
    participant_means = (
        group_df
        .groupby("participant_id", as_index=False)[["active_mean", "inactive_mean"]]
        .mean()
        .round(4)
    )

    print("\nParticipant active/inactive mdev means:")
    print(participant_means.to_string(index=False))

    participant_means_csv_path = output_dir / "participant_active_inactive_means.csv"
    participant_means.to_csv(participant_means_csv_path, index=False)
    print(f"Wrote participant active/inactive means to: {participant_means_csv_path}")

    ax = participant_means.plot(
        x="participant_id",
        y=["inactive_mean", "active_mean"],
        kind="bar",
        figsize=(10, 6),
        width=0.8,
        color=["#5ea0ca", "#fea858"],
    )

    ax.set_xlabel("Participant ID")
    ax.set_ylabel("mdev")
    #ax.set_title("Active vs inactive mdev by participant")
    ax.legend(["Shape inactive mdev", "Shape active mdev"])
    plt.xticks(rotation=0)
    plt.tight_layout()

    plot_output_path = output_dir / "participant_active_inactive_mdev.png"
    plt.savefig(plot_output_path, dpi=300)
    plt.close()
    print(f"Wrote participant active/inactive mdev plot to: {plot_output_path}")

def write_group_threshold_detection_summary(threshold_detection_summary_files, output_dir):
    threshold_dfs = []

    for file in sorted(threshold_detection_summary_files, key=lambda path: participant_sort_value(path.parent.name)):
        threshold_df = pd.read_csv(file)
        if threshold_df.empty:
            continue

        threshold_dfs.append(threshold_df)

    if not threshold_dfs:
        print("\nNo usable threshold detection summary CSV files found.")
        return

    group_threshold_df = pd.concat(threshold_dfs, ignore_index=True)
    group_threshold_df = sort_by_participant_id(group_threshold_df)
    group_threshold_df = group_threshold_df[
        ["participant_id"] + [f"reversal_{i}" for i in range(1, 9)] + ["mean_threshold"]
    ]

    threshold_cols = [col for col in group_threshold_df.columns if col != "participant_id"]
    group_threshold_df[threshold_cols] = group_threshold_df[threshold_cols].apply(
        pd.to_numeric,
        errors="coerce",
    ).round(4)

    #Print to console
    print("\nThreshold detection summary:")
    print(group_threshold_df.to_string(index=False))

    #Calculate group mean and confidence interval. Take mean of all participant means, so equally weighted per participant (P6 has only 6 reversals)
    participant_means = pd.to_numeric(
    group_threshold_df["mean_threshold"],
    errors="coerce"
    ).dropna()

    n = len(participant_means)
    mean = participant_means.mean()
    sem = stats.sem(participant_means)

    ci_low, ci_high = stats.t.interval(
    confidence=0.95,
    df=n - 1,
    loc=mean,
    scale=sem
    )

    print(f"\nGroup mean: {mean:.4f}")
    print(f"95% CI: [{ci_low:.4f}, {ci_high:.4f}]")

    #Write to CSV
    combined_csv_path = output_dir / "threshold_detection_summary_combined.csv"
    group_threshold_df.to_csv(combined_csv_path, index=False, float_format="%.4f")
    print(f"\nWrote combined threshold detection summary to: {combined_csv_path}")

    #Create table and write to PNG
    display_df = group_threshold_df.copy()
    display_df.columns = ["ID"] + [f"Rev {i}" for i in range(1, 9)] + ["Mean"]
    display_df = display_df.fillna("")

    for col in display_df.columns[1:]:
        display_df[col] = display_df[col].apply(
            lambda value: "" if value == "" else f"{float(value):.4f}"
        )

    fig_height = max(2.0, 0.35 * len(display_df) + 0.8)
    fig, ax = plt.subplots(figsize=(9.5, fig_height))
    ax.axis("off")

    col_widths = [0.065] + [0.081] * 8 + [0.09]
    table = ax.table(
        cellText=display_df.values,
        colLabels=display_df.columns,
        cellLoc="center",
        colWidths=col_widths,
        loc="center",
    )
    table.auto_set_font_size(False)
    table.set_fontsize(7.5)
    table.scale(1, 1.3)

    for (row, col), cell in table.get_celld().items():
        cell.PAD = 0.02
        cell.set_edgecolor("#4a4a4a")
        cell.set_linewidth(0.6)
        if row == 0:
            cell.set_facecolor("#e8e8e8")
            cell.set_text_props(weight="bold")
        elif col == len(display_df.columns) - 1:
            cell.set_facecolor("#f5f5f5")
            cell.set_text_props(weight="bold")
        else:
            cell.set_facecolor("white")

    png_output_path = output_dir / "threshold_detection_summary_table.png"
    fig.savefig(png_output_path, bbox_inches="tight", dpi=300)
    plt.close(fig)
    print(f"Wrote group threshold detection summary table to: {png_output_path}")

def write_statistics_by_shape_depth_table_png(group_statistics_by_shape_depth_means, output_dir):
    # Prepare display labels and format numeric values consistently for the table image.
    display_df = group_statistics_by_shape_depth_means.copy()
    display_df.columns = ["Shape depth", "mdev", "Avg detection time", "Num detections"]
    display_df = display_df.fillna("")

    for col in display_df.columns[1:]:
        display_df[col] = display_df[col].apply(
            lambda value: "" if value == "" else f"{float(value):.4f}"
        )

    # Size the figure based on row count so the table remains readable as shapes are added.
    fig_height = max(2.0, 0.35 * len(display_df) + 0.8)
    fig, ax = plt.subplots(figsize=(7.5, fig_height))
    ax.axis("off")

    table = ax.table(
        cellText=display_df.values,
        colLabels=display_df.columns,
        cellLoc="center",
        colWidths=[0.24, 0.18, 0.32, 0.22],
        loc="center",
    )
    table.auto_set_font_size(False)
    table.set_fontsize(8)
    table.scale(1, 1.3)

    # Apply simple publication-friendly styling: bold header, light borders, compact padding.
    for (row, col), cell in table.get_celld().items():
        cell.PAD = 0.02
        cell.set_edgecolor("#4a4a4a")
        cell.set_linewidth(0.6)
        if row == 0:
            cell.set_facecolor("#e8e8e8")
            cell.set_text_props(weight="bold")
        else:
            cell.set_facecolor("white")

    png_output_path = output_dir / "statistics_by_shape_depth_group_means_table.png"
    fig.savefig(png_output_path, bbox_inches="tight", dpi=300)
    plt.close(fig)
    print(f"Wrote group means by shape depth table to: {png_output_path}")

def write_statistics_by_shape_depth_plot_png(group_statistics_by_shape_depth_df, output_dir):
    def confidence_interval_95(values):
        values = values.dropna()
        if len(values) < 2:
            return 0.0
        return stats.t.ppf(0.975, len(values) - 1) * stats.sem(values)

    plot_df = (
        group_statistics_by_shape_depth_df
        .groupby("shape_depth")
        .agg(
            mdev=("mdev", "mean"),
            mdev_ci=("mdev", confidence_interval_95),
            avg_detection_time=("avg_detection_time", "mean"),
            avg_detection_time_ci=("avg_detection_time", confidence_interval_95),
        )
        .reset_index()
        .round(4)
    )
    plot_df = sort_by_shape_depth(plot_df)
    plot_df = plot_df.iloc[::-1].reset_index(drop=True)

    x_positions = list(range(len(plot_df)))
    fig, ax_mdev = plt.subplots(figsize=(8, 5))
    ax_detection_time = ax_mdev.twinx()

    mdev_plot = ax_mdev.errorbar(
        x_positions,
        plot_df["mdev"],
        yerr=plot_df["mdev_ci"],
        marker="o",
        capsize=4,
        label="mdev",
        color="#5ea0ca",
    )
    detection_time_plot = ax_detection_time.errorbar(
        x_positions,
        plot_df["avg_detection_time"],
        yerr=plot_df["avg_detection_time_ci"],
        marker="o",
        capsize=4,
        label="Avg detection time",
        color="#fea858",
    )

    ax_mdev.set_xlabel("Shape depth")
    ax_mdev.set_ylabel("mdev")
    ax_detection_time.set_ylabel("Avg detection time")
    ax_mdev.xaxis.label.set_weight("bold")
    ax_mdev.yaxis.label.set_weight("bold")
    ax_detection_time.yaxis.label.set_weight("bold")
    ax_mdev.set_xticks(x_positions)
    ax_mdev.set_xticklabels(plot_df["shape_depth"])
    ax_mdev.legend(
        [mdev_plot, detection_time_plot],
        ["mdev", "Avg detection time"],
        loc="upper left",
    )

    fig.tight_layout()

    png_output_path = output_dir / "statistics_by_shape_depth_group_means_plot.png"
    fig.savefig(png_output_path, dpi=300)
    plt.close(fig)
    print(f"Wrote group means by shape depth plot to: {png_output_path}")

def write_group_statistics_by_shape_depth(statistics_by_shape_depth_files, output_dir):
    statistics_dfs = []

    for file in sorted(statistics_by_shape_depth_files, key=lambda path: participant_sort_value(path.parent.name)):
        statistics_df = pd.read_csv(file)
        if statistics_df.empty:
            continue

        statistics_dfs.append(statistics_df)

    if not statistics_dfs:
        print("\nNo usable statistics by shape depth CSV files found.")
        return

    group_statistics_by_shape_depth_df = pd.concat(statistics_dfs, ignore_index=True)
    group_statistics_by_shape_depth_df = sort_by_participant_id(group_statistics_by_shape_depth_df)

    numeric_cols = [
        col
        for col in group_statistics_by_shape_depth_df.columns
        if col not in ["participant_id", "shape_depth"]
    ]
    group_statistics_by_shape_depth_df[numeric_cols] = group_statistics_by_shape_depth_df[numeric_cols].apply(
        pd.to_numeric,
        errors="coerce",
    )

    combined_csv_path = output_dir / "statistics_by_shape_depth_combined.csv"
    group_statistics_by_shape_depth_df.to_csv(combined_csv_path, index=False, float_format="%.4f")
    print(f"\nWrote combined statistics by shape depth to: {combined_csv_path}")

    group_statistics_by_shape_depth_means = (
        group_statistics_by_shape_depth_df
        .groupby("shape_depth", as_index=False)[numeric_cols]
        .mean()
        .round(4)
    )
    group_statistics_by_shape_depth_means = sort_by_shape_depth(group_statistics_by_shape_depth_means)

    print("\nGroup means by shape depth:")
    print(group_statistics_by_shape_depth_means.to_string(index=False))

    means_csv_path = output_dir / "statistics_by_shape_depth_group_means.csv"
    group_statistics_by_shape_depth_means.to_csv(means_csv_path, index=False, float_format="%.4f")
    print(f"Wrote group means by shape depth to: {means_csv_path}")

    write_statistics_by_shape_depth_table_png(group_statistics_by_shape_depth_means, output_dir)
    write_statistics_by_shape_depth_plot_png(group_statistics_by_shape_depth_df, output_dir)

#Root dir is "data" with all participants directories inside. Iterate over these to build summary
root_dir = Path(os.path.normpath(os.path.join(os.getcwd(), "..", "data", "Main_study")))
summary_output_dir = Path(os.path.join(os.getcwd(),"..", "Summary"))
os.makedirs(summary_output_dir, exist_ok=True)


#Match on this filename for each participant
summary_pattern = "Summary_stats.csv"
statistics_by_shape_depth_pattern = "statistics_by_shape_depth.csv"
threshold_detection_summary_pattern = "threshold_detection_summary.csv"

summary_files = []
statistics_by_shape_depth_files = []
threshold_detection_summary_files = []

for participant_dir in root_dir.iterdir():
    if not participant_dir.is_dir():
        continue

    matches = list(participant_dir.glob(summary_pattern))
    summary_files.extend(matches)

    statistics_by_shape_depth_matches = list(participant_dir.glob(statistics_by_shape_depth_pattern))
    statistics_by_shape_depth_files.extend(statistics_by_shape_depth_matches)

    threshold_detection_summary_matches = list(participant_dir.glob(threshold_detection_summary_pattern))
    threshold_detection_summary_files.extend(threshold_detection_summary_matches)

if not summary_files:
    raise FileNotFoundError("No participant summary CSV files found.")

summary_files = sorted(summary_files, key=lambda path: participant_sort_value(path.parent.name))
print("Found summary files:")
print("\n".join(str(path) for path in summary_files))

all_dfs = [pd.read_csv(file) for file in summary_files]
group_df = pd.concat(all_dfs, ignore_index=True)
group_df = sort_by_participant_id(group_df)
#Disable, columns no longer exist. Keep for use when have mdev calc sorted
#group_df["active_mean"] = pd.to_numeric(group_df["active_mean"], errors="coerce")
#group_df["inactive_mean"] = pd.to_numeric(group_df["inactive_mean"], errors="coerce")

# Write combined table with all data
combined_csv_path = summary_output_dir / "group_summary_combined.csv"
group_df.to_csv(combined_csv_path, index=False)
print(f"Wrote combined summary to: {combined_csv_path}")

#write_participant_active_inactive_plot(group_df, summary_output_dir)

# Compute means of numeric columns
group_means = group_df.mean(numeric_only=True).round(4)
print("\nOverall group means:")
print(group_means)

# Save means as CSV
group_means_df = group_means.reset_index()
group_means_df.columns = ["metric", "mean"]
group_means_csv_path = summary_output_dir / "group_summary_means.csv"
group_means_df.to_csv(group_means_csv_path, index=False)
print(f"Wrote group means to: {group_means_csv_path}")

if not statistics_by_shape_depth_files:
    print("\nNo participant statistics by shape depth CSV files found.")
else:
    statistics_by_shape_depth_files = sorted(
        statistics_by_shape_depth_files,
        key=lambda path: participant_sort_value(path.parent.name),
    )
    print("\nFound statistics by shape depth files:")
    print("\n".join(str(path) for path in statistics_by_shape_depth_files))
    write_group_statistics_by_shape_depth(statistics_by_shape_depth_files, summary_output_dir)

if not threshold_detection_summary_files:
    print("\nNo participant threshold detection summary CSV files found.")
else:
    print("\n".join(str(path) for path in sorted(threshold_detection_summary_files, key=lambda path: participant_sort_value(path.parent.name))))
    write_group_threshold_detection_summary(threshold_detection_summary_files, summary_output_dir)
