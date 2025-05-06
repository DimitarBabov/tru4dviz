import geopandas as gpd
from shapely.geometry import box
import matplotlib.pyplot as plt
from matplotlib import rcParams

def generate_map(lat_min, lat_max, lon_min, lon_max, 
                 countries_shapefile, states_shapefile, cities_shapefile, output_file='map.png'):
    # Load the shapefiles
    world = gpd.read_file(countries_shapefile)     # Countries
    states = gpd.read_file(states_shapefile)       # States/Provinces
    cities = gpd.read_file(cities_shapefile)       # Populated Places (cities)
    
    # Define the bounding box using shapely's box function
    bounding_box = gpd.GeoDataFrame({'geometry': [box(lon_min, lat_min, lon_max, lat_max)]}, crs="EPSG:4326")

    # Clip datasets to the bounding box
    world_clipped = gpd.clip(world, bounding_box)
    states_clipped = gpd.clip(states, bounding_box)
    cities_clipped = gpd.clip(cities, bounding_box)

    # Set the figure background to black
    fig, ax = plt.subplots(figsize=(12, 10), facecolor='black')

    # Plot countries with white boundary lines
    world_clipped.boundary.plot(ax=ax, linewidth=1.0, edgecolor='white')

    # Plot states/provinces with dashed white lines
    states_clipped.boundary.plot(ax=ax, linewidth=0.5, edgecolor='white', linestyle='--')

    # Plot cities (populated places) with white points
    cities_clipped.plot(ax=ax, color='white', markersize=10)

    # Add city names in white
    for x, y, label in zip(cities_clipped.geometry.x, cities_clipped.geometry.y, cities_clipped['NAME']):
        ax.text(x, y, label, fontsize=9, ha='right', color='white')

    # Remove axes, grid, and background colors
    ax.set_axis_off()

    # Set the limits of the map to the lat/lon boundaries
    ax.set_xlim(lon_min, lon_max)
    ax.set_ylim(lat_min, lat_max)

    # Save the plot as a PNG file with a black background
    plt.savefig(output_file, dpi=300, bbox_inches='tight', pad_inches=0, facecolor='black')
    plt.close()

# Example usage: adjust the paths to match your local files
generate_map(lat_min=20, lat_max=55, lon_min=-130, lon_max=-60, 
             countries_shapefile='map_data/110m_cultural/ne_110m_admin_0_countries.shp',
             states_shapefile='map_data/110m_cultural/ne_110m_admin_1_states_provinces.shp',
             cities_shapefile='map_data/110m_cultural/ne_110m_populated_places.shp',
             output_file='usa_map_black_background.png')
