# 🐳 Docker Management API Documentation

**Phase 1 Week 2 Day 13-14 Implementation**  
**Task ID**: todo_27  
**Status**: Completed  
**Coordinated by**: 4 Sages System

---

## 📋 Overview

The Docker Management API provides RESTful endpoints for managing Docker containers, images, and templates within the AI Company infrastructure. This API integrates with the existing Docker Template Manager and follows the 4 Sages coordination principles.

## 🚀 Getting Started

### Prerequisites
- Docker installed and running
- Python 3.8+
- Flask framework
- docker-py library

### Installation
```bash
pip install docker flask
```

### Starting the API
```bash
cd /home/aicompany/ai_co
./start_flask_docker_api.sh
```

The API will be available at: `http://localhost:5555/api/docker`

## 📚 API Endpoints

### Health Check
```
GET /api/docker/health
```
Returns the health status of the Docker API.

**Response:**
```json
{
  "status": "healthy",
  "docker_available": true,
  "timestamp": "2025-07-06T20:50:00",
  "sage_coordination": "active"
}
```

### Container Management

#### List Containers
```
GET /api/docker/containers?all=true&status=running
```
Lists all containers with optional filters.

**Query Parameters:**
- `all` (boolean): Show all containers (default: false)
- `status` (string): Filter by status (running, exited, etc.)
- `label` (string): Filter by label

#### Get Container Details
```
GET /api/docker/containers/{container_id}
```
Returns detailed information about a specific container.

#### Create Container
```
POST /api/docker/containers
```
Creates a new container from a template or custom configuration.

**Request Body (Template):**
```json
{
  "template": "web_api",
  "project_type": "WEB_API",
  "security_level": "DEVELOPMENT",
  "name": "my-api-container",
  "start": true
}
```

**Request Body (Custom):**
```json
{
  "image": "python:3.9",
  "name": "custom-container",
  "environment": {
    "ENV_VAR": "value"
  },
  "ports": {
    "8080/tcp": "8080"
  },
  "volumes": ["/data:/app/data"],
  "command": "python app.py",
  "start": false
}
```

#### Start Container
```
POST /api/docker/containers/{container_id}/start
```
Starts a stopped container.

#### Stop Container
```
POST /api/docker/containers/{container_id}/stop
```
Stops a running container.

**Request Body (Optional):**
```json
{
  "timeout": 10
}
```

#### Remove Container
```
DELETE /api/docker/containers/{container_id}?force=true
```
Removes a container.

**Query Parameters:**
- `force` (boolean): Force removal of running container

#### Get Container Logs
```
GET /api/docker/containers/{container_id}/logs?tail=100&timestamps=true
```
Retrieves container logs.

**Query Parameters:**
- `tail` (string): Number of lines or "all" (default: "all")
- `since` (string): Show logs since timestamp
- `timestamps` (boolean): Include timestamps (default: false)

### Image Management

#### List Images
```
GET /api/docker/images
```
Lists all Docker images.

### Template Management

#### List Templates
```
GET /api/docker/templates
```
Lists available Docker templates from the Template Manager.

**Response:**
```json
{
  "templates": [
    {
      "name": "web_api_fastapi",
      "project_type": "WEB_API",
      "runtime": "PYTHON",
      "security_level": "DEVELOPMENT",
      "base_image": "python:3.9-slim",
      "ports": ["8000:8000"],
      "description": "WEB_API project with DEVELOPMENT security"
    }
  ],
  "count": 15,
  "timestamp": "2025-07-06T20:50:00"
}
```

### System Information

#### Get System Info
```
GET /api/docker/system/info
```
Returns Docker system information.

**Response:**
```json
{
  "docker_version": "24.0.7",
  "api_version": "1.43",
  "containers": 10,
  "containers_running": 5,
  "containers_paused": 0,
  "containers_stopped": 5,
  "images": 20,
  "driver": "overlay2",
  "memory_total": 8589934592,
  "operating_system": "Ubuntu 22.04",
  "architecture": "x86_64",
  "timestamp": "2025-07-06T20:50:00"
}
```

## 🔒 Security Features

### Container Labels
All containers created through this API are automatically labeled:
- `ai.company.managed`: "true"
- `ai.company.created_by`: "docker_api"
- `ai.company.created_at`: ISO timestamp
- `ai.company.sage_coordination`: "enabled"

### Security Levels
When using templates, the following security levels are available:
- `SANDBOX`: Maximum isolation
- `RESTRICTED`: Limited capabilities
- `DEVELOPMENT`: Standard development environment
- `TRUSTED`: Full capabilities

## 🧪 Testing

Run the test suite:
```bash
python3 test_docker_api.py
```

## 🤝 Integration with 4 Sages

This API follows the 4 Sages coordination principles:

1. **Task Sage**: Manages container lifecycle tasks
2. **Knowledge Sage**: Stores container patterns and best practices
3. **Incident Sage**: Monitors container health and handles failures
4. **RAG Sage**: Analyzes container usage patterns

## 📊 Monitoring

The API provides monitoring through:
- Health check endpoints
- Container statistics
- System information
- Detailed logging

## 🚨 Error Handling

All endpoints return appropriate HTTP status codes:
- `200`: Success
- `201`: Created
- `400`: Bad Request
- `404`: Not Found
- `500`: Internal Server Error
- `503`: Service Unavailable (Docker not available)

Error responses include detailed messages:
```json
{
  "error": "Container not found"
}
```

## 🔄 Next Steps

Future enhancements planned:
1. WebSocket support for real-time logs
2. Container metrics dashboard
3. Automated container scheduling
4. Integration with CI/CD pipelines
5. Multi-host Docker Swarm support

---

**Created by**: Claude Code Instance  
**Reviewed by**: 4 Sages System  
**Date**: 2025-07-06