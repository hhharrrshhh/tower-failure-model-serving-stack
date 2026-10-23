#!/usr/bin/env bash
# ==============================================================================
# Tower Serving Stack - File Permissions Demonstration
# Task 1 Acceptance Criterion:
# "A permissions example is demonstrated, for instance a file that one group
#  may read but not modify."
# ==============================================================================

set -euo pipefail

echo "=== [1] Creating Demonstration Group & User ==="
sudo groupadd -f towerops
if ! id -u opsengineer >/dev/null 2>&1; then
    sudo useradd -m -g towerops -s /bin/bash opsengineer
    echo "[✓] Created user 'opsengineer' in group 'towerops'"
else
    echo "[✓] User 'opsengineer' already exists"
fi

DEMO_DIR="/tmp/tower_permissions_demo"
sudo mkdir -p "${DEMO_DIR}"

echo "=== [2] Creating Sensitive Configuration File ==="
CONFIG_FILE="${DEMO_DIR}/production_config.env"
echo "API_SECRET_KEY=tower_internal_secret_998234" | sudo tee "${CONFIG_FILE}" >/dev/null
echo "MODEL_THRESHOLD=0.45" | sudo tee -a "${CONFIG_FILE}" >/dev/null

echo "=== [3] Configuring Group Read-Only Ownership & Permissions ==="
# Owner: root (rw-), Group: towerops (r--), Others: none (---)
sudo chown root:towerops "${CONFIG_FILE}"
sudo chmod 640 "${CONFIG_FILE}"

echo "[✓] Configured permissions: $(ls -l "${CONFIG_FILE}")"

echo "=== [4] Demonstration Test: Group Member Read Test ==="
if sudo -u opsengineer cat "${CONFIG_FILE}" >/dev/null 2>&1; then
    echo "[SUCCESS] opsengineer (group towerops) can READ ${CONFIG_FILE}"
else
    echo "[FAILED] opsengineer was unable to read"
    exit 1
fi

echo "=== [5] Demonstration Test: Group Member Modify Test (Expected to Fail) ==="
if sudo -u opsengineer bash -c "echo 'MALICIOUS_OVERWRITE=1' >> ${CONFIG_FILE}" 2>/dev/null; then
    echo "[FAILED] opsengineer was able to modify ${CONFIG_FILE}!"
    exit 1
else
    echo "[SUCCESS] Permission denied! opsengineer CANNOT MODIFY ${CONFIG_FILE}"
fi

echo "=== [6] Demonstration Test: Non-Member Access (Expected to Fail) ==="
if sudo -u nobody cat "${CONFIG_FILE}" 2>/dev/null; then
    echo "[FAILED] 'nobody' was able to read ${CONFIG_FILE}!"
    exit 1
else
    echo "[SUCCESS] Permission denied! Others cannot read ${CONFIG_FILE}"
fi

echo ""
echo "=============================================================================="
echo "Permissions demonstration completed successfully!"
echo "Target file: ${CONFIG_FILE}"
echo "Permissions: -rw-r----- (640) owned by root:towerops"
echo "=============================================================================="
