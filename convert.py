# json_to_xlsx.py
import json
import pandas as pd
from pathlib import Path

# Input and output filenames
in_path = Path("autogen-New.json")
out_path = Path("C:\\Users\\julius\\Downloads\\AmOption_rubric.csv")

# Load JSON
with open(in_path, "r", encoding="utf-8") as f:
    data = json.load(f)

# Flatten into a table
df = pd.json_normalize(data, sep=".")

# Save to CSV
df.to_csv(out_path, index=False)

print(f"Saved {out_path}")
