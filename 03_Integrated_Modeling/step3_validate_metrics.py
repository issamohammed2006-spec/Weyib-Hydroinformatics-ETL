import rasterio
from rasterio.warp import reproject, Resampling
import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import confusion_matrix, accuracy_score, precision_score, recall_score, f1_score, cohen_kappa_score

def validate_maps(hecras_path, pre_path, post_path):
    print("Aligning and Reading Rasters...")
    
    with rasterio.open(hecras_path) as src_hec:
        hec_data = src_hec.read(1)
        hec_meta = src_hec.meta
        
    def get_aligned_array(path):
        with rasterio.open(path) as src:
            aligned_data = np.full(hec_data.shape, np.nan, dtype=np.float32)
            reproject(
                source=src.read(1),
                destination=aligned_data,
                src_transform=src.transform,
                src_crs=src.crs,
                dst_transform=hec_meta['transform'],
                dst_crs=hec_meta['crs'],
                resampling=Resampling.nearest
            )
        return aligned_data

    pre_vals = get_aligned_array(pre_path)
    post_vals = get_aligned_array(post_path)

    valid_pre = ~np.isnan(pre_vals)
    valid_post = ~np.isnan(post_vals)
    
    pre_water = valid_pre & (pre_vals < -18.0)
    post_water = valid_post & (post_vals < -18.0)
    
    flood_extent = post_water & (~pre_water) & valid_pre & valid_post
    flood_extent = flood_extent.astype(np.uint8)
    
    total_flood_pixels = np.sum(flood_extent)
    print(f"Total Flood Pixels Detected by Satellite: {total_flood_pixels}")

    hec_data = np.where(hec_data > 0, 1, 0).astype(np.uint8)

    y_true = flood_extent.flatten()
    y_pred = hec_data.flatten()
    
    valid_mask = valid_pre.flatten() & valid_post.flatten()
    
    if np.sum(valid_mask) == 0:
        print("Error: No valid overlapping pixels found.")
        return

    y_true, y_pred = y_true[valid_mask], y_pred[valid_mask]

    # --- SAFE METRICS CALCULATION ---
    cm = confusion_matrix(y_true, y_pred, labels=[0, 1])
    tn, fp, fn, tp = cm.ravel()
    
    accuracy = accuracy_score(y_true, y_pred)
    precision = precision_score(y_true, y_pred, zero_division=0)
    recall = recall_score(y_true, y_pred, zero_division=0)
    f1 = f1_score(y_true, y_pred, zero_division=0)
    kappa = cohen_kappa_score(y_true, y_pred)

    print("\n--- Validation Results ---")
    print(f"True Positives (Both Flooded): {tp}")
    print(f"False Positives (Model Flood, Sat Dry): {fp}")
    print(f"False Negatives (Model Dry, Sat Flood): {fn}")
    print(f"True Negatives (Both Dry): {tn}")
    print("-" * 30)
    print(f"Overall Accuracy: {accuracy:.2%}")
    print(f"Precision: {precision:.2%}")
    print(f"Recall: {recall:.2%}")
    print(f"F1-Score: {f1:.3f}")
    print(f"Kappa Coefficient: {kappa:.3f}")

    # --- VISUALIZE THE MISMATCH ---
    print("\nGenerating comparison image...")
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    
    axes[0].imshow(pre_vals, cmap='gray')
    axes[0].set_title("Pre-Flood Satellite (Nov 1-10)")
    
    axes[1].imshow(post_vals, cmap='gray')
    axes[1].set_title("Post-Flood Satellite (Nov 22-25)")
    
    axes[2].imshow(hec_data, cmap='Blues')
    axes[2].set_title("HEC-RAS 100-Year Flood Model")
    
    plt.tight_layout()
    plt.savefig("D:/Thesis/SQL/validation_comparison.png", dpi=300)
    print("Saved comparison image to D:/Thesis/SQL/validation_comparison.png")

if __name__ == "__main__":
    validate_maps(
        hecras_path=r"D:\Thesis\SQL\HEC_RAS_Binary.tif",
        pre_path=r"D:\Thesis\SQL\Raw_Pre_VH_Nov2023.tif",
        post_path=r"D:\Thesis\SQL\Raw_Post_VH_Nov2023.tif"
    )