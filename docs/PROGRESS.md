## Phase 1: Infrastructure
- Fixed `docker-compose.yml` to use official Apache Kafka image (KRaft mode).
- Verified Postgres 16 initialization and Kafka topic creation (max message 5MB).
- Status: PASS

## Phase 2: R, EDA and Probabilistic Priors
- Generated class frequencies, object distributions, and box size plots.
- Exported Dirichlet priors (`class_prior.csv`) and count statistics (`count_stats.csv`).
- Finding: Extreme overdispersion detected; Negative Binomial required for dashboard anomaly alerts.
- Status: PASS

## Phase 3: Data Prep and Model Training
- Validated YOLO labels successfully (`check_labels.py`).
- Resolved PyTorch 2.6 `torch.load(weights_only=True)` checkpoint compatibility issue.
- Switched detector architecture to `yolov8n` (imgsz=640) for fast execution.
- Trained YOLOv8n (2 epochs) to unblock downstream pipeline development; weights saved to `runs/jatayu_model/weights/best.pt`.
- Generated `docs/MODEL_REPORT.md` with evaluation metrics and per-class AP.
- Status: PASS

## Phase 4: Replay Producer
- Producer streams resized, encoded frames to Kafka `drone.frames`.
- Consumer verified monotonic order. Max sustainable framerate measured at ~17.6 FPS.
- Status: PASS

## Phase 5: Detector and Tracker Service
- Deployed YOLOv8n detector with ByteTrack integration.
- Resolved PyTorch 2.6 serialization and JSON float32 casting boundaries.
- Verified live publishing to `drone.detections` with validated JSON schema and persistent track IDs.
- Performance: Mean inference latency 15–28 ms (~35–65 FPS), meeting real-time processing constraints on RTX 5060.
- Status: PASS

## Phase 6: Spark Streaming
- Implemented PySpark Structured Streaming job with 10-second tumbling windows and 20-second watermark.
- Handled Bronze layer raw writes to Parquet and Gold layer aggregation upserts to Postgres via psycopg2.
- Configured gap-filling SQL view (`window_counts_filled`) for continuous zero-filled class intervals.
- Status: PASS



