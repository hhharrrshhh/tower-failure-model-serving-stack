# Linux Command Log: 25 Distinct Commands

**Project:** Project 2 - Tower-Failure Model on a Linux Server: Deployed, Load-Tested and Monitored  
**Task 1 Deliverable:** Acceptance Criteria — "The command log covers navigation, file permissions, process inspection, log searching and disk or memory monitoring. Keep a command log of at least 25 distinct Linux commands, each with a note on why it was needed in this project."

---

## Command Log Table

| # | Command | Category | Why It Was Needed in This Project | Example Invocation |
|---|---|---|---|---|
| 1 | `ssh` | Remote Access | Securely connecting to the remote Ubuntu cloud VM where the containerized service is deployed. | `ssh -i ~/.ssh/tower-key.pem ubuntu@54.198.22.10` |
| 2 | `ls` | Navigation | Inspecting files in the project root, artifacts directory, and Docker volumes. | `ls -la /opt/tower-service/artifacts` |
| 3 | `cd` | Navigation | Navigating between project modules, logs, and configuration directories. | `cd /opt/tower-service && pwd` |
| 4 | `pwd` | Navigation | Confirming current working directory before executing relative-path scripts. | `pwd` |
| 5 | `mkdir` | Navigation / Setup | Creating directories for logs, model artifacts, and Prometheus configuration. | `mkdir -p /var/log/tower-watchdog /opt/tower-service/artifacts` |
| 6 | `chmod` | Permissions | Setting least-privilege permissions on `production_config.env` (`640`) and making scripts executable (`+x`). | `chmod 640 /tmp/tower_permissions_demo/production_config.env` |
| 7 | `chown` | Permissions | Assigning ownership of config files to `root:towerops` to restrict modification rights. | `chown root:towerops /tmp/tower_permissions_demo/production_config.env` |
| 8 | `groupadd` | Permissions | Creating the dedicated `towerops` group for operations engineers. | `groupadd -f towerops` |
| 9 | `useradd` | Permissions | Creating the restricted demonstration user `opsengineer` belonging to group `towerops`. | `useradd -m -g towerops -s /bin/bash opsengineer` |
| 10 | `sudo` | Permissions / Exec | Running administrative provisioning commands and executing tests under another user with `sudo -u`. | `sudo -u opsengineer cat /tmp/tower_permissions_demo/production_config.env` |
| 11 | `ps` | Process Inspection | Checking whether Uvicorn/FastAPI or watchdog processes are actively running. | `ps aux \| grep uvicorn` |
| 12 | `top` / `htop` | Process Inspection | Monitoring live per-core CPU and memory utilization during concurrency load spikes. | `top -b -n 1 \| head -n 15` |
| 13 | `kill` | Process Control | Simulating a service crash by terminating container process for auto-recovery testing. | `kill -9 $(pgrep -f uvicorn \| head -n 1)` |
| 14 | `pgrep` | Process Inspection | Quickly finding the process ID of the Uvicorn worker or Python serving process. | `pgrep -l -f uvicorn` |
| 15 | `systemctl` | Process / Service | Managing Docker daemon service and viewing daemon logs. | `sudo systemctl status docker` |
| 16 | `grep` | Log Searching | Filtering watchdog logs for failure detection events, HTTP errors, or restart triggers. | `grep -E "CRITICAL\|UNHEALTHY\|RESTART" /var/log/tower-watchdog/watchdog.log` |
| 17 | `tail` | Log Searching | Streaming live health check results and uvicorn access logs in real time. | `tail -n 25 /var/log/tower-watchdog/watchdog.log` |
| 18 | `journalctl` | Log Searching | Inspecting system-level and container daemon logs during crash investigations. | `sudo journalctl -u docker.service --since "10 minutes ago" --no-pager` |
| 19 | `awk` | Log Searching / Metrics | Parsing response latency percentiles and error status codes from raw CSV/log files. | `awk -F',' '$3 ~ /5../ {print $1, $2, $3}' /var/log/tower-service/access.log` |
| 20 | `df` | Disk Monitoring | Checking available disk space to ensure Prometheus TSDB or rotated logs do not exhaust disk. | `df -h /var/log` |
| 21 | `free` | Memory Monitoring | Checking available system RAM before running 500-user concurrency tests to detect OOM risk. | `free -h` |
| 22 | `curl` | Network / Testing | Querying `/health`, `/version`, `/predict`, and `/metrics` directly from the server terminal. | `curl -s http://localhost:8000/health \| jq .` |
| 23 | `ss` / `netstat` | Network Monitoring | Verifying that ports 8000 (FastAPI), 9090 (Prometheus), and 3000 (Grafana) are listening. | `ss -tulpn \| grep -E '8000\|9090\|3000'` |
| 24 | `crontab` | Automation | Installing and inspecting the automated 1-minute watchdog cron job for Task 7 recovery. | `crontab -l` |
| 25 | `logrotate` | Log Management | Testing automated log rotation for `/var/log/tower-watchdog/watchdog.log` to prevent disk overflow. | `sudo logrotate -d /etc/logrotate.d/tower-watchdog` |

---

## Verification Evidence

All 25 commands have been mapped to specific workflows in Tasks 1–8:
- **Navigation & Inspection**: Commands 2, 3, 4, 5, 11, 14, 15
- **Permissions Demonstration**: Commands 6, 7, 8, 9, 10
- **Log Searching & Diagnostics**: Commands 16, 17, 18, 19
- **Disk & Memory Monitoring**: Commands 12, 20, 21
- **Network, Probing & Remote Access**: Commands 1, 22, 23
- **Automation & Log Rotation**: Commands 13, 24, 25
