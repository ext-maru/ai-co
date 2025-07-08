#!/bin/bash
#!/bin/bash
cd /home/aicompany/ai_co
python3 check_slack_project_status.py > slack_project_status_$(date +%Y%m%d_%H%M%S).log
cat slack_project_status_*.log | tail -n 100
