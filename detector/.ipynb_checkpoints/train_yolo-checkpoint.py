# detector/train_yolo.py
import os
import time
import sys
import torch

# --- PyTorch 2.6 Workaround ---
# PyTorch 2.6 changed torch.load(weights_only=True) by default, breaking YOLO.
# We patch it here to default to False for trusted local weights.
_original_load = torch.load
def _patched_load(*args, **kwargs):
    if 'weights_only' not in kwargs:
        kwargs['weights_only'] = False
    return _original_load(*args, **kwargs)
torch.load = _patched_load
# -------------------------------

from ultralytics import YOLO

def main():
    smoke_test = '--smoke' in sys.argv
    epochs = 2 if smoke_test else 20
    print(f"Starting YOLOv8 training. Smoke test: {smoke_test}, Epochs: {epochs}")
    
    # Load a pretrained model (YOLOv8 medium)
    model = YOLO('yolov8m.pt')
    
    # Train
    results = model.train(
        data='detector/data.yaml',
        epochs=epochs,
        imgsz=640,
        batch=16,          # Safe for 8GB VRAM at 1280 resolution
        device=0,         # Use RTX 5060
        project='runs',
        name='jatayu_model',
        exist_ok=True,
        workers=4
    )
    
    print("\nTraining completed. Evaluating on validation set...")
    metrics = model.val()
    
    # Generate Report
    os.makedirs('docs', exist_ok=True)
    with open('docs/MODEL_REPORT.md', 'w') as f:
        f.write("# YOLOv8 Training Report\n\n")
        f.write(f"**Epochs**: {epochs}\n")
        f.write(f"**mAP50**: {metrics.box.map50:.4f}\n")
        f.write(f"**mAP50-95**: {metrics.box.map:.4f}\n\n")
        f.write("## Per-Class AP50\n")
        for i, cls_ap in enumerate(metrics.box.maps):
            f.write(f"* **Class {i}**: {cls_ap:.4f}\n")
            
    print(f"\nModel saved to: runs/jatayu_model/weights/best.pt")
    print(f"Report saved to docs/MODEL_REPORT.md")

if __name__ == '__main__':
    start_time = time.time()
    main()
    elapsed = time.time() - start_time
    
    hours, remainder = divmod(elapsed, 3600)
    minutes, seconds = divmod(remainder, 60)
    print(f"\nTotal execution time: {int(hours)}h {int(minutes)}m {seconds:.2f}s ({elapsed:.2f} seconds total)")

