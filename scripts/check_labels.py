# scripts/check_labels.py
import os
import glob
from pathlib import Path

def validate_dataset(dataset_path):
    print(f"Validating dataset at: {dataset_path}")
    dataset_dir = Path(dataset_path)
    
    images = sorted(glob.glob(str(dataset_dir / "**" / "*.jpg"), recursive=True))
    print(f"Found {len(images)} images.")
    
    errors = 0
    for img_path in images:
        lbl_path = img_path.replace('images', 'labels').replace('.jpg', '.txt')
        if not os.path.exists(lbl_path):
            # Sometimes YOLO folders just dump everything together
            lbl_path = img_path.replace('.jpg', '.txt')
            if not os.path.exists(lbl_path):
                print(f"[FAIL] Missing label for {img_path}")
                errors += 1
                continue
                
        with open(lbl_path, 'r') as f:
            for line_idx, line in enumerate(f):
                parts = line.strip().split()
                if not parts:
                    continue
                if len(parts) != 5:
                    print(f"[FAIL] {lbl_path} line {line_idx+1}: wrong token count.")
                    errors += 1
                    continue
                cls_id = int(parts[0])
                if not (0 <= cls_id <= 9):
                    print(f"[FAIL] {lbl_path}: Class ID {cls_id} out of bounds (0-9).")
                    errors += 1
                
                coords = [float(x) for x in parts[1:]]
                if any(c < 0.0 or c > 1.0 for c in coords):
                    print(f"[FAIL] {lbl_path}: Coordinates out of [0,1] bounds: {coords}")
                    errors += 1

    if errors == 0:
        print("[OK] All labels validated successfully.")
    else:
        print(f"[FAIL] Found {errors} errors.")

if __name__ == "__main__":
    validate_dataset(r"D:\PG\semester 3\R project\JATAYU_Dataset")