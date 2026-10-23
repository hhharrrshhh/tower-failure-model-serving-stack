# Remote Linux Server Setup Guide (5-Minute Deployment)

**Goal:** Fulfill Task 1 & Task 4 requirement for deploying the tower prediction stack to a remote Linux server accessible via SSH.

---

## Recommended Free Server Option: AWS EC2 (Free Tier)

### Step 1: Launch Instance in AWS Console
1. Log in to [AWS Console](https://console.aws.amazon.com/ec2).
2. Click **Launch Instance**:
   - **Name:** `tower-serving-server`
   - **AMI:** Ubuntu Server 24.04 LTS (HVM), SSD Volume Type (Free tier eligible)
   - **Instance Type:** `t2.micro` (or `t3.micro` if in supported region)
   - **Key Pair:** Create a new key pair (e.g. `tower-key.pem`) and download to your machine.
   - **Network Settings (Firewall / Security Group):**
     - Allow SSH traffic from Anywhere (Port 22)
     - Allow Custom TCP Port `8000` (FastAPI) from Anywhere (or your IP)
     - Allow Custom TCP Port `9090` (Prometheus) from your IP
     - Allow Custom TCP Port `3000` (Grafana) from your IP
3. Click **Launch Instance**.
4. Note the **Public IPv4 address** (e.g., `54.198.x.x`).

---

## Step 2: Connect via SSH
From your Windows PowerShell or Terminal:
```bash
# Set secure permission on the key file (if in Linux/WSL)
chmod 400 ~/.ssh/tower-key.pem

# SSH into the server
ssh -i ~/.ssh/tower-key.pem ubuntu@<PUBLIC_IP>
```

---

## Step 3: Install Docker & Docker Compose (Single Command on Server)
Once logged into your server, run:
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker ubuntu
sudo systemctl enable docker
sudo systemctl start docker

# Verify Docker is running
docker --version
docker compose version
```

---

## Step 4: Clone and Launch the Serving Stack
```bash
# Clone the repository
git clone <YOUR_GIT_REPO_URL> /opt/tower-service
cd /opt/tower-service

# Single-command start for service, Prometheus, and Grafana
docker compose up -d

# Verify containers are healthy
docker compose ps
curl http://localhost:8000/health
```
