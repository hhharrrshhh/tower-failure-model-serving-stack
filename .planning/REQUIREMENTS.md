# Requirements: Project 2 - Tower Serving Stack

**Defined:** 2026-10-23  
**Core Value:** Provide a verified, reproducible, containerized prediction and monitoring pipeline deployed on a remote Linux server that survives peak traffic, recovers automatically from failure, and provides full empirical defense for serving capacity and alerting thresholds.

## v1 Requirements

### Task 1: Server Setup & Linux Practice (SRV)
- [ ] **SRV-01**: Remote Linux server instance provisioned with accessible SSH key-based authentication.
- [ ] **SRV-02**: File permission demonstration implemented (e.g., restricted directory/file with read-only group access).
- [ ] **SRV-03**: Command log maintained containing at least 25 distinct Linux commands with specific project rationale covering navigation, permissions, processes, log searching, and resource monitoring.

### Task 2: Model Preparation & Feature Logic (MDL)
- [ ] **MDL-01**: Single reusable feature preprocessing module implemented and shared between training and serving.
- [ ] **MDL-02**: Binary classification model trained on `telecom_tower_failure.csv` addressing missing values and ~20.8% failure imbalance.
- [ ] **MDL-03**: Evaluation metric selected and justified for imbalanced data (PR-AUC, ROC-AUC, F1-score with threshold calibration).
- [ ] **MDL-04**: Model saved as a versioned artifact (e.g. `model_v1.joblib`).
- [ ] **MDL-05**: Raw-input schema contract documented specifying field names, data types, and plausible operational ranges.

### Task 3: Prediction Service (API)
- [ ] **API-01**: FastAPI application exposes `POST /predict` accepting single or batch raw sensor readings.
- [ ] **API-02**: Service exposes `GET /health` and `GET /version` endpoints.
- [ ] **API-03**: Strict Pydantic input validation rejects missing fields or out-of-range sensor readings with 422 errors without crashing.
- [ ] **API-04**: Model is loaded once into memory on application startup, not per request.
- [ ] **API-05**: Verification script confirms predictions on 50 sample rows match offline predictions exactly (0 drift).

### Task 4: Containerised Deployment (DOCKER)
- [ ] **DOCKER-01**: Service packaged into a versioned Docker image with multi-stage or lean build.
- [ ] **DOCKER-02**: `docker-compose.yml` orchestrates service, Prometheus, and Grafana with a single command (`docker compose up -d`).
- [ ] **DOCKER-03**: Restart policies (`restart: unless-stopped` or `always`) configured and verified on container crash.
- [ ] **DOCKER-04**: Clear documentation allowing fresh clone deployment on remote Linux server.

### Task 5: Monitoring & Alerts (MON)
- [ ] **MON-01**: FastAPI instrumented exposing Prometheus metrics at `/metrics` (request count, latency histogram, error rate, tower failure predictions count).
- [ ] **MON-02**: Grafana dashboard provisioned via configuration showing RPS, p50/p95/p99 latency, error rate, failure prediction ratio, and basic server resource usage (CPU/memory).
- [ ] **MON-03**: Two Prometheus alert rules defined (e.g., High Latency p95 > threshold, High Error Rate / High Failure Ratio).
- [ ] **MON-04**: Both alerts triggered and demonstrated in firing state with captured proof.

### Task 6: Load Testing & Bottleneck Diagnosis (LOAD)
- [ ] **LOAD-01**: Load test designed using Locust/k6 and payloads drawn from `load_test_requests.csv`.
- [ ] **LOAD-02**: Test scenarios executed at 10, 100, and 500 concurrency, including ramp-up and sudden traffic spikes.
- [ ] **LOAD-03**: Throughput, latency percentiles (p50, p95, p99), and error rates recorded; breaking point explicitly defined and measured.
- [ ] **LOAD-04**: Bottleneck identified using Prometheus/Grafana and server metrics (CPU saturation, worker concurrency, or I/O).
- [ ] **LOAD-05**: Concrete performance improvement implemented (e.g., worker scaling, batch vectorization), re-tested, and presented in a Before-vs-After comparison table.

### Task 7: Automated Health Checks & Recovery (AUTO)
- [ ] **AUTO-01**: Scheduled Bash watchdog script checks `GET /health` at regular intervals.
- [ ] **AUTO-02**: Watchdog logs all check results with timestamps to a dedicated log file.
- [ ] **AUTO-03**: Automatic restart executed upon health check failure, logging recovery time.
- [ ] **AUTO-04**: Log rotation configured (logrotate or bash script) and verified working.
- [ ] **AUTO-05**: Anti-restart loop protection implemented to prevent infinite thrashing if startup fails.

### Task 8: Capacity & Alert-Threshold Defense (CAP)
- [ ] **CAP-01**: 1-page operational capacity & alerting memo written for shift engineers.
- [ ] **CAP-02**: Serving configuration (workers, CPU/memory limits, replicas) recommended and defended using empirical Task 6 load-test numbers for an explicit peak RPS.
- [ ] **CAP-03**: Both alert thresholds defended against plausible alternative values using measured load test distributions.

## Out of Scope

| Feature | Reason |
|---------|--------|
| Drift retraining pipeline | Belongs to Project 3 |
| CI/CD quality gate with GitHub Actions | Belongs to Project 1 |
| MLflow model registry tracking server | Belongs to Project 4 |
| Paid SaaS monitoring (Datadog, New Relic) | Assignment mandates free/open-source stack |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| SRV-01, SRV-02, SRV-03 | Phase 1: Server Setup & Linux Environment | Pending |
| MDL-01, MDL-02, MDL-03, MDL-04, MDL-05 | Phase 2: Feature Engineering & Model Training | Pending |
| API-01, API-02, API-03, API-04, API-05 | Phase 3: Prediction Service & Validation | Pending |
| DOCKER-01, DOCKER-02, DOCKER-03, DOCKER-04 | Phase 4: Containerization & Deployment | Pending |
| MON-01, MON-02, MON-03, MON-04 | Phase 5: Prometheus/Grafana Monitoring & Alerts | Pending |
| LOAD-01, LOAD-02, LOAD-03, LOAD-04, LOAD-05 | Phase 6: Load Testing & Bottleneck Optimization | Pending |
| AUTO-01, AUTO-02, AUTO-03, AUTO-04, AUTO-05 | Phase 7: Health Check Automation & Self-Healing | Pending |
| CAP-01, CAP-02, CAP-03 | Phase 8: Capacity Defense Memo & Final Deliverables | Pending |

**Coverage:**
- v1 requirements: 34 total
- Mapped to phases: 34
- Unmapped: 0

---
*Requirements defined: 2026-10-23*
