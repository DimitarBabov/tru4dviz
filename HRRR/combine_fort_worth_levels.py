import os
import glob
import pandas as pd

# Directory containing the level CSVs
LEVELS_DIR = os.path.join(os.path.dirname(__file__), '../HRRRdata_nat/levels_extracted')
# Output file
OUTPUT_CSV = os.path.join(LEVELS_DIR, 'fort_worth_all_levels_combined.csv')

# Find all level CSVs and sort by level number
csv_files = glob.glob(os.path.join(LEVELS_DIR, 'fort_worth_level*_params.csv'))
csv_files = sorted(csv_files, key=lambda x: int(os.path.basename(x).split('_')[2][5:]))

# Concatenate all rows (no header)
with open(OUTPUT_CSV, 'w') as fout:
    for i, csv_file in enumerate(csv_files):
        with open(csv_file, 'r') as fin:
            lines = fin.readlines()
            # Skip header (first line) in each file
            lines = lines[1:]
            for line in lines:
                fout.write(line)
print(f"Combined CSV written to {OUTPUT_CSV}") 