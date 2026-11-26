# Jatayu-Sentinel: Real-Time Aerial Traffic Surveillance & Bayesian Anomaly Detection

An end-to-end, low-latency distributed data pipeline for real-time Unmanned Aerial Vehicle (UAV) traffic monitoring, multi-object tracking, and probabilistic anomaly detection. 

Achieving an end-to-end inference-to-storage latency of **35–50 ms**, Jatayu-Sentinel bridges lightweight edge computer vision with fault-tolerant stream processing and interpretable Bayesian statistics to analyze heterogeneous, non-lane-based aerial traffic feeds.

---

## System Architecture

The pipeline ingests high-altitude (~120m) aerial drone footage, extracts vehicle kinematics at the edge, streams telemetry through a distributed message broker, and surfaces statistical anomalies on a live dashboard:

1. **Edge Vision & Tracking:** **YOLOv8 Nano** paired with **ByteTrack** performs real-time object detection and multi-object tracking without heavy GPU overhead.
2. **Distributed Message Brokering:** **Apache Kafka (KRaft mode)** handles fault-tolerant, Zookeeper-free ingestion of real-time tracking metadata.
3. **Stateful Stream Processing:** **PySpark Structured Streaming** aggregates unbounded telemetry into **10-second tumbling windows**, handling out-of-order frames and zero-inflation gap-filling.
4. **Persistence Layer:** Aggregated window metrics and trajectory telemetry are persisted to a containerized **PostgreSQL** database.
5. **Bayesian Anomaly Detection & UI:** An interactive **R Shiny** dashboard delivers synchronized live video feeds, time-series telemetry, and real-time probabilistic alerts.

---

## Key Features

* **Regional Heterogeneous Traffic Taxonomy:** Trained on the **JATAYUv1.0** dataset (29,413 annotated aerial frames) adhering to Indian Highway Capacity Manual (Indo-HCM) classifications across 10 distinct classes:
  * `auto_rickshaw`, `e_rickshaw`, `cycle_rickshaw`, `tractor_trolley`, `motorcycle`, `car`, `bus`, `truck`, `bicycle`, and `pedestrian`.
* **Principled Bayesian Anomaly Modeling:** Replaces rigid, deterministic threshold rules with conjugate Bayesian inference:
  * **Gamma-Poisson (Negative Binomial) Modeling:** Dynamically models natural traffic variance to detect sudden vehicle count surges.
  * **Dirichlet Posterior Updates:** Tracks shifts in categorical vehicle class-mix distributions in real time.
* **Zero-Inflation Mitigation:** Ensures continuous time-series integrity by explicitly imputing zero counts during empty or sparse tumbling windows.

---

## Tech Stack

| Layer | Technologies |
| :--- | :--- |
| **Computer Vision & MOT** | Python, Ultralytics YOLOv8n, ByteTrack, OpenCV |
| **Streaming & Ingestion** | Apache Kafka (KRaft mode), PySpark Structured Streaming |
| **Database & Storage** | PostgreSQL, Docker |
| **Statistical Modeling & UI** | R, R Shiny, Gamma-Poisson & Dirichlet Conjugate Models |

---

