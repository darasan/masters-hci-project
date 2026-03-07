import pandas as pd
import matplotlib.pyplot as plt

# Load CSV
df = pd.read_csv("..\..\Logs\plottest1.csv")

# Print columns so we can verify structure
print("Columns in file:", df.columns)

# Rename columns if needed
df.columns = ["timestamp", "meters", "currentLane", "targetLane"]

# Convert to numeric just in case
df["timestamp"] = pd.to_numeric(df["timestamp"], errors="coerce")
df["meters"] = pd.to_numeric(df["meters"], errors="coerce")
df["currentLane"] = pd.to_numeric(df["currentLane"], errors="coerce")
df["targetLane"] = pd.to_numeric(df["targetLane"], errors="coerce")

# Remove any invalid rows
df = df.dropna()

# Plot
plt.figure(figsize=(12,4))

plt.step(
    df["timestamp"],
    df["currentLane"],
    where="post",
    label="Driver Lane"
)

plt.step(
    df["timestamp"],
    df["targetLane"],
    where="post",
    label="Target Lane"
)

plt.yticks([-1,0,1], ["Left","Center","Right"])

plt.xlabel("Time (seconds)")
plt.ylabel("Lane")
plt.title("Lane Change Test Timeline")

plt.legend()
plt.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig("lane_plot.png", dpi=300)

plt.show()

