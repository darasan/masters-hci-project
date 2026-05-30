import pandas as pd
import matplotlib.pyplot as plt

csv_path = r"C:\HCI_project\Lane-Change-Test-main\Logs\MainStudy\Summary\Charts.csv"

# Load data
df = pd.read_csv(csv_path)

# Convert Run labels like R1, R2, ... into numeric values for plotting
df["RunNumber"] = df["run"].str.extract(r"R(\d+)").astype(int)

# Ensure lines are drawn in run order within each participant
df = df.sort_values(["participant_id", "RunNumber"])

# Plot one line per participant
plt.figure(figsize=(10, 6))

for participant_id, group in df.groupby("participant_id"):
    plt.plot(
        group["RunNumber"],
        group["delta_mdev"],
        marker="o",
        linewidth=1.5,
        label=participant_id
    )

# Axis formatting
all_runs = sorted(df["RunNumber"].unique())
plt.xticks(all_runs, [f"R{n}" for n in all_runs], rotation=45)

plt.xlabel("Run ID")
plt.ylabel("delta mdev")
plt.title("Delta MDEV by run per participant")
plt.grid(True, alpha=0.3)
plt.legend(title="Participant")
plt.tight_layout()
plt.show()
