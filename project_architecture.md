# DreamVision Smart Factory - Project Architecture & Data Flow

## 1. System Overview
DreamVision is an Industry 4.0 Thermal AI Inspection system designed to capture live thermal telemetry from edge devices (e.g., ESP32 connected to MLX90640), process anomalies locally, and synchronize telemetry with a cloud backend (MongoDB Atlas). 

The platform is capable of running a full suite of services locally on a single machine or edge gateway, orchestrated by main launcher scripts like `run_dreamvision.py` and `run_live_thermal.py`.

## 2. Global Architecture Layout

The application relies on a polyglot microservice pattern running in tandem:
- **Thermal Edge Capture (Python)**: Interfaces with the camera hardware, performs realtime stats calculations, applies boundary boxes, and generates OpenCV displays. 
- **Capture API Edge Server (Python - Port 8001)**: Intermediary for handling stream capture data.
- **Edge AI Server / UI Host (Python - Port 8002)**: Primarily hosts the dashboard endpoints, broadcasts new telemetry, and serves the static HTML/JS frontend assets (`/app/index.html`).
- **Cloud Express Backend (Node.js - Port 3000)**: Serves as the cloud-facing REST API providing aggregated statistics, historical queries, and cloud integrations (connecting to MongoDB).
- **Control Center Frontend**: Pure HTML/JS/CSS application utilizing WebSockets/HTTP polling to fetch telemetry from the servers. Includes a Digital Twin (`digital_twin.js`) to render components visually.

### High-Level Directory Structure
```
DreanVision-main/
├── run_dreamvision.py         # 1-Click Platform Launcher (Starts API, Edge Server, Live View)
├── main_api.py                # Capture API Server (Port 8001)
├── edge_server/               # Edge AI Server hosting dashboard + endpoints (Port 8002)
├── frontend/                  # Static HTML/JS Dashboard files (served by edge_server)
├── express_backend/           # Node.js API facing MongoDB (Port 3000)
│   ├── index.js               # Express app with endpoints (/results, /stats, /inspection)
│   └── package.json           # Node dependencies
├── project/                   # Core Edge Computing Logic
│   ├── run_live_thermal.py    # Dedicated launcher for Live Thermal OpenCV window & syncing
│   ├── camera/                # Hardware interfacing (esp32_stream.py, camera_interface.py)
│   ├── data/                  # Edge SQLite storage and snapshots destination
│   ├── database/              # SQLite edge DB logic (db.py, anomaly_manager.py)
│   └── mongo_db.py            # MongoDB sync client
└── database/                  # SQLite models and schemas for root level launchers
```

## 3. Data Flow & Streaming Pipelines

### A. Real-Time Hardware Streaming Pipeline
1. **Source**: ESP32 Camera (or Simulator fallback) broadcasts thermal data.
2. **Ingestion**: Internal `camera_interface.py` decodes the incoming byte frames into generic numpy float arrays (representing Celsius).
3. **Filtering & Analysis**: The frames are sent to `image_processing.py` where min, mean, max, and hotspot coordinates are calculated. 
4. **Local Thresholding (SQLite)**: Real-time max temps are compared to normal/critical thresholds stored inside the local `component_temperature_rules` table via `db.py`.
5. **Visualization**: NumPy arrays are converted to BGR color maps via OpenCV (`cvcolormap`), overlaid with bounding boxes and statuses, and displayed via `cv2.imshow()`.

### B. Storage & Cloud Upload Pipeline (Distributed Processing)
To prevent network latency from disrupting the real-time camera FPS, data storage is decoupled:
1. **Edge Persist**: A snapshot is triggered. The statistics, rule metadata, and status are instantly saved to the **Local SQLite Database** (`parts_inspection` table).
2. **Dashboard Broadcast**: A quick HTTP POST broadcast is triggered to `http://localhost:8002/dashboard/broadcast_new` to instantly update the frontend.
3. **Internal Queue Array**: The record is pushed to a non-blocking, max-sized `queue.Queue`.
4. **Cloud Uploader Thread**: A Daemon thread (`_CloudUploader`) continuously drains this queue, sending asynchronous `update_one(upsert=True)` payloads to **MongoDB Atlas**. 

### C. Frontend Telemetry Flow
1. Load dashboard (`index.html`) via Edge Server (Port 8002).
2. The UI polls or receives stats from `/stats` and `/results` via either Edge Server or Express Backend.
3. The Digital Twin component listens to these stats and adjusts the thermal colorings of 3D SVGs/Canvas matching the physical parts.

## 4. Database Models

### Local Edge DB (SQLite - `dreamvision.db` / `edge_inspection.db`)
* **`component_temperature_rules`**: `component_name (PK)`, `normal_temp_min`, `normal_temp_max`, `critical_temp`, `failure_temp`.
* **`parts_inspection`**: `part_uid (PK)`, `component_name`, `temperature`, `status`, `sync_status`, `verified_status`.
* **`inspection_anomalies`**: Track anomalous events over time.

