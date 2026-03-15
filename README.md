# DreamVision Smart Factory Platform

DreamVision is a cutting-edge Industry 4.0 smart factory inspection system that automatically pairs hardware like ESP32-S3 thermal glasses with a resilient, latency-free Edge AI server to ingest, evaluate, and trace automotive components natively.

## System Workflow & Architecture
* **Capture Edge Device (Hardware)**: Extracts MJPEG thermal frames.
* **Edge Server Pipeline (`/edge_server`)**: Decompresses frames, evaluates the heat maps against the `data/components.csv` dataset, extracts temperatures using ML-trained `scikit-learn` algorithms, determines defect status (OK/WARNING/NOK), and triggers the cloud and SQLite storage.
* **Smart Factory Analytics (`/analytics`)**: Runs native Z-score process anomaly detection alongside a long-term moving-average trend maintenance engine to alert supervisors natively.
* **Supervisor Web Dashboard (`/frontend`)**: Single-Page API displaying the Digital Twin metrics, traceability analytics, and Supervisor Verification workflows instantly triggered over REST/WebSockets.

## Installation Instructions

1. Clone the repository natively:
   ```bash
   git clone https://github.com/bhagyawantganesh48/DreanVision.git
   cd DreamVision
   ```

2. Establish Dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Provision your Local Runtime Environment by launching the System Validator:
   ```bash
   python run_smart_factory.py
   ```

## Dashboard Usage Instructions

The Web UI hosts directly off the FastAPI framework seamlessly without any Nginx configuration blocks!

1. Start up your native Edge factory server:
   ```bash
   python edge_server/api/server.py
   ```
2. Open your standard web browser and head exactly to:
   **http://localhost:8002/app/index.html**

3. You can explore the active pipeline metrics, review Digital Twin SVG architectures natively, query the SQLite DB seamlessly using UID hashes, and explicitly update tracking parameters triggering CSV export.
