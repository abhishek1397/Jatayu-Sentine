# spark/stream_aggregate.py
import os
import sys
import psycopg2

# --- Fix for Windows Hadoop / winutils ---
os.environ['HADOOP_HOME'] = r'C:\hadoop'
os.environ['hadoop.home.dir'] = r'C:\hadoop'
os.environ['PATH'] = r'C:\hadoop\bin;' + os.environ.get('PATH', '')
# -----------------------------------------

import psycopg2.extras
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json, explode, window, approx_count_distinct, avg
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, DoubleType, ArrayType

# Automatic Kafka connector download for Spark 3.5.0
os.environ['PYSPARK_SUBMIT_ARGS'] = '--packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0 pyspark-shell'

def write_to_postgres(df, epoch_id):
    """Custom foreachBatch writer handling Postgres UPSERT via psycopg2"""
    rows = df.collect()
    if not rows:
        return
        
    try:
        conn = psycopg2.connect(
            dbname="jatayu_db",
            user="jatayu_user",
            password="jatayu_password",
            host="127.0.0.1",       # Explicit IPv4 avoids Windows IPv6 timeouts
            port="5432"
        )
        cur = conn.cursor()
        
        query = """
            INSERT INTO public.window_counts (window_start, window_end, camera_id, cls, vehicles, avg_conf)
            VALUES %s
            ON CONFLICT (window_start, camera_id, cls) 
            DO UPDATE SET vehicles = EXCLUDED.vehicles, avg_conf = EXCLUDED.avg_conf;
        """
        
        values = [(r.window.start, r.window.end, r.camera_id, r.cls, int(r.vehicles), float(r.avg_conf)) for r in rows]
        psycopg2.extras.execute_values(cur, query, values)
        
        conn.commit()
        cur.close()
        conn.close()
        print(f"[{epoch_id}] Wrote {len(rows)} aggregated rows to Postgres.")
    except Exception as e:
        print(f"Error writing to Postgres: {e}")

def main():
    print("Initializing Spark Session...")
    spark = SparkSession.builder \
        .appName("JatayuSentinelStream") \
        .getOrCreate()
        
    spark.sparkContext.setLogLevel("WARN")

    # Define JSON Schema matching detector output
    object_schema = StructType([
        StructField("track_id", IntegerType(), True),
        StructField("cls", StringType(), True),
        StructField("conf", DoubleType(), True),
        StructField("box", ArrayType(DoubleType()), True)
    ])
    
    payload_schema = StructType([
        StructField("camera_id", StringType(), True),
        StructField("frame_id", IntegerType(), True),
        StructField("ts", DoubleType(), True),
        StructField("objects", ArrayType(object_schema), True)
    ])

    print("Connecting to Kafka...")
    # 1. Read from Kafka
    raw_df = spark.readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", "127.0.0.1:9092") \
        .option("subscribe", "drone.detections") \
        .option("startingOffsets", "latest") \
        .load()

    # 2. Parse JSON & Add Timestamp
    parsed_df = raw_df.select(
        from_json(col("value").cast("string"), payload_schema).alias("data")
    ).select("data.*")
    
    # Cast UNIX seconds/fractional seconds to Spark Timestamp
    parsed_df = parsed_df.withColumn("event_time", col("ts").cast("timestamp"))

    # 3. Explode objects (1 row per bounding box)
    exploded_df = parsed_df.withColumn("obj", explode(col("objects")))
    
    flat_df = exploded_df.select(
        col("camera_id"),
        col("event_time"),
        col("obj.track_id").alias("track_id"),
        col("obj.cls").alias("cls"),
        col("obj.conf").alias("conf")
    ).filter(col("cls").isNotNull())

    # 4. BRONZE LAYER: Write raw flattened data to Parquet
    os.makedirs("data/bronze/detections", exist_ok=True)
    os.makedirs("data/checkpoints/bronze", exist_ok=True)
    os.makedirs("data/checkpoints/gold", exist_ok=True)

    bronze_query = flat_df.writeStream \
        .format("parquet") \
        .option("path", "data/bronze/detections") \
        .option("checkpointLocation", "data/checkpoints/bronze") \
        .trigger(processingTime="10 seconds") \
        .start()

    # 5. GOLD LAYER: Aggregate into 10-second tumbling windows
    agg_df = flat_df \
        .withWatermark("event_time", "20 seconds") \
        .groupBy(
            window(col("event_time"), "10 seconds"),
            col("camera_id"),
            col("cls")
        ) \
        .agg(
            approx_count_distinct("track_id").alias("vehicles"),
            avg("conf").alias("avg_conf")
        )

    # 6. Write to Postgres
    print("Starting streaming queries...")
    gold_query = agg_df.writeStream \
        .foreachBatch(write_to_postgres) \
        .outputMode("update") \
        .option("checkpointLocation", "data/checkpoints/gold") \
        .trigger(processingTime="10 seconds") \
        .start()

    spark.streams.awaitAnyTermination()

if __name__ == "__main__":
    main()