### Cloud DB (MongoDB Atlas)
* **`inspections` Collection**: A flattened NoSQL replicate of `parts_inspection`, including nested hardware stats (min, max, etc.). Acts as the global telemetry warehouse.

---

## 5. Architectural Flaws & Improvement Suggestions

While functional, the current architecture mixes Edge and Cloud responsibilities across overlapping boundaries. Below are prioritized recommendations to stream-line and harden the project for Enterprise deployments.

### A. Reducing Complexity & Deployment Friction
**Current Problem:** Running the platform natively requires managing Python versions, Node.js versions, and avoiding port conflicts manually. Cross-platform execution is brittle.
**Solution (Containerization):**
* Dockerize the application into isolated containers: `thermal-edge` (Python), `cloud-api` (Node.js), `dashboard-ui` (Nginx). 
* Create a `docker-compose.yml` to spin up dependencies seamlessly without manual process monitoring (`_monitor_processes` hack).

### B. Modularization & Message Brokering (Decoupling)
**Current Problem:** Direct HTTP calls between Python sub-scripts and Queue threads mean losing data on crash. The architecture is tightly coupled (Python directly imports local SQLite, while Node reads from Mongo).
**Solution (Event-Driven Architecture):**
* Introduce **MQTT (via Mosquitto)** or **Redis Pub/Sub** on the edge device. 
* The Camera module purely pushes `{temp: 45, hotspot_x: 10}` to `sensor/thermal/raw`.
* An independent `AnomalyDetector` module subscribes to this topic, compares it with SQLite, and publishes to `sensor/thermal/anomaly`.
* The `CloudUploader` subscribes to it and guarantees delivery using an Outbox Pattern instead of a volatile internal Python `queue.Queue`.

### C. Bug & Failure Prevention
**Current Problem:** The SQLite database is accessed by multiple threads/processes concurrently, which leads to `database is locked` errors during high throughput. The Cloud Upload thread silently drops data if the Queue fills up.
**Solution:**
* Implement Async DB operations using something like SQLite WAL mode combined with SQLAlchemy, or upgrade the edge DB to PostgreSQL if running on a competent Edge Gateway.
* Implement a robust Retry/Backoff mechanism for the MongoDB connection instead of silently failing or dropping records when offline.
* Add comprehensive input validation and try-catch blocks in the Express backend (currently basic). Use Zod or Joi to strictly validate incoming payloads.

### D. Single Source of Truth for APIs
**Current Problem:** There is a Node API (`express_backend`) AND an Edge AI Server API (`edge_server`) doing similar things.
**Solution:**
* Sunset one of the APIs purely for external processing. 
* Keep the Edge AI server purely for local low-latency operations (like shutting off a physical machine).
* Rely entirely on the Express Node.js backend acting as the Cloud gateway for long-term historical aggregations and global dashboards. 

## 6. Component Level Breakdown

### A. Express Backend (`express_backend/index.js`)
* **Role**: Serves as the cloud-facing REST API providing a unified interface to the MongoDB Atlas backend.
* **Core Functions**:
  * `POST /inspection`: Receives new inspection records (from Python edge routers or ESP32 devices directly), calculates preliminary status (OK/WARNING/NOK), and performs an upsert by `part_uid`. It pushes Server-Sent Events (SSE) updates via `/stream`.
  * `GET /results`: Retrieves the latest 50 inspection events.
  * `GET /stats`: Aggregates the yield, defect percentages, and status counts globally across the system.
* **Deployment Context**: Typically deployed to a cloud provider like Render (`render_deployment_guide.md`), exposing the database seamlessly to any web-based dashboards globally (like Netlify).

### B. Hardware Diagnostics & Scanning Scripts
* **`diag_stream.py`**: A small utility script to ping the Edge Server Stream (`http://localhost:8001/stream`) and confirm if chunked video bytes are successfully being delivered over HTTP.
* **`scan_esp32_endpoints.py`**: Helps discover ESP32 streaming endpoints on a local network (e.g. `192.168.4.1`) across common ports (`80, 81, 8000`) looking for known streaming paths. This is extremely useful for headless setup when the IP or configuration changes dynamically.

### C. Firmware Build Configurations (`firmware/platformio.ini`)
* **Environment**: Configured for ESP32 utilizing the Arduino framework.
* **Libraries**: Strictly specifies dependencies on `Adafruit MLX90640` (the core thermal camera), `Adafruit GFX Library`, and an optional `Adafruit-ST7735-Library` Driver for debugging via a TFT LCD.
* **Implications**: The hardware is not acting strictly as an IP webcam; it has the MLX sensor directly connected over I2C, and relies on Espressif WiFi logic to broadcast the data array on a specific web port.
