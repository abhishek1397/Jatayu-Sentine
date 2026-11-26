# detector/detect_track.py
import json
import time
import sys
import numpy as np
import cv2
import torch

# --- PyTorch 2.6 Workaround ---
_original_load = torch.load
def _patched_load(*args, **kwargs):
    if 'weights_only' not in kwargs:
        kwargs['weights_only'] = False
    return _original_load(*args, **kwargs)
torch.load = _patched_load
# -------------------------------

from confluent_kafka import Consumer, Producer
from ultralytics import YOLO

def main():
    print("Loading YOLO model...")
    # Load the model we trained in Phase 3
    model = YOLO("yolov8n.pt")

    # Kafka Setup
    consumer = Consumer({
        'bootstrap.servers': '127.0.0.1:9092',
        'group.id': 'yolo_detector_group',
        'auto.offset.reset': 'latest',
        'fetch.message.max.bytes': 5242880
    })
    
    producer = Producer({
        'bootstrap.servers': '127.0.0.1:9092',
        'linger.ms': 5
    })

    consumer.subscribe(['drone.frames'])
    print("Detector running. Listening to drone.frames...")

    # Class mappings
    class_names = model.names

    frames_processed = 0
    total_inference_time = 0
    total_e2e_time = 0

    try:
        while True:
            msg = consumer.poll(1.0)
            if msg is None:
                continue
            if msg.error():
                print(f"Consumer Error: {msg.error()}")
                continue

            receive_time = time.time()
            
            # 1. Parse Headers
            headers = dict(msg.headers() or [])
            frame_id = headers.get('frame_id', b'0').decode('utf-8')
            ts = float(headers.get('ts', b'0').decode('utf-8'))
            source = headers.get('source', b'unknown').decode('utf-8')
            camera_id = f"cam_{source.split('.')[0]}" # Mock camera ID from filename

            # 2. Decode Image
            nparr = np.frombuffer(msg.value(), np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if frame is None:
                continue


# 3. Inference & Tracking
            start_infer = time.time()
            # Added conf=0.45 to eliminate weak/noisy false positives
            results = model.track(frame, persist=True, verbose=False, tracker="bytetrack.yaml", conf=0.45)
            infer_time = time.time() - start_infer

            # 4. Parse Results
            objects = []
            if results[0].boxes is not None and results[0].boxes.id is not None:
                boxes = results[0].boxes.xywhn.cpu().numpy() # normalized xywh
                track_ids = results[0].boxes.id.int().cpu().tolist()
                classes = results[0].boxes.cls.int().cpu().tolist()
                confs = results[0].boxes.conf.cpu().tolist()

                for box, track_id, cls, conf in zip(boxes, track_ids, classes, confs):
                    # Filter out any detection with confidence < 0.45
                    if conf < 0.45:
                        continue

                    objects.append({
                        "track_id": int(track_id),
                        "cls": str(class_names[cls]),
                        "conf": round(float(conf), 3),
                        "box": [round(float(c), 3) for c in box]
                    })

            # 5. Publish to drone.detections (Always publish, even if 0 objects)
            payload = {
                "camera_id": camera_id,
                "frame_id": int(frame_id),
                "ts": ts,
                "objects": objects
            }
            
            producer.produce(
                topic="drone.detections",
                value=json.dumps(payload).encode('utf-8')
            )
            producer.poll(0)
            
            # Metrics
            e2e_time = receive_time - ts
            frames_processed += 1
            total_inference_time += infer_time
            total_e2e_time += max(0, e2e_time) # avoid negative if clock drift

            if frames_processed % 30 == 0:
                avg_infer = (total_inference_time / 30) * 1000
                avg_e2e = (total_e2e_time / 30) * 1000
                print(f"[{time.strftime('%X')}] Frame: {frame_id} | Objects: {len(objects)} | Infer: {avg_infer:.1f}ms | E2E Latency: {avg_e2e:.1f}ms")
                total_inference_time = 0
                total_e2e_time = 0

    except KeyboardInterrupt:
        print("Stopping detector...")
    finally:
        consumer.close()
        producer.flush()

if __name__ == "__main__":
    main()