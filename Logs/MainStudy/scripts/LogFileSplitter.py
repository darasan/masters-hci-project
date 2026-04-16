import sys
import csv
import os
import pandas as pd

# Check for input argument
if len(sys.argv) < 2:
    print("Usage: LogFileSplitter.py <input_csv>")
    sys.exit(1)

input_csv = sys.argv[1]

# Validate input file
if not os.path.isfile(input_csv):
    print(f"Error: File not found -> {input_csv}")
    sys.exit(1)

# Prepare paths
input_dir = os.path.dirname(os.path.abspath(input_csv))
base_name = os.path.splitext(os.path.basename(input_csv))[0]
output_dir = os.path.normpath(os.path.join(input_dir, "..", "processed"))
os.makedirs(output_dir, exist_ok=True)

print("base name: ", base_name)

#Find header row and check valid
expected_cols = ["Meters", "LateralPos", "currentLane", "targetLane"]
header_row_idx = None

with open(input_csv, "r", encoding="utf-8", errors="replace") as f:
    reader = csv.reader(f)
    for i, row in enumerate(reader):
        # Ensure enough columns
        if len(row) >= 5:
            # Compare columns 2–5 (index 1–4)
            if [col.strip() for col in row[1:5]] == expected_cols:
                header_row_idx = i
                break

if header_row_idx is None:
    raise ValueError("Could not find header row based on expected columns")

# Keep the first 2 rows as metadata for each output file
metadata_rows = pd.read_csv(input_csv, nrows=2, header=None)

# Read file, skip rows before valid header
df = pd.read_csv(input_csv, skiprows=header_row_idx, header=0)

# Use the second real column as the log column, first is timestamp
log_col = df.columns[1]

# Define end marker to split each run
end_marker = "Reached end of test (finish line)"
end_mask = df[log_col].astype("string").str.contains(end_marker, regex=False, na=False)

end_indices = df.index[end_mask].tolist()
print("Found markers at rows: ", end_indices)

if not end_indices:
    raise ValueError(f'No end marker found in column "{log_col}"')

run_count = 1
start_idx = 0

for end_idx in end_indices:
    run_df = df.loc[start_idx:end_idx]

    output_filename = f"{base_name}_run{run_count}.csv"
    output_path = os.path.join(output_dir, output_filename)

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        metadata_rows.to_csv(f, index=False, header=False)
        run_df.to_csv(f, index=False)

    print(f"Saved: {output_path}")

    run_count += 1
    start_idx = end_idx + 1
