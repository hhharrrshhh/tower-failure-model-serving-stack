# MLOps Project 2: Final Engineering Report & Demonstration Guide
## Tower-Failure Model on a Linux Server: Deployed, Load-Tested and Monitored

**Course:** Elective II: Machine Learning Operations (MLOps)  
**Instructor:** Dr. Santosh Kumar  
**Group 12:** Harsh Gharat (B032) & Manav Thakkar (B055)  
**Date:** October 2026  

---

## 1. Executive Summary & Architecture

This project implements an end-to-end production serving stack for predicting mobile tower failures within 48 hours based on multivariate sensor history. Designed for deployment on a Linux server, the system consists of:
- **Shared Feature Pipeline:** Zero-skew preprocessing (`TowerFeatureEngineer`) shared between training and inference.
- **Model Engine:** `HistGradientBoostingClassifier` trained on 1,500 rows (`telecom_tower_failure.csv`), handling 20.8% failure rate and missing values.
- **Serving API:** FastAPI service exposing `/predict` (single and batch), `/health`, `/version`, and Prometheus `/metrics`.
- **Packaging:** Dockerized stack (`tower-api`, Prometheus, Grafana) orchestrated with `docker-compose.yml`.
- **Monitoring & Alerts:** Provisioned Grafana dashboard tracking RPS, latency percentiles (p50, p95, p99), error rate, failure ratio, and CPU/RAM; two Prometheus alert rules (`HighLatencyP95` and `HighFailurePredictionSpike`).
- **Empirical Load Testing:** Locust load tests under 10, 100, and 500 concurrency using `load_test_requests.csv`; bottleneck diagnosed and resolved via NumPy vectorization (+42% throughput, -47% median latency under peak stress).
- **Self-Healing Automation:** Scheduled Bash watchdog script with anti-restart loop protection and log rotation.

---

## 2. Linux Server Setup & Practice (Task 1)

1. **Remote Access:** The stack is provisioned for remote execution via SSH on an Ubuntu server (see `docs/remote_server_guide.md`).
2. **Permissions Demonstration:** Implemented in `scripts/setup_permissions.sh`. A sensitive config file `/tmp/tower_permissions_demo/production_config.env` is assigned ownership `root:towerops` and mode `640` (`-rw-r-----`). Verification in Linux proves:
   - Group member `opsengineer` can read the configuration.
   - Group member `opsengineer` is denied write/modify access.
   - Non-members (`nobody`) are denied read access.
3. **Command Log:** `docs/linux_command_log.md` documents 25 distinct Linux commands with contextual justifications covering navigation, permissions, process management, log searching, network probing, and disk/memory monitoring.

---

## 3. Model Preparation & Input Contract (Task 2)

- **Dataset:** 1,500 labeled tower sensor records with 20.8% failure rate (imbalanced). Columns `Temperature_C`, `Battery_Voltage`, `Fan_Speed_RPM`, and `Humidity_Percent` contain ~3% missing values.
- **Feature Engineering:** `src/features.py` defines `TowerFeatureEngineer` implementing median imputation and domain interactions:
  - `temp_to_fan`: Thermal load relative to cooling fan speed
  - `power_to_traffic`: Energy efficiency under subscriber demand
  - `stress_index`: Thermal-electrical cabinet stress
- **Evaluation Metric Justification:** Standard accuracy is misleading on a dataset where 79.2% of towers do not fail. We prioritized **Precision-Recall AUC (PR-AUC)** and **F1-Score** with balanced loss weighting:
  - **ROC-AUC:** `0.7802`
  - **PR-AUC (Average Precision):** `0.5008` (vs. 0.2080 random baseline)
  - **F1-Score (Failure class):** `0.5041` (Precision: 50.8%, Recall: 50.0% at 0.45 threshold)
- **Artifact:** Versioned artifact `artifacts/model_v1.joblib` and `artifacts/model_metadata.json`.
- **Contract:** Documented in `docs/input_contract.md`.

---

## 4. Prediction Service & Parity Verification (Task 3)

- **Endpoints:**
  - `POST /predict`: Accepts single or batch telemetry readings, returns prediction class, probability, and risk level.
  - `GET /health`: Returns `{ "status": "healthy", "model_loaded": true, "version": "v1.0.0" }`.
  - `GET /version`: Returns model training timestamp and algorithm metadata.
  - `GET /metrics`: Exports Prometheus format metrics.
- **Startup Lifecycle:** Model loaded once into memory via FastAPI `@asynccontextmanager lifespan`.
- **Validation:** Pydantic models in `src/schemas.py` enforce physical bounds (`Temperature_C` in `[-40, 300]`, `Battery_Voltage` in `[0, 120]`, etc.). Invalid readings return `422 Unprocessable Entity` without crashing.
- **Parity Test (`tests/test_parity.py`):** Verified 50 random sample rows from `telecom_tower_failure.csv`. Online API predictions matched offline model predictions with **0 drift (100.0% exact match)**.

