import rasterio
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm
import numpy as np

def create_hazard_map(tif_path, output_png):
    print("Generating Publication-Ready Hazard Map...")
    
    # 1. Open the GeoTIFF
    with rasterio.open(tif_path) as src:
        flood_depth = src.read(1)
        extent = [src.bounds.left, src.bounds.right, src.bounds.bottom, src.bounds.top]

    # 2. Define Hazard Classes based on flood depth (in meters)
    # 0 - 0.5m = Low, 0.5 - 1.5m = Medium, 1.5 - 3.0m = High, > 3.0m = Very High
    bounds = [0.1, 0.5, 1.5, 3.0, 10.0] 
    colors = ['#ffffb2', '#fecc5c', '#fd8d3c', '#e31a1c'] # Yellow, Orange, Dark Orange, Red
    cmap = ListedColormap(colors)
    norm = BoundaryNorm(bounds, cmap.N)

    # Mask dry areas (depth < 0.1m)
    flood_depth_masked = np.ma.masked_where(flood_depth < 0.1, flood_depth)

    # 3. Setup the plot
    fig, ax = plt.subplots(figsize=(12, 10), dpi=300)
    
    # Plot the data
    im = ax.imshow(flood_depth_masked, extent=extent, cmap=cmap, norm=norm)
    
    # 4. Add colorbar with custom labels
    cbar = plt.colorbar(im, ax=ax, shrink=0.6, pad=0.03, ticks=[0.3, 1.0, 2.25, 6.5])
    cbar.ax.set_yticklabels(['Low (0.1 - 0.5m)', 'Medium (0.5 - 1.5m)', 'High (1.5 - 3.0m)', 'Very High (> 3.0m)'], fontsize=12)
    cbar.set_label('Flash Flood Hazard Level', fontsize=14, fontweight='bold')

    # 5. Formatting
    ax.set_title("100-Year Flash Flood Hazard Map - Weyib Sub-Basin", fontsize=18, fontweight='bold', pad=20)
    ax.set_xlabel("Easting (m)", fontsize=14, fontweight='bold')
    ax.set_ylabel("Northing (m)", fontsize=14, fontweight='bold')
    
    # 6. Save the image
    plt.savefig(output_png, bbox_inches='tight')
    plt.close()
    print(f"✅ Map successfully saved as: {output_png}")

if __name__ == "__main__":
    # Use the exact file name you provided!
    INPUT_TIF = r"D:\Thesis\SQL\100yr_hazard_map.png\Depth (02JAN2000 00 00 00).Terrain.Clipped weyib 12.5 Dem.tif" 
    
    # Change the output name slightly so it doesn't conflict with the folder
    OUTPUT_PNG = r"D:\Thesis\SQL\100yr_hazard_map_final.png"
    
    create_hazard_map(INPUT_TIF, OUTPUT_PNG)