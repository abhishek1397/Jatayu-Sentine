# scripts/healthcheck.py
import psycopg2
from confluent_kafka.admin import AdminClient

print("--- INFRASTRUCTURE HEALTHCHECK ---")

# 1. Kafka Check
print("Checking Kafka...")
try:
    admin = AdminClient({'bootstrap.servers': 'localhost:9092'})
    topics = admin.list_topics(timeout=10).topics
    required_topics = ['drone.frames', 'drone.detections']

    for rt in required_topics:
        if rt in topics:
            print(f"[OK] Kafka Topic '{rt}' exists.")
        else:
            print(f"[FAIL] Kafka Topic '{rt}' is missing!")
except Exception as e:
    print(f"[FAIL] Kafka connection failed: {e}")

# 2. Postgres Check
print("\nChecking Postgres...")
try:
    conn = psycopg2.connect(
        dbname="jatayu_db", user="jatayu_user",
        password="jatayu_password", host="localhost", port="5432"
    )
    cur = conn.cursor()
    cur.execute("SELECT to_regclass('public.window_counts');")
    exists = cur.fetchone()[0]
    if exists:
        print("[OK] Postgres table 'window_counts' exists.")
    else:
        print("[FAIL] Postgres table 'window_counts' missing!")
    cur.close()
    conn.close()
except Exception as e:
    print(f"[FAIL] Postgres connection failed: {e}")