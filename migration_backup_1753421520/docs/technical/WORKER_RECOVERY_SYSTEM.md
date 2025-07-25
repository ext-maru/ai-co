# Worker Auto-Recovery System

**Deployed**: 2025-07-07 11:35:05
**Version**: 1.0.0

## Quick Start

### CLI Usage
```bash
# Check system status
python3 commands/ai_worker_recovery.py status

# Start monitoring
python3 commands/ai_worker_recovery.py start

# Manually recover a worker
python3 commands/ai_worker_recovery.py recover --worker task_worker
```

### Service Management
```bash
# Start as service
sudo systemctl start worker-recovery

# Check service status
sudo systemctl status worker-recovery

# View logs
sudo journalctl -u worker-recovery -f
```

### Configuration
Edit `/home/aicompany/ai_co/config/worker_recovery.yaml` to adjust settings.

## Features
- Automatic health monitoring
- Multiple recovery strategies
- State preservation
- Slack notifications
- Elder Council integration

## Troubleshooting
- Check logs in `/home/aicompany/ai_co/logs/`
- Review saved states in `/home/aicompany/ai_co/data/worker_states/`
- Elder notifications in `/home/aicompany/ai_co/knowledge_base/elder_notifications/`
