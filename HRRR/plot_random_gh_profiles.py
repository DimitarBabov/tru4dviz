import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Load the CSV
csv_path = "HRRRdata_nat/levels_extracted/fort_worth_gh_levels.csv"
df = pd.read_csv(csv_path)

# Identify gh columns and extract level numbers
gh_cols = [col for col in df.columns if col.startswith("gh[gpm]_lev")]
levels = [int(col.split("_lev")[1]) for col in gh_cols]
sorted_indices = np.argsort(levels)
gh_cols_sorted = [gh_cols[i] for i in sorted_indices]
levels_sorted = [levels[i] for i in sorted_indices]

# Randomly select 5 rows
np.random.seed(42)  # for reproducibility
selected_rows = df.sample(n=5, random_state=42)

# Plot
grid_labels = []
plt.figure(figsize=(10, 6))
for idx, (_, row) in enumerate(selected_rows.iterrows()):
    gh_profile = row[gh_cols_sorted].values
    label = f'Grid point {idx+1} (lat={row.latitude:.3f}, lon={row.longitude:.3f})'
    plt.plot(levels_sorted, gh_profile, marker='o', label=label)
    grid_labels.append(label)

plt.xlabel('Model Level')
plt.ylabel('Geopotential Height [gpm]')
plt.title('Randomly Selected Geopotential Height Profiles')
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.xlim(0, max(50, max(levels_sorted)))
plt.savefig("random_gh_profiles.png", dpi=200)
print("Plot saved as random_gh_profiles.png") 