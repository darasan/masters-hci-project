from pathlib import Path
import pandas as pd
import os
import sys
import matplotlib.pyplot as plt


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

#Root dir is "data" with all participants directories inside. Iterate over these to build summary
root_dir = Path(os.path.normpath(os.path.join(os.getcwd(), "..", "data")))
summary_output_dir = Path(os.path.join(os.getcwd(),"..", "Summary"))
os.makedirs(summary_output_dir, exist_ok=True)

#print("root_dir: ", root_dir)

#Match on this filename for each participant
summary_pattern = "Summary_stats.csv"
shape_detection_times_pattern = "Shape_detection_times.csv"

summary_files = []
shape_detection_times_files = []

for participant_dir in root_dir.iterdir():
    if not participant_dir.is_dir():
        continue

    matches = list(participant_dir.glob(summary_pattern))
    summary_files.extend(matches)

    shape_detection_times_matches = list(participant_dir.glob(shape_detection_times_pattern))
    shape_detection_times_files.extend(shape_detection_times_matches)

if not summary_files:
    raise FileNotFoundError("No participant summary CSV files found.")

summary_files = sorted(summary_files)
print("Found summary files:")
print("\n".join(str(path) for path in summary_files))

all_dfs = [pd.read_csv(file) for file in summary_files]
group_df = pd.concat(all_dfs, ignore_index=True)
group_df["active_mean"] = pd.to_numeric(group_df["active_mean"], errors="coerce")
group_df["inactive_mean"] = pd.to_numeric(group_df["inactive_mean"], errors="coerce")


# Write combined table with all data
combined_csv_path = summary_output_dir / "group_summary_combined.csv"
group_df.to_csv(combined_csv_path, index=False)
print(f"Wrote combined summary to: {combined_csv_path}")

write_participant_active_inactive_plot(group_df, summary_output_dir)

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

if not shape_detection_times_files:
    print("\nNo participant shape detection time CSV files found.")
else:
    shape_detection_times_files = sorted(shape_detection_times_files)
    print("\nFound shape detection time files:")
    print("\n".join(str(path) for path in shape_detection_times_files))

    shape_detection_times_dfs = [pd.read_csv(file) for file in shape_detection_times_files]
    group_shape_detection_times_df = pd.concat(shape_detection_times_dfs, ignore_index=True)

    combined_shape_detection_times_csv_path = summary_output_dir / "group_shape_detection_times_combined.csv"
    group_shape_detection_times_df.to_csv(combined_shape_detection_times_csv_path, index=False)
    print(f"Wrote combined shape detection times to: {combined_shape_detection_times_csv_path}")

    group_shape_detection_times_df["weighted_detection_time"] = (
        group_shape_detection_times_df["avg_detection_time"]
        * group_shape_detection_times_df["num_detections"]
    )

    group_shape_detection_times = (
        group_shape_detection_times_df
        .groupby("shape_type", as_index=False)
        .agg(
            total_detection_time=("weighted_detection_time", "sum"),
            total_detections=("num_detections", "sum"),
            num_participants=("participant_id", "nunique"),
        )
    )

    group_shape_detection_times["group_avg_detection_time"] = (
        group_shape_detection_times["total_detection_time"]
        / group_shape_detection_times["total_detections"]
    )

    group_shape_detection_times = group_shape_detection_times[
        ["shape_type", "group_avg_detection_time", "total_detections", "num_participants"]
    ].round(4)

    print("\nGroup average detection time by shape type:")
    print(group_shape_detection_times.to_string(index=False))

    group_shape_detection_times_csv_path = summary_output_dir / "group_shape_detection_times_means.csv"
    group_shape_detection_times.to_csv(group_shape_detection_times_csv_path, index=False)
    print(f"Wrote group shape detection times to: {group_shape_detection_times_csv_path}")
