import numpy as np
import requests
from io import BytesIO
import rasterio
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from mpl_toolkits.mplot3d import Axes3D

def get_elevation_data(bbox):
    """Get elevation data for a bounding box using USGS 3DEP API."""
    # USGS 3DEP API endpoint
    url = "https://elevation.nationalmap.gov/arcgis/rest/services/3DEPElevation/ImageServer/exportImage"
    
    # Parameters for the API request
    params = {
        "bbox": f"{bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]}",
        "bboxSR": "4326",  # WGS84
        "size": "1024,1024",
        "format": "tiff",
        "pixelType": "F32",
        "noDataInterpretation": "esriNoDataMatchAny",
        "interpolation": "BILINEAR",
        "f": "image"
    }
    
    print("Downloading elevation data...")
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        # Read the GeoTIFF data
        with BytesIO(response.content) as f:
            with rasterio.open(f) as src:
                elevation = src.read(1)
                return elevation
    except Exception as e:
        print(f"Error downloading elevation data: {e}")
        return None

def plot_elevation(elevation_data, bbox):
    """Create visualization of elevation data."""
    # Create figure with two subplots
    fig = plt.figure(figsize=(15, 6))
    
    # Create custom colormap for elevation
    colors = ['#313695', '#4575b4', '#74add1', '#abd9e9', '#e0f3f8', 
              '#ffffbf', '#fee090', '#fdae61', '#f46d43', '#d73027', '#a50026']
    cmap = LinearSegmentedColormap.from_list('elevation_cmap', colors)
    
    # Plot elevation map
    ax1 = fig.add_subplot(121)
    im1 = ax1.imshow(elevation_data, cmap=cmap, aspect='auto')
    ax1.set_title('Elevation Map')
    ax1.set_xlabel('Longitude')
    ax1.set_ylabel('Latitude')
    plt.colorbar(im1, ax=ax1, label='Elevation (meters)')
    
    # Plot 3D surface
    ax2 = fig.add_subplot(122, projection='3d')
    x = np.linspace(bbox[0], bbox[2], elevation_data.shape[1])
    y = np.linspace(bbox[1], bbox[3], elevation_data.shape[0])
    X, Y = np.meshgrid(x, y)
    
    # Downsample data for better 3D visualization
    stride = 20
    surf = ax2.plot_surface(X[::stride, ::stride], Y[::stride, ::stride], 
                           elevation_data[::stride, ::stride], cmap=cmap,
                           linewidth=0, antialiased=True)
    ax2.set_title('3D Surface')
    ax2.set_xlabel('Longitude')
    ax2.set_ylabel('Latitude')
    ax2.set_zlabel('Elevation (meters)')
    
    # Adjust layout and save
    plt.tight_layout()
    plt.savefig('fort_worth_elevation.png', dpi=300, bbox_inches='tight')
    print("Visualization saved to 'fort_worth_elevation.png'")

# Fort Worth bounding box (west, south, east, north)
fort_worth_bbox = (-97.648, 32.742, -96.898, 33.231)

# Get elevation data
elevation_data = get_elevation_data(fort_worth_bbox)

if elevation_data is not None:
    # Calculate statistics
    min_elev = np.min(elevation_data)
    max_elev = np.max(elevation_data)
    mean_elev = np.mean(elevation_data)
    
    # Calculate resolution
    lon_span = fort_worth_bbox[2] - fort_worth_bbox[0]  # degrees
    lat_span = fort_worth_bbox[3] - fort_worth_bbox[1]  # degrees
    
    # Resolution in degrees per pixel
    lon_res = lon_span / elevation_data.shape[1]
    lat_res = lat_span / elevation_data.shape[0]
    
    # Convert to meters (approximate at this latitude)
    # 1 degree of latitude ≈ 111,320 meters
    # 1 degree of longitude ≈ 111,320 * cos(latitude) meters
    lat_meters_per_degree = 111320
    lon_meters_per_degree = 111320 * np.cos(np.radians((fort_worth_bbox[1] + fort_worth_bbox[3]) / 2))
    
    lon_res_meters = lon_res * lon_meters_per_degree
    lat_res_meters = lat_res * lat_meters_per_degree
    
    print("\nElevation Statistics:")
    print(f"Minimum elevation: {min_elev:.2f} meters")
    print(f"Maximum elevation: {max_elev:.2f} meters")
    print(f"Mean elevation: {mean_elev:.2f} meters")
    print(f"\nData dimensions: {elevation_data.shape}")
    
    print("\nResolution:")
    print(f"Longitude resolution: {lon_res:.6f} degrees ({lon_res_meters:.2f} meters)")
    print(f"Latitude resolution: {lat_res:.6f} degrees ({lat_res_meters:.2f} meters)")
    
    # Print a sample 5x5 grid
    print("\nSample 5x5 grid of elevation data (meters):")
    print(elevation_data[:5, :5])
    
    # Create visualization
    print("\nCreating visualization...")
    plot_elevation(elevation_data, fort_worth_bbox)
    
    # Save to CSV
    print("\nSaving elevation data to CSV...")
    df = pd.DataFrame(elevation_data)
    df.to_csv('fort_worth_elevation.csv', index=True, header=True)
    print("Data saved to 'fort_worth_elevation.csv'")
else:
    print("Failed to download elevation data") 