# Plan 01-01: Linux Server Provisioning & Environment Setup

## Goal
Establish remote Linux server access via SSH, configure file permissions demonstration, and initiate the 25-command operational log.

## Requirements
- SRV-01: Remote Linux server instance provisioned with accessible SSH key-based authentication.
- SRV-02: File permission demonstration implemented (restricted directory/file with read-only group access).
- SRV-03: Command log maintained containing at least 25 distinct Linux commands with specific project rationale.

## Proposed Changes
1. Document manual provisioning steps for AWS EC2 Free Tier (Ubuntu 24.04 LTS t2.micro / t3.micro) or Oracle Cloud Always Free VM.
2. Author `scripts/setup_permissions.sh` demonstrating user/group permission configuration on Linux.
3. Author `docs/linux_command_log.md` with initial verified commands (navigation, permissions, processes, log searching, disk/memory monitoring).

## Verification Commands
- `ssh -i <key.pem> ubuntu@<server-ip> "uname -a"`
- `bash scripts/setup_permissions.sh`
- Verification of 25 distinct commands in `docs/linux_command_log.md`.
