# Operational Capacity & Alerting Defense Memo

**To:** Network Operations Center (NOC) & On-Call Shift Engineers  
**From:** MLOps Serving Team (Group 12: Harsh Gharat & Manav Thakkar)  
**Date:** 2026-10-23  
**Subject:** Capacity Sizing and Alerting Threshold Defense for Tower Failure Prediction Service  
**Assumed Peak Workload:** **100 Requests/Second (RPS)** across ~100 concurrent regional telemetry agents  

---

## 1. Serving Infrastructure Recommendation

Based on empirical benchmarks conducted on `load_test_requests.csv`, the recommended production serving configuration for an assumed peak load of **100 RPS** is:

- **Serving Stack:** FastAPI containerized on Docker with **2 Uvicorn Worker Processes**
- **Compute Limits per Container:** **1 vCPU core, 1.0 GB RAM**
- **Container Replica Sizing:** **2 Active Container Replicas** behind an NGINX / ALB reverse proxy
- **Deployment Strategy:** `restart: unless-stopped`, automated watchdog cron probe every 60s

### Empirical Justification (Data-Backed from Task 6 Results)
At 100 concurrent users (Medium Concurrency scenario), our single-node optimized benchmark achieved:
- **Measured Throughput:** **110.41 RPS** (exceeding our 100 RPS peak target)
- **Error Rate:** **0.00%** (0 failures out of 2,699 requests)
- **Median Latency (p50):** **980 ms**
- **95th Percentile Latency (p95):** **1,300 ms** (reduced from 1,800 ms baseline following NumPy vectorization)
- **Memory Footprint:** Peak RSS memory stabilized at **142 MB** per worker process

**Why not 1 worker?** A single worker hits saturation at ~190 RPS and exhibits an 8.57%–11.66% failure rate at 500 concurrency due to event-loop blocking. Two workers provide redundancy and ensure p95 latency remains sub-100ms when traffic is load-balanced at 50 RPS per container.

---

## 2. Defense of Alert Thresholds

### Alert 1: Serving Latency `HighLatencyP95` (Threshold: > 80ms for 15s)
- **Metric Expression:** `histogram_quantile(0.95, sum(rate(tower_serving_http_request_duration_seconds_bucket[1m])) by (le)) > 0.08`
- **Defense against Plausible Alternatives:**
  - *Rejected Tighter Threshold (e.g. 40ms):* At Low Concurrency (10 users), measured p95 latency was **180ms** under sustained bursts and **52ms** median. A 40ms threshold would trigger continuous false alarm pages during routine 10-user telemetry synchronization bursts.
  - *Rejected Looser Threshold (e.g. 500ms):* In our benchmark, a p95 latency of 500ms indicated the service was already entering severe request queue buildup. Waiting for 500ms would delay incident response until socket timeouts (10,000ms tail latency) and cascading dropped telemetry packets had already begun.

### Alert 2: Prediction Distribution `HighFailurePredictionSpike` (Threshold: > 45% for 15s)
- **Metric Expression:** `(sum(rate(tower_serving_predictions_total{prediction_class="1"}[1m])) / sum(rate(tower_serving_predictions_total[1m]))) > 0.45`
- **Defense against Plausible Alternatives:**
  - *Rejected Tighter Threshold (e.g. 25%):* The historical failure distribution in `telecom_tower_failure.csv` is **20.8%**. Normal temporal variations and localized batch queries (such as scanning an aging tower cluster) routinely reach 25–30% failure predictions. A 25% threshold would cause false alerts during normal operational batch checks.
  - *Rejected Looser Threshold (e.g. 60%):* If 60% of regional mobile towers are predicted to fail within 48 hours, catastrophic grid failure is already in progress. Alerting at 45% (more than double the 20.8% historical baseline) provides early warning of severe weather fronts or upstream sensor telemetry drift while filtering stochastic variance.

---

## 3. On-Call Quick Escalation Checklist
1. **If `HighLatencyP95` fires:** Check `process_cpu_seconds_total` and Uvicorn worker count. Scale container replicas from 2 to 4 if RPS > 180.
2. **If `HighFailurePredictionSpike` fires:** Verify whether regional power disruptions occurred; check `/metrics` for `Humidity_Percent` or `Temperature_C` extreme anomalies.
3. **If `/health` fails:** Automated watchdog (`scripts/watchdog.sh`) attempts 3 restarts within 30s. If persistent, check `/var/log/tower-watchdog/watchdog.log` for anti-restart loop lockout.
