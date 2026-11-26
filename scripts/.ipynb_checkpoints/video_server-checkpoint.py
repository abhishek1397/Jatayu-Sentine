# scripts/video_server.py
import time
from flask import Flask, Response
from confluent_kafka import Consumer, KafkaError

app = Flask(__name__)

def generate_frames():
    consumer = Consumer({
        'bootstrap.servers': '127.0.0.1:9092',
        'group.id': f'shiny_video_viewer_{int(time.time())}',
        'auto.offset.reset': 'latest',
        'enable.auto.commit': True
    })
    consumer.subscribe(['drone.frames'])

    try:
        while True:
            msg = consumer.poll(timeout=0.2)
            if msg is None:
                continue
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    continue
                else:
                    print(f"[Video Server Error] {msg.error()}")
                    continue

            frame_bytes = msg.value()
            if not frame_bytes:
                continue

            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
    except GeneratorExit:
        pass
    except Exception as e:
        print(f"[Video Server Exception] {e}")
    finally:
        consumer.close()

@app.route('/video_feed')
def video_feed():
    return Response(
        generate_frames(),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )

if __name__ == '__main__':
    print("Video Stream Server running on http://127.0.0.1:5000 ...")
    app.run(host='127.0.0.1', port=5000, threaded=True)