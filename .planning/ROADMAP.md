# Roadmap: Project 2 - Tower Serving Stack

## Overview

A phased, verification-driven execution roadmap for taking a mobile tower failure prediction model to a fully monitored, self-healing, load-tested containerized deployment on a remote Linux server, completing all 8 required tasks with zero fabricated data.

## Phases

- [ ] **Phase 1: Linux Server Setup & Environment** - Provision Linux environment, verify SSH access, configure permissions, and initiate the 25-command operational log.
- [ ] **Phase 2: Feature Engineering & Model Training** - Build single reusable feature module, train failure-prediction model on `telecom_tower_failure.csv`, evaluate with class-imbalanced metrics, save versioned artifact, and document raw-input contract.
- [ ] **Phase 3: Prediction Service & Parity Verification** - Expose model via FastAPI (`/predict`, `/health`, `/version`), implement strict Pydantic input validation, load model once at startup, and verify 50 sample predictions match offline results.
- [ ] **Phase 4: Containerised Deployment Stack** - Package service into versioned Docker image, orchestrate with Docker Compose, configure restart policies, and verify deployment on Linux server.
- [ ] **Phase 5: Prometheus & Grafana Monitoring** - Expose Prometheus metrics, provision reproducible Grafana dashboard (RPS, latency percentiles, errors, failure ratio, resources), and trigger two live alert rules.
- [ ] **Phase 6: Load Testing & Bottleneck Optimization** - Benchmark using Locust with `load_test_requests.csv` at 10, 100, 500 concurrency; identify breaking point, diagnose bottleneck, apply 1 optimization, and record before/after table.
- [ ] **Phase 7: Automated Health Checks & Self-Healing** - Implement scheduled Bash watchdog script via cron with timestamped logging, log rotation, anti-restart loop protection, and prove auto-recovery.
- [ ] **Phase 8: Capacity Defense Memo & Final Deliverables** - Author 1-page capacity & alerting defense memo using empirical load test data, assemble 25-command log, and prepare demonstration scripts.

## Phase Details

### Phase 1: Linux Server Setup & Environment
**Goal**: Establish a functional Linux development/server environment, confirm remote SSH access, configure demo file permissions, and begin the 25-command operational log.
**Depends on**: Nothing
**Requirements**: SRV-01, SRV-02, SRV-03
**Success Criteria**:
  1. Linux server is accessible via SSH (remote cloud VM or SSH-enabled Linux instance).
  2. File permission demonstration is created (e.g. read-only group access for operational files).
  3. Linux command log has initial entries covering navigation, permissions, and network checks with explicit rationale.
**Plans**: 1 plan (01-01)

Plans:
- [ ] 01-01: Provision server access, configure permissions demo, and start command log.

### Phase 2: Feature Engineering & Model Training
**Goal**: Build a single reusable feature preprocessing module, train a tower failure prediction model on `telecom_tower_failure.csv` addressing class imbalance, save the versioned artifact, and document the input contract.
**Depends on**: Phase 1
**Requirements**: MDL-01, MDL-02, MDL-03, MDL-04, MDL-05
**Success Criteria**:
  1. A single shared feature module exists in the codebase and is imported by training code.
  2. Missing values in `telecom_tower_failure.csv` are handled cleanly in pipeline.
  3. Model evaluation report justifies PR-AUC / ROC-AUC / F1 for the 20.8% failure rate.
  4. Model artifact is serialized with version metadata.
  5. Raw-input contract document defines fields, types, and plausible operational ranges.
**Plans**: 1 plan (02-01)

Plans:
- [ ] 02-01: Implement feature engineering, model training pipeline, and input contract document.

### Phase 3: Prediction Service & Parity Verification
**Goal**: Build and test the FastAPI serving application exposing `/predict`, `/health`, and `/version`, with robust Pydantic validation and 50-sample offline prediction parity.
**Depends on**: Phase 2
**Requirements**: API-01, API-02, API-03, API-04, API-05
**Success Criteria**:
  1. Service loads model artifact once at startup (lifespan event).
  2. Single and batch prediction requests return predictions without error.
  3. Invalid requests (missing fields, out-of-range sensor values) return clear 422 errors and never crash the process.
  4. Test suite verifies running service output matches offline model output on 50 sample rows.
**Plans**: 1 plan (03-01)

Plans:
- [ ] 03-01: Build FastAPI service with Pydantic validation, startup loader, and parity test suite.

