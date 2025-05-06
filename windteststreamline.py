import os
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image
import re

# Load the U and V component PNGs as numpy arrays
def load_wind_component(file_path):
    with Image.open(file_path) as img:
        img = img.convert('L')  # Convert to grayscale
        return np.array(img, dtype=np.float32) / 255.0 * 2 - 1  # Scale to range [-1, 1]

# Generate a streamline plot based on the U and V components
def generate_streamline_plot(u_component, v_component, output_file):
    x = np.linspace(0, u_component.shape[1] - 1, u_component.shape[1])
    y = np.linspace(0, u_component.shape[0] - 1, v_component.shape[0])
    X, Y = np.meshgrid(x, y)

    # Plot wind streamlines using matplotlib's streamplot
    plt.figure(figsize=(20.48, 10.24), dpi=100)  # Set the size of the image to 2048xwhatever it comes to
    plt.streamplot(X, Y, u_component, v_component, color='white', linewidth=0.1, density=6.0, arrowsize=0.6)
    plt.axis('off')

    # Save the output to a PNG file with the specified dimensions
    plt.gca().set_xlim([0, u_component.shape[1]])
    plt.gca().set_ylim([0, u_component.shape[0]])
    plt.gca().invert_yaxis()
    plt.savefig(output_file, dpi=100, bbox_inches='tight', pad_inches=0, transparent=True)
    plt.close()

if __name__ == "__main__":
    folder_path = "./png_data"  # Specify the folder containing UGRD and VGRD files
    ugrd_files = sorted([f for f in os.listdir(folder_path) if re.match(r"UGRD_.*\.png", f)])
    vgrd_files = sorted([f for f in os.listdir(folder_path) if re.match(r"VGRD_.*\.png", f)])

    for u_file, v_file in zip(ugrd_files, vgrd_files):
        # Ensure matching UGRD and VGRD files
        match = re.match(r"UGRD_(.*)\.png", u_file)
        if match:
            common_part = match.group(1)
            v_match = f"VGRD_{common_part}.png"
            if v_match == v_file:
                u_component = load_wind_component(os.path.join(folder_path, u_file))
                v_component = load_wind_component(os.path.join(folder_path, v_file))

                # Generate and save the streamline plot in the same folder as the source files
                output_file = os.path.join(folder_path, f"WIND_{common_part}.png")
                generate_streamline_plot(u_component, v_component, output_file)

                print(f"Wind streamline image generated successfully: {output_file}")
