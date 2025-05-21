import os
import csv
import json
from PIL import Image
import numpy as np

# --- CONFIG ---
CSV_PATH = os.path.join(os.path.dirname(__file__), '../HRRRdata_nat/levels_extracted/fort_worth_levels_1_to_15_unity.csv')
IMG_FOLDER = os.path.join(os.path.dirname(__file__), '../HRRRdata_nat/levels_extracted_img_encoded')
LEVELS = range(1, 16)

# --- 1. Load CSV ---
csv_points = []
with open(CSV_PATH, newline='') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        lat = float(row['latitude'])
        lon = float(row['longitude'])
        csv_points.append((lat, lon))
print(f"CSV: {len(csv_points)} points")

# --- 2. Load images and meta, count valid points ---
img_points = []
for level in LEVELS:
    meta_path = os.path.join(IMG_FOLDER, f"fort_worth_level{level}_meta.json")
    img_path = os.path.join(IMG_FOLDER, f"fort_worth_level{level}_img.png")
    if not os.path.exists(meta_path) or not os.path.exists(img_path):
        print(f"Missing files for level {level}")
        continue
    with open(meta_path) as f:
        meta = json.load(f)
    img = Image.open(img_path)
    arr = np.array(img)
    num_lat, num_lon = arr.shape[:2]
    dLat = (meta['max_lat'] - meta['min_lat']) / (meta['num_lat'] - 1) if meta['num_lat'] > 1 else 0
    dLon = (meta['max_lon'] - meta['min_lon']) / (meta['num_lon'] - 1) if meta['num_lon'] > 1 else 0
    for y in range(num_lat):
        for x in range(num_lon):
            rgba = arr[y, x]
            if np.all(rgba == 0):
                continue  # skip missing
            lat = meta['min_lat'] + y * dLat
            lon = meta['min_lon'] + x * dLon
            img_points.append((lat, lon))
print(f"IMG: {len(img_points)} points")

# --- 3. Compare ---
csv_set = set((round(lat, 5), round(lon, 5)) for lat, lon in csv_points)
img_set = set((round(lat, 5), round(lon, 5)) for lat, lon in img_points)

print(f"Points in CSV not in IMG: {len(csv_set - img_set)}")
print(f"Points in IMG not in CSV: {len(img_set - csv_set)}")

if csv_set - img_set:
    print("Example CSV-only points:", list(csv_set - img_set)[:5])
if img_set - csv_set:
    print("Example IMG-only points:", list(img_set - csv_set)[:5]) 