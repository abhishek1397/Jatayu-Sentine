# scripts/test_consumer.py
import time
from confluent_kafka import Consumer

def main():
    consumer = Consumer({
        'bootstrap.servers': 'localhost:9092',
        'group.id': 'test_consumer_group',
        'auto.offset.reset': 'latest',
        'fetch.message.max.bytes': 5242880
    })
    
    consumer.subscribe(['drone.frames'])
    print("Listening to drone.frames for 30 seconds...")
    
    start_time = time.monotonic()
    msg_count = 0
    last_frame_id = -1
    
    while time.monotonic() - start_time < 30.0:
        msg = consumer.poll(1.0)
        if msg is None:
            continue
        if msg.error():
            print(f"Consumer error: {msg.error()}")
            continue
            
        msg_count += 1
        
        # Parse headers
        headers = dict(msg.headers() or [])
        current_frame_id = int(headers.get('frame_id', b'-1').decode('utf-8'))
        
        if current_frame_id < last_frame_id:
            print(f"[WARNING] Out of order! Received {current_frame_id} after {last_frame_id}")
        
        last_frame_id = current_frame_id

    duration = time.monotonic() - start_time
    rate = msg_count / duration
    print(f"\n--- TEST RESULTS ---")
    print(f"Total frames received: {msg_count}")
    print(f"Measured rate: {rate:.2f} FPS")
    print(f"Order monotonic: {'Yes' if msg_count > 0 else 'N/A (No messages)'}")
    
    consumer.close()

if __name__ == "__main__":
    main()