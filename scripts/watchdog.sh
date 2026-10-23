#!/usr/bin/env bash
# ==============================================================================
# Tower Serving Stack - Automated Health Check & Self-Healing Watchdog
# Task 7 Implementation:
# 1. Scheduled health check against /health endpoint
# 2. Timestamped logging with explicit ISO timestamps
# 3. Automatic container/process restart upon failure
# 4. Anti-restart loop protection (prevents infinite thrashing if corrupted)
# 5. Log rotation (rotates when log reaches threshold)
# ==============================================================================

set -euo pipefail

SERVICE_URL="${SERVICE_URL:-http://localhost:8000/health}"
LOG_DIR="${LOG_DIR:-/var/log/tower-watchdog}"
LOG_FILE="${LOG_DIR}/watchdog.log"
STATE_FILE="/tmp/tower_watchdog_state.json"
MAX_CONSECUTIVE_RESTARTS=3
MAX_LOG_SIZE_BYTES=$((500 * 1024)) # 500 KB rotation threshold
MAX_ROTATED_FILES=5

# Ensure log directory exists
mkdir -p "${LOG_DIR}"

log_msg() {
    local level="$1"
    local message="$2"
    local timestamp
    timestamp="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
    echo "[${timestamp}] [${level}] ${message}" | tee -a "${LOG_FILE}"
}

# --- 1. Built-in Log Rotation ---
rotate_logs_if_needed() {
    if [[ -f "${LOG_FILE}" ]]; then
        local current_size
        current_size=$(stat -c%s "${LOG_FILE}" 2>/dev/null || stat -f%z "${LOG_FILE}" 2>/dev/null || echo 0)
        if [[ "${current_size}" -ge "${MAX_LOG_SIZE_BYTES}" ]]; then
            log_msg "INFO" "Log size (${current_size} bytes) exceeded threshold (${MAX_LOG_SIZE_BYTES} bytes). Performing log rotation..."
            for ((i = MAX_ROTATED_FILES - 1; i >= 1; i--)); do
                if [[ -f "${LOG_FILE}.${i}" ]]; then
                    mv "${LOG_FILE}.${i}" "${LOG_FILE}.$((i + 1))"
                fi
            done
            mv "${LOG_FILE}" "${LOG_FILE}.1"
            touch "${LOG_FILE}"
            log_msg "INFO" "Log rotation complete. Fresh log initialized."
        fi
    fi
}

# --- 2. State Management for Anti-Restart Loop ---
get_failure_count() {
    if [[ -f "${STATE_FILE}" ]]; then
        grep -o '"failures":[0-9]*' "${STATE_FILE}" | cut -d':' -f2 || echo 0
    else
        echo 0
    fi
}

set_failure_count() {
    local count="$1"
    echo "{\"failures\": ${count}, \"last_updated\": \"$(date -u +"%Y-%m-%dT%H:%M:%SZ")\"}" > "${STATE_FILE}"
}

# Run log rotation check first
rotate_logs_if_needed

# --- 3. Health Probe ---
HTTP_RESPONSE=$(curl -s -w "\n%{http_code}" --max-time 4 "${SERVICE_URL}" 2>/dev/null || echo -e '{"error":"connect_failed"}\n000')
HTTP_BODY=$(echo "${HTTP_RESPONSE}" | head -n -1)
HTTP_CODE=$(echo "${HTTP_RESPONSE}" | tail -n 1)

if [[ "${HTTP_CODE}" == "200" ]] && [[ "${HTTP_BODY}" == *"healthy"* ]] && [[ "${HTTP_BODY}" == *"true"* ]]; then
    log_msg "INFO" "Health check PASSED: Status 200, Service healthy and model loaded."
    set_failure_count 0
    exit 0
fi

# --- 4. Failure Handling & Anti-Restart Loop ---
CONSECUTIVE_FAILURES=$(get_failure_count)
CONSECUTIVE_FAILURES=$((CONSECUTIVE_FAILURES + 1))
set_failure_count "${CONSECUTIVE_FAILURES}"

log_msg "CRITICAL" "Health check FAILED! HTTP Status: ${HTTP_CODE}, Response: ${HTTP_BODY} (Consecutive failures: ${CONSECUTIVE_FAILURES})"

if [[ "${CONSECUTIVE_FAILURES}" -gt "${MAX_CONSECUTIVE_RESTARTS}" ]]; then
    log_msg "FATAL" "ANTI-RESTART LOOP TRIGGERED! Consecutive restarts exceeded limit (${MAX_CONSECUTIVE_RESTARTS}). Halting automated restart to prevent system thrashing. Manual on-call inspection required."
    exit 2
fi

# --- 5. Automatic Restart & Recovery Timing ---
log_msg "WARN" "Initiating automated recovery restart (Attempt ${CONSECUTIVE_FAILURES}/${MAX_CONSECUTIVE_RESTARTS})..."
RESTART_START_TIME=$(date +%s)

# Trigger restart: Docker container if running in docker, or fallback to uvicorn process
if command -v docker >/dev/null 2>&1 && docker ps -q -f name=tower-api | grep -q .; then
    docker restart tower-api >/dev/null 2>&1 || true
    log_msg "INFO" "Issued 'docker restart tower-api'"
else
    # Fallback process restart for local testing
    pkill -f "uvicorn.*app:app" || true
    nohup python -m uvicorn app:app --host 0.0.0.0 --port 8000 --app-dir src >/tmp/tower_serving_recovery.log 2>&1 &
    log_msg "INFO" "Restarted local uvicorn background process"
fi

# Poll until service recovers or 30s timeout
RECOVERED=false
for i in {1..30}; do
    sleep 1
    CHECK_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 2 "${SERVICE_URL}" 2>/dev/null || echo "000")
    if [[ "${CHECK_CODE}" == "200" ]]; then
        RECOVERY_TIME=$(( $(date +%s) - RESTART_START_TIME ))
        log_msg "RECOVERY" "SUCCESS! Service recovered and responding healthy at ${SERVICE_URL} in ${RECOVERY_TIME}s."
        RECOVERED=true
        break
    fi
done

if [[ "${RECOVERED}" == "false" ]]; then
    log_msg "ERROR" "Recovery timeout! Service failed to return HTTP 200 within 30 seconds."
    exit 1
fi