---

## 5. Containerised Deployment (Task 4)

- **Dockerfile:** Minimal Python 3.11-slim container with built-in healthcheck probe.
- **Docker Compose:** `docker-compose.yml` starts `tower-api`, `prometheus`, and `grafana` in a unified bridge network (`tower-net`).
- **Restart Policy:** Configured with `restart: unless-stopped` to guarantee automatic recovery across container crashes or host reboot.

---

## 6. Monitoring & Alerts (Task 5)

- **Dashboard:** Auto-provisioned in Grafana via `monitoring/grafana/provisioning/` (uid: `tower-serving-telemetry`) with 5 panels:
  1. Throughput / Request Rate (RPS)
  2. Latency Percentiles (p50, p95, p99)
  3. Error Rate Percentage
  4. Failure Prediction Share (%) vs. Historical Baseline (20.8%)
  5. Process Memory (RSS) & System Resources
- **Alert Rules (`monitoring/prometheus/alert_rules.yml`):**
  - `HighLatencyP95`: p95 latency > 80ms for 15s.
  - `HighFailurePredictionSpike`: Share of failure predictions > 45% for 15s.

---

## 7. Load Testing & Bottleneck Diagnosis (Task 6)

Load test scenarios were executed using Locust (`load_test/locustfile.py`) with real sensor requests from `load_test_requests.csv` at 10, 100, and 500 concurrency.

### Before vs. After Optimization Results

| Scenario | Concurrency | Baseline RPS | Optimized RPS | Baseline p50 | Optimized p50 | Baseline p95 | Optimized p95 | Baseline Failures | Optimized Failures |
|---|---|---|---|---|---|---|---|---|---|
| **Low Concurrency** | 10 | 46.12 | **93.06** | 160 ms | **52 ms** | 330 ms | **180 ms** | 0.0% | 0.0% |
| **Medium Concurrency**| 100 | 108.09 | **110.41** | 600 ms | **980 ms** | 1,800 ms | **1,300 ms** | 0.0% | 0.0% |
| **Peak Stress 500** | 500 | 191.70 | **272.42** | 1,500 ms | **800 ms** | 2,000 ms | **2,000 ms** | 11.66% | **8.57%** |

### Bottleneck Diagnosis & Improvement
- **Bottleneck Identified:** Under 500 concurrent users, the service became bottlenecked by per-request Pandas DataFrame allocations (`pd.DataFrame(records)` and column filtering), blocking the single-threaded asyncio event loop.
- **Improvement Implemented:** Replaced DataFrame instantiation with direct 2D NumPy array matrix construction and vectorized NumPy arithmetic in `src/features.py`.
- **Measured Evidence:** Under 500 users, throughput rose from **191.70 to 272.42 RPS (+42.1%)**, peak requests served increased from **5,599 to 8,003**, and max response timeout dropped by **5.15 seconds**.

---

## 8. Automated Recovery & Log Rotation (Task 7)

- **Watchdog Routine:** `scripts/watchdog.sh` queries `http://localhost:8000/health`.
- **Recovery Timing:** Deliberately terminating the service process triggers failure detection, automated restart, and recovery confirmation.
- **Anti-Restart Loop:** If 3 consecutive restart attempts fail without a healthy response, the script enters a safety lockout (`FATAL`) to prevent system thrashing and alerts on-call engineers.
- **Log Rotation:** Self-contained threshold rotation (>500KB) and Linux `logrotate` configuration (`scripts/logrotate.conf`) keep rotated archives (`watchdog.log.1`, `.2`).

---

## 9. 5-Minute Demonstration Walkthrough Checklist

During the project evaluation demonstration:
1. **Show Remote Access & Permissions:** Run `bash scripts/setup_permissions.sh` demonstrating `opsengineer` can read but not modify `production_config.env`.
2. **Show Parity Test:** Run `python tests/test_parity.py` proving exact offline-to-online prediction parity across 50 sample rows.
3. **Show Docker Deployment:** Run `docker compose up -d` and show healthy container status with `docker compose ps`.
4. **Show Live Dashboard:** Open `http://localhost:3000` (Grafana) showing real-time RPS, latency percentiles, error rate, and failure ratio.
5. **Show Load Testing:** Run `python load_test/run_benchmarks.py` and inspect the Before-vs-After benchmark table.
6. **Demonstrate Kill & Self-Healing:** Terminate the container (`docker kill tower-api`), run `bash scripts/watchdog.sh`, and watch the recovery log record the exact recovery time in seconds.
