#!/bin/bash
# Register Elder Tree services with Consul

set -e

CONSUL_URL="http://localhost:8500/v1/agent/service/register"

# Function to register a service
register_service() {
    local name=$1
    local port=$2
    local tags=$3
    
    echo "Registering $name on port $port..."
    
    curl -X PUT $CONSUL_URL -H "Content-Type: application/json" -d @- <<EOF
{
  "ID": "$name",
  "Name": "$name",
  "Tags": [$tags],
  "Port": $port,
  "Check": {
    "HTTP": "http://localhost:$port/health",
    "Interval": "10s",
    "Timeout": "5s"
  }
}
EOF
    
    echo "Registered $name"
}

# Register 4 Sages
register_service "knowledge-sage" 50051 '"sage","ai","knowledge"'
register_service "task-sage" 50052 '"sage","ai","task"'
register_service "incident-sage" 50053 '"sage","ai","incident"'
register_service "rag-sage" 50054 '"sage","ai","rag"'

# Register Elder Flow
register_service "elder-flow" 50100 '"orchestrator","workflow"'

# Register Servants
register_service "code-crafter" 60101 '"servant","dwarf","code"'
register_service "research-wizard" 60102 '"servant","rag_wizard","research"'
register_service "quality-guardian" 60103 '"servant","elf","quality"'
register_service "crisis-responder" 60104 '"servant","incident_knight","crisis"'

echo "All services registered with Consul!"