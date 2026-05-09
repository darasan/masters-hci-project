from pathlib import Path
import pandas as pd
import os
import sys

#Root dir is "data" with all participants directories inside. Iterate over these to build summary
root_dir = Path(os.path.normpath(os.path.join(os.getcwd(), "..", "data")))
summary_output_dir = Path(os.path.join(os.getcwd(),"..", "Summary"))
os.makedirs(summary_output_dir, exist_ok=True)

#print("root_dir: ", root_dir)

#Match on this filename for each participant
summary_pattern = "Summary_stats.csv"

summary_files = []

for participant_dir in root_dir.iterdir():
    if not participant_dir.is_dir():
        continue

    matches = list(participant_dir.glob(summary_pattern))
    summary_files.extend(matches)

if not summary_files:
    raise FileNotFoundError("No participant summary CSV files found.")

summary_files = sorted(summary_files)
print("Found summary files:")
print("\n".join(str(path) for path in summary_files))

all_dfs = [pd.read_csv(file) for file in summary_files]
group_df = pd.concat(all_dfs, ignore_index=True)


# Write combined table with all data
combined_csv_path = summary_output_dir / "group_summary_combined.csv"
group_df.to_csv(combined_csv_path, index=False)
print(f"Wrote combined summary to: {combined_csv_path}")

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
