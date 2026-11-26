# producer/replay_producer.py
import cv2
import time
import os
import argparse
from confluent_kafka import Producer

def get_delivery_callback():
    def delivery_report(err, msg):
        if err is not None:
            print(f"[Delivery Error] {err}")
    return delivery_report

def resize_frame(frame, max_width=1920):
    h, w = frame.shape[:2]
    if w > max_width:
        ratio = max_width / float(w)
        new_h = int(h * ratio)
        frame = cv2.resize(frame, (max_width, new_h), interpolation=cv2.INTER_AREA)
    return frame

def main():
    parser = argparse.ArgumentParser(description="JATAYU Drone Replay Producer")
    parser.add_argument("--source", required=True, help="Path to mp4 video or image folder")
    parser.add_argument("--fps", type=int, default=30, help="Target FPS")
    parser.add_argument("--topic", default="drone.frames", help="Kafka topic")
    parser.add_argument("--broker", default="localhost:9092", help="Kafka broker")
    args = parser.parse_args()

    producer = Producer({
        'bootstrap.servers': args.broker,
        'message.max.bytes': 5242880,  # 5MB
        'linger.ms': 10
    })

    print(f"Starting producer. Target FPS: {args.fps}, Source: {args.source}")
    target_interval = 1.0 / args.fps
    frame_id = 0
    start_time = time.monotonic()
    last_log_time = start_time
    frames_since_log = 0

    is_dir = os.path.isdir(args.source)
    if is_dir:
        files = sorted([os.path.join(args.source, f) for f in os.listdir(args.source) if f.endswith(('.jpg', '.png'))])
        stream = iter(files)
    else:
        cap = cv2.VideoCapture(args.source)
        if not cap.isOpened():
            print(f"Error opening video: {args.source}")
            return

    while True:
        loop_start = time.monotonic()
        
        # Read frame
        if is_dir:
            try:
                frame_path = next(stream)
                frame = cv2.imread(frame_path)
                filename = os.path.basename(frame_path)
            except StopIteration:
                break
        else:
            ret, frame = cap.read()
            if not ret:
                break
            filename = os.path.basename(args.source)

        if frame is None:
            continue

        # Resize and Encode
        frame = resize_frame(frame)
        ret, buffer = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
        if not ret:
            continue

        # Prepare headers and payload
        ts = int(time.time())
        headers = {
            'frame_id': str(frame_id).encode('utf-8'),
            'ts': str(ts).encode('utf-8'),
            'source': filename.encode('utf-8')
        }

        # Produce message
        producer.produce(
            topic=args.topic,
            value=buffer.tobytes(),
            headers=headers,
            on_delivery=get_delivery_callback()
        )
        producer.poll(0)
        
        frame_id += 1
        frames_since_log += 1

        # Pacing
        elapsed = time.monotonic() - loop_start
        sleep_time = target_interval - elapsed
        if sleep_time > 0:
            time.sleep(sleep_time)

        # Logging every 5 seconds
        now = time.monotonic()
        if now - last_log_time >= 5.0:
            actual_fps = frames_since_log / (now - last_log_time)
            print(f"[{time.strftime('%X')}] Sent {frames_since_log} frames | Actual FPS: {actual_fps:.2f} | Frame ID: {frame_id}")
            frames_since_log = 0
            last_log_time = now

    producer.flush()
    if not is_dir:
        cap.release()
    print("Streaming finished.")

if __name__ == "__main__":
    main()