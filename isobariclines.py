import os
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image
from scipy.ndimage import gaussian_filter
from scipy.interpolate import griddata
from fetch_gfs_data import PNG_DIR

# Load the PNG as a numpy array (assumed to represent pressure or scalar values)
def load_scalar_field(file_path):
    with Image.open(file_path) as img:
        img = img.convert('L')  # Convert to grayscale
        return np.array(img, dtype=np.float32) / 255.0  # Normalize to [0, 1] range

# Apply a Gaussian filter to smooth the scalar field
def smooth_data(data, sigma=2):
    return gaussian_filter(data, sigma=sigma)

# Interpolate the scalar field to a higher resolution grid
def interpolate_data(data, new_shape):
    x = np.linspace(0, data.shape[1] - 1, data.shape[1])
    y = np.linspace(0, data.shape[0] - 1, data.shape[0])
    X, Y = np.meshgrid(x, y)

    xi = np.linspace(0, data.shape[1] - 1, new_shape[1])
    yi = np.linspace(0, data.shape[0] - 1, new_shape[0])
    XI, YI = np.meshgrid(xi, yi)

    data_interp = griddata((X.flatten(), Y.flatten()), data.flatten(), (XI, YI), method='linear')
    return data_interp

# Generate isobaric lines (contours) from the scalar field (pressure data)
def generate_isobaric_plot(scalar_field, output_file):
    x = np.linspace(0, scalar_field.shape[1] - 1, scalar_field.shape[1])
    y = np.linspace(0, scalar_field.shape[0] - 1, scalar_field.shape[0])
    X, Y = np.meshgrid(x, y)

    # Create a figure
    plt.figure(figsize=(20.48, 10.24), dpi=100)

    # Plot contour lines (isobaric lines) with increased levels and smoothing
    contours = plt.contour(X, Y, scalar_field, levels=20, colors='white', linewidths=0.75)
    
    plt.axis('off')

    # Save the output to a PNG file
    plt.gca().set_xlim([0, scalar_field.shape[1]])
    plt.gca().set_ylim([0, scalar_field.shape[0]])
    plt.gca().invert_yaxis()
    plt.savefig(output_file, dpi=100, bbox_inches='tight', pad_inches=0, transparent=True)
    plt.close()

    return contours

# Create a matching text file with the same name as the PNG but with a .info extension
def create_info_file(output_file, scalar_field, contours):
    info_file = output_file.replace('.png', '.info')
    min_value = np.min(scalar_field)
    max_value = np.max(scalar_field)
    contour_levels = contours.levels
    
    with open(info_file, 'w') as f:
        f.write(f"Min Value: {min_value}\n")
        f.write(f"Max Value: {max_value}\n")
        f.write("Contour Levels:\n")
        for level in contour_levels:
            f.write(f"  {level}\n")
    print(f"Info file created successfully: {info_file}")

# Main function to create isobaric lines and corresponding info files
def CreateIsobaricLines():    
    # Only select PNG files that start with 'HGT'
    png_files = sorted([f for f in os.listdir(PNG_DIR) if f.startswith('HGT') and f.endswith('.png')])

    for png_file in png_files:
        # Load and preprocess the scalar field (apply smoothing and interpolation)
        scalar_field = load_scalar_field(os.path.join(PNG_DIR, png_file))
        scalar_field_smoothed = smooth_data(scalar_field, sigma=2)  # Adjust smoothing
        scalar_field_interp = interpolate_data(scalar_field_smoothed, (500, 500))  # Increase resolution

        # Generate and save the isobaric plot (contour plot)
        output_file = os.path.join(PNG_DIR, f"ISOBARIC{png_file}")
        contours = generate_isobaric_plot(scalar_field_interp, output_file)

        # Create a matching info file
        create_info_file(output_file, scalar_field_interp, contours)

        print(f"Isobaric contour image and info file generated successfully: {output_file}")

if __name__ == "__main__":
    CreateIsobaricLines()
