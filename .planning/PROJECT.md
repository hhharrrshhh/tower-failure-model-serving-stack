# Project 2: Tower-Failure Model on a Linux Server: Deployed, Load-Tested and Monitored

## What This Is

An end-to-end MLOps serving and operations stack for predicting mobile tower failures within 48 hours. The system takes a machine learning model from raw sensor history to a containerized, monitored production service on a remote Linux server, proven under peak simulated traffic, guarded by automated self-healing routines, and defended with measured empirical capacity benchmarks.

## Core Value

Provide a verified, reproducible, containerized prediction and monitoring pipeline deployed on a remote Linux server that survives peak traffic, recovers automatically from failure, and provides full empirical defense for serving capacity and alerting thresholds.

## Requirements

### Validated

(None yet — execute phases to validate)

### Active

- [ ] **Task 1: Linux Server Setup & Command Logging** — Establish remote access to a Linux server, configure user/group permissions, and maintain a 25-command operational log.
- [ ] **Task 2: Feature Engineering & Model Training** — Build a single reusable feature module, train failure prediction model on `telecom_tower_failure.csv` addressing class imbalance (~20.8%), save versioned model artifact, document input contract.
- [ ] **Task 3: Production Prediction Service** — Develop FastAPI service exposing `/predict` (single and batch), `/health`, `/version`, with Pydantic validation, startup-only model loading, and matching offline predictions on 50 sample rows.
- [ ] **Task 4: Containerised Deployment** — Package service, Prometheus, and Grafana in Docker Compose with restart policies; deploy to remote Linux server with single-command startup.
- [ ] **Task 5: Monitoring & Alerting Stack** — Instrument service for RPS, latency percentiles (p50, p95, p99), error rate, failure prediction ratio, and system resources; provision Grafana dashboard and 2 Prometheus alerts.
- [ ] **Task 6: Load Testing & Bottleneck Diagnosis** — Execute Locust load tests at 10, 100, 500 concurrency using `load_test_requests.csv`; identify breaking point, diagnose bottleneck with metrics, implement 1 optimization, and record before/after table.
- [ ] **Task 7: Automated Health Checks & Recovery** — Scheduled Bash watchdog routine via cron with timestamped logging, log rotation, anti-restart loop prevention, and demonstrated auto-recovery.
- [ ] **Task 8: Capacity & Alert-Threshold Defense Memo** — 1-page operational memo defending server sizing and alert thresholds using measured Task 6 load-test metrics.

### Out of Scope

- CI/CD quality gate pipelines (Project 1 scope)
- Drift-triggered automated retraining pipelines (Project 3 scope)
- Full MLflow tracking server setup (Project 4 scope)
- Paid cloud infrastructure or proprietary monitoring SaaS (Datadog/New Relic)
- Public unauthenticated internet exposure

## Context

- **Academic Context**: Elective II: Machine Learning Operations (MLOps), Semester III. Prepared by Dr. Santosh Kumar.
- **Group 12**: Harsh Gharat (B032) & Manav Thakkar (B055).
- **Dataset**: `project2_tower_serving/telecom_tower_failure.csv` (1,500 rows, 10 columns, 20.8% positive failure rate, missing values in 4 columns) and `project2_tower_serving/load_test_requests.csv` (300 rows, 9 raw feature columns).
- **Academic Integrity**: All deliverables, code, dashboards, test results, and memos must be genuinely run, measured, and understood by the team. AI is used solely for assistance, planning, syntax lookup, and debugging.

## Constraints

- **Timeframe**: Rapid turnaround targeting complete implementation within a 6-hour execution window.
- **Platform**: Local development on Windows with WSL2/Ubuntu + Docker, final remote deployment on a free Linux server (e.g. AWS EC2 free-tier / Oracle Cloud Always Free or equivalent SSH-accessible VM).
- **Free-Tier Only**: Zero budget, strictly open-source tooling (FastAPI, Docker, Prometheus, Grafana, Locust, Bash).
- **Parity Rule**: Exact same feature engineering code used at training time and serving time.
- **Zero Fabrication**: All benchmarks, latency percentiles, error rates, and screenshots must be empirically measured.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| FastAPI + Pydantic v2 | High-performance async serving, native OpenAPI documentation, automatic validation, straightforward Prometheus instrumentation | — Pending |
| Scikit-learn Pipeline with Joblib | Self-contained, robust preprocessing (imputation + scaling + classifier) prevents training-serving skew | — Pending |
| Docker Compose Stack | Single-command start for service, Prometheus, and Grafana with network isolation | — Pending |
| Locust for Load Testing | Python-native, handles `load_test_requests.csv` payloads cleanly, supports concurrency ramping and headless metric output | — Pending |
| AWS EC2 / Oracle Cloud free Linux VM | Fastest path to satisfy remote Linux server and SSH requirement within 6-hour deadline | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition**:
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

---
*Last updated: 2026-10-23 after project initialization*
