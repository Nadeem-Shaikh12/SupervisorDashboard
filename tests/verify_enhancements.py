import os
import sys
import numpy as np
import cv2

# Ensure project root is in path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from camera.image_processing import ThermalProcessor
from camera.camera_interface import SimulatorCamera
import camera.config as cfg

def main():
    print("--- Verifying 'Pro' Thermal Enhancements ---")
    
    # Setup test directory
    test_out_dir = os.path.join(cfg.DATA_ROOT, "test_verification")
    os.makedirs(test_out_dir, exist_ok=True)
    
    # 1. Generate a synthetic frame using the Simulator
    cam = SimulatorCamera()
    cam.open()
    frame = cam.next_frame()
    cam.close()
    
    if frame is None:
        print("Error: Could not generate test frame.")
        return

    # 2. Process with ThermalProcessor
    proc = ThermalProcessor()
    
    # We'll manually step through to save intermediate results
    
    # Step A: Simple Min/Max Normalization (for comparison)
    f_min, f_max = frame.min(), frame.max()
    simple_norm = ((frame - f_min) / (f_max - f_min) * 255.0).astype(np.uint8)
    simple_heatmap = cv2.applyColorMap(simple_norm, cv2.COLORMAP_INFERNO)
    cv2.imwrite(os.path.join(test_out_dir, "01_simple_normalization.png"), simple_heatmap)
    
    # Step B: Percentile Normalization (as implemented)
    vmin, vmax = np.percentile(frame, [2, 98])
    perc_norm = np.clip(frame, vmin, vmax)
    perc_norm = ((perc_norm - vmin) / (vmax - vmin) * 255.0).astype(np.uint8)
    cv2.imwrite(os.path.join(test_out_dir, "02_percentile_norm.png"), perc_norm)
    
    # Step C: CLAHE
    clahe_img = proc._apply_clahe(perc_norm)
    cv2.imwrite(os.path.join(test_out_dir, "03_clahe_applied.png"), clahe_img)
    
    # Step D: Colormap
    heatmap = cv2.applyColorMap(clahe_img, cv2.COLORMAP_INFERNO)
    cv2.imwrite(os.path.join(test_out_dir, "04_colormap_applied.png"), heatmap)
    
    # Step E: Resize (Lanczos4)
    resized = cv2.resize(heatmap, (640, 480), interpolation=cv2.INTER_LANCZOS4)
    cv2.imwrite(os.path.join(test_out_dir, "05_resized_lanczos4.png"), resized)
    
    # Step F: Sharpening
    sharpened = proc._apply_sharpening(resized)
    cv2.imwrite(os.path.join(test_out_dir, "06_final_sharpened.png"), sharpened)
    
    # 3. Full pipeline result
    full_result = proc.process(frame)
    cv2.imwrite(os.path.join(test_out_dir, "07_full_pipeline.png"), full_result.heatmap_bgr)
    
    print(f"\nVerification successful!")
    print(f"Results saved to: {test_out_dir}")
    print("Files 01-07 show the progression of the enhancement.")

if __name__ == "__main__":
    main()