### Phase 4: Containerised Deployment Stack
**Goal**: Containerize the service with Docker and Docker Compose, establish automated restart policies, and verify single-command deployment.
**Depends on**: Phase 3
**Requirements**: DOCKER-01, DOCKER-02, DOCKER-03, DOCKER-04
**Success Criteria**:
  1. Docker image is built with a version tag (`tower-serving:v1`).
  2. `docker compose up -d` brings up the entire stack with a single command.
  3. Service automatically restarts on container process failure (`restart: unless-stopped`).
  4. Deployment instructions documented for clean clone reproduction on the server.
**Plans**: 1 plan (04-01)

Plans:
- [ ] 04-01: Create Dockerfile, docker-compose.yml, restart configuration, and deployment documentation.

### Phase 5: Prometheus & Grafana Monitoring
**Goal**: Expose Prometheus metrics, provision reproducible Grafana dashboards, configure 2 alert conditions, and trigger live alerts with captured evidence.
**Depends on**: Phase 4
**Requirements**: MON-01, MON-02, MON-03, MON-04
**Success Criteria**:
  1. FastAPI exposes `/metrics` capturing request rate, latency percentiles, error count, and failure prediction count.
  2. Grafana dashboard is provisioned via yaml/json configuration (no manual-only creation).
  3. Panels display request rate, p50/p95/p99 latency, error rate, failure ratio, and host/container CPU/RAM.
  4. Two Prometheus alerts (e.g. HighLatency and HighFailureRate) are defined and triggered with evidence.
**Plans**: 1 plan (05-01)

Plans:
- [ ] 05-01: Instrument metrics, provision Grafana dashboard, configure and fire alert rules.

### Phase 6: Load Testing & Bottleneck Optimization
**Goal**: Execute Locust load tests across 10, 100, 500 users using `load_test_requests.csv`, diagnose bottleneck with live metrics, implement 1 optimization, and document before/after comparison.
**Depends on**: Phase 5
**Requirements**: LOAD-01, LOAD-02, LOAD-03, LOAD-04, LOAD-05
**Success Criteria**:
  1. Locust script simulates realistic traffic using `load_test_requests.csv`.
  2. Throughput, p50/p95/p99 latency, and error rates measured at 10, 100, 500 concurrency + sudden spike.
  3. Breaking point is explicitly observed and documented.
  4. Bottleneck diagnosed using Prometheus/Grafana and server metrics.
  5. 1 performance improvement applied, re-tested, and documented in a Before-vs-After results table.
**Plans**: 1 plan (06-01)

Plans:
- [ ] 06-01: Execute Locust load test suite, diagnose bottleneck, implement optimization, and re-test.

### Phase 7: Automated Health Checks & Self-Healing
**Goal**: Deploy scheduled Bash watchdog script via cron with timestamped logging, log rotation, anti-restart loop prevention, and demonstrated auto-recovery.
**Depends on**: Phase 4
**Requirements**: AUTO-01, AUTO-02, AUTO-03, AUTO-04, AUTO-05
**Success Criteria**:
  1. Bash watchdog script queries `/health` on a schedule.
  2. Log file contains timestamped checks, failure detection, restart trigger, and recovery time.
  3. Log rotation is configured and tested.
  4. Watchdog avoids infinite restart loops if service fails persistently.
  5. Deliberately killing the container triggers automatic detection and recovery.
**Plans**: 1 plan (07-01)

Plans:
- [ ] 07-01: Create and verify health check watchdog script, cron entry, log rotation, and recovery test.

### Phase 8: Capacity Defense Memo & Final Deliverables
**Goal**: Write the 1-page capacity and alert-threshold defense memo citing empirical Task 6 numbers, finalize the 25-command log, and package demonstration assets.
**Depends on**: Phase 5, Phase 6, Phase 7
**Requirements**: CAP-01, CAP-02, CAP-03
**Success Criteria**:
  1. 1-page capacity-and-alerting memo cites exact Task 6 measured p95 latency and error rate for an explicit peak RPS.
  2. Both alert thresholds are defended against plausible tighter/looser alternatives.
  3. Command log reaches >=25 distinct Linux commands with contextual justifications.
  4. Short design report and demonstration checklist prepared for team walkthrough.
**Plans**: 1 plan (08-01)

Plans:
- [ ] 08-01: Write capacity defense memo, complete 25-command log, and package project deliverables.

---
*Roadmap created: 2026-10-23*
