# scripts/test_detections.py
import json
import time
from confluent_kafka import Consumer

def main():
    consumer = Consumer({
        'bootstrap.servers': 'localhost:9092',
        'group.id': 'test_detections_group',
        'auto.offset.reset': 'latest'
    })
    
    consumer.subscribe(['drone.detections'])
    print("Listening to drone.detections for 30 seconds...")
    
    start_time = time.time()
    msg_count = 0
    valid_json = True
    
    while time.time() - start_time < 30.0:
        msg = consumer.poll(1.0)
        if msg is None:
            continue
            
        msg_count += 1
        try:
            payload = json.loads(msg.value().decode('utf-8'))
            if "camera_id" not in payload or "objects" not in payload:
                valid_json = False
            
            if len(payload["objects"]) > 0:
                print(f"Frame {payload['frame_id']} | Valid JSON | Tracks: {[obj['track_id'] for obj in payload['objects']]}")
            else:
                print(f"Frame {payload['frame_id']} | Valid JSON | Tracks: [] (Empty frame)")
                
        except Exception as e:
            print(f"JSON Error: {e}")
            valid_json = False

    print(f"\n--- DETECTIONS TEST RESULTS ---")
    print(f"Messages received: {msg_count}")
    print(f"Valid JSON structure: {valid_json}")
    consumer.close()

if __name__ == "__main__":
    main()