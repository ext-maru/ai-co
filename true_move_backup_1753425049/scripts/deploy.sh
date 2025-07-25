#!/bin/bash

# Elders Guild CI/CD Deployment Script
# Created: 2025-07-11
# Author: Claude Elder

set -e

# Configuration
PROJECT_NAME="elders-guild"
DOCKER_COMPOSE_FILE="docker-compose.yml"
DOCKER_COMPOSE_PROD_FILE="docker-compose.prod.yml"
BACKUP_DIR="/tmp/elders-guild-backup"
LOG_FILE="/tmp/elders-guild-deploy.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1" | tee -a "$LOG_FILE"
}

warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1" | tee -a "$LOG_FILE"
}

# Function to check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."

    # Check Docker
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed"
        exit 1
    fi

    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        error "Docker Compose is not installed"
        exit 1
    fi

    # Check if running as root or with sudo
    if [[ $EUID -ne 0 ]]; then
        warning "Script not running as root. You may need sudo for Docker commands."
    fi

    log "Prerequisites check completed"
}

# Function to backup current deployment
backup_deployment() {
    log "Creating backup of current deployment..."

    # Create backup directory
    mkdir -p "$BACKUP_DIR"

    # Backup docker-compose files
    if [[ -f "$DOCKER_COMPOSE_FILE" ]]; then
        cp "$DOCKER_COMPOSE_FILE" "$BACKUP_DIR/docker-compose.yml.backup"
        log "Backed up docker-compose.yml"
    fi

    # Backup database
    if docker-compose ps postgres | grep -q "Up"; then
        log "Backing up database..."
        docker-compose exec -T postgres pg_dump -U elder_admin elders_guild > "$BACKUP_DIR/database_backup.sql"
        log "Database backup completed"
    fi

    # Backup volumes
    log "Backing up Docker volumes..."
    docker run --rm -v elders-guild_postgres_data:/data -v "$BACKUP_DIR":/backup alpine tar czf /backup/postgres_data.tar.gz -C /data .
    docker run --rm -v elders-guild_redis_data:/data -v "$BACKUP_DIR":/backup alpine tar czf /backup/redis_data.tar.gz -C /data .

    log "Backup completed. Files stored in $BACKUP_DIR"
}

# Function to run tests
run_tests() {
    log "Running tests..."

    # Unit tests
    log "Running unit tests..."
    python -m pytest tests/unit/ -v --tb=short

    # Integration tests (if environment supports it)
    if [[ -n "$RUN_INTEGRATION_TESTS" ]]; then
        log "Running integration tests..."
        python -m pytest tests/integration/ -v --tb=short
    fi

    log "Tests completed successfully"
}

# Function to build Docker images
build_images() {
    log "Building Docker images..."

    # Build main application image
    docker build -t "${PROJECT_NAME}:latest" .

    # Build for production if prod compose file exists
    if [[ -f "$DOCKER_COMPOSE_PROD_FILE" ]]; then
        docker build -t "${PROJECT_NAME}:prod" --target production .
    fi

    log "Docker images built successfully"
}

# Function to deploy services
deploy_services() {
    local env="$1"
    log "Deploying services for environment: $env"

    # Stop existing services
    log "Stopping existing services..."
    docker-compose down --remove-orphans

    # Pull latest images
    log "Pulling latest images..."
    docker-compose pull

    # Start services
    log "Starting services..."
    if [[ "$env" == "production" ]] && [[ -f "$DOCKER_COMPOSE_PROD_FILE" ]]; then
        docker-compose -f "$DOCKER_COMPOSE_PROD_FILE" up -d
    else
        docker-compose up -d
    fi

    log "Services deployed successfully"
}

# Function to wait for services to be ready
wait_for_services() {
    log "Waiting for services to be ready..."

    local max_attempts=30
    local attempt=1

    while [[ $attempt -le $max_attempts ]]; do
        log "Health check attempt $attempt/$max_attempts"

        # Check PostgreSQL
        if docker-compose exec -T postgres pg_isready -U elder_admin -d elders_guild &> /dev/null; then
            log "PostgreSQL is ready"
        else
            warning "PostgreSQL not ready yet"
            sleep 10
            ((attempt++))
            continue
        fi

        # Check Redis
        if docker-compose exec -T redis redis-cli ping &> /dev/null; then
            log "Redis is ready"
        else
            warning "Redis not ready yet"
            sleep 10
            ((attempt++))
            continue
        fi

        # Check API server
        if curl -f http://localhost:8001/api/v2/system/health &> /dev/null; then
            log "API server is ready"
            break
        else
            warning "API server not ready yet"
            sleep 10
            ((attempt++))
        fi
    done

    if [[ $attempt -gt $max_attempts ]]; then
        error "Services failed to become ready within timeout"
        return 1
    fi

    log "All services are ready"
}

# Function to run post-deployment tasks
post_deployment_tasks() {
    log "Running post-deployment tasks..."

    # Run database migrations
    log "Running database migrations..."
    docker-compose exec -T api-server python -m libs.elders_guild_db_manager --migrate

    # Initialize system data
    log "Initializing system data..."
    docker-compose exec -T api-server python -c "
import asyncio
from libs.elders_guild_event_bus import ElderGuildEventBus, EventType
from libs.elders_guild_db_manager import EldersGuildDatabaseManager, DatabaseConfig
import os

async def init_system():
    # Initialize database
    config = DatabaseConfig()
    db_manager = EldersGuildDatabaseManager(config)
    await db_manager.initialize()

    # Initialize event bus
    event_bus = ElderGuildEventBus(db_manager)
    await event_bus.initialize()

    # Publish system startup event
    await event_bus.publish_event(
        EventType.SYSTEM_STARTUP,
        source='deployment_script',
        data={'version': '1.0.0', 'environment': '${1:-development}'}
    )

    await event_bus.stop()
    await db_manager.close()

    print('System initialization completed')

asyncio.run(init_system())
"

    log "Post-deployment tasks completed"
}

# Function to verify deployment
verify_deployment() {
    log "Verifying deployment..."

    # Check service status
    log "Checking service status..."
    docker-compose ps

    # Check API endpoints
    log "Testing API endpoints..."

    # Health check
    if curl -f http://localhost:8001/api/v2/system/health; then
        log "Health check endpoint is working"
    else
        error "Health check endpoint failed"
        return 1
    fi

    # Version check
    if curl -f http://localhost:8001/api/v2/system/version; then
        log "Version endpoint is working"
    else
        error "Version endpoint failed"
        return 1
    fi

    # Check database connectivity
    log "Checking database connectivity..."
    if docker-compose exec -T postgres pg_isready -U elder_admin -d elders_guild; then
        log "Database is accessible"
    else
        error "Database is not accessible"
        return 1
    fi

    # Check Redis connectivity
    log "Checking Redis connectivity..."
    if docker-compose exec -T redis redis-cli ping; then
        log "Redis is accessible"
    else
        error "Redis is not accessible"
        return 1
    fi

    log "Deployment verification completed successfully"
}

# Function to rollback deployment
rollback_deployment() {
    log "Rolling back deployment..."

    # Stop current services
    docker-compose down --remove-orphans

    # Restore backup files
    if [[ -f "$BACKUP_DIR/docker-compose.yml.backup" ]]; then
        cp "$BACKUP_DIR/docker-compose.yml.backup" "$DOCKER_COMPOSE_FILE"
        log "Restored docker-compose.yml"
    fi

    # Restore database
    if [[ -f "$BACKUP_DIR/database_backup.sql" ]]; then
        log "Restoring database..."
        docker-compose up -d postgres
        sleep 10
        docker-compose exec -T postgres psql -U elder_admin -d elders_guild < "$BACKUP_DIR/database_backup.sql"
        log "Database restored"
    fi

    # Restore volumes
    if [[ -f "$BACKUP_DIR/postgres_data.tar.gz" ]]; then
        log "Restoring PostgreSQL data..."
        docker run --rm -v elders-guild_postgres_data:/data -v "$BACKUP_DIR":/backup alpine tar xzf /backup/postgres_data.tar.gz -C /data
    fi

    if [[ -f "$BACKUP_DIR/redis_data.tar.gz" ]]; then
        log "Restoring Redis data..."
        docker run --rm -v elders-guild_redis_data:/data -v "$BACKUP_DIR":/backup alpine tar xzf /backup/redis_data.tar.gz -C /data
    fi

    # Start services
    docker-compose up -d

    log "Rollback completed"
}

# Function to clean up
cleanup() {
    log "Cleaning up..."

    # Remove unused Docker images
    docker image prune -f

    # Remove unused volumes
    docker volume prune -f

    # Remove unused networks
    docker network prune -f

    log "Cleanup completed"
}

# Function to show usage
usage() {
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  deploy [env]     Deploy the application (env: development|production)"
    echo "  rollback         Rollback to previous deployment"
    echo "  test             Run tests only"
    echo "  build            Build Docker images only"
    echo "  backup           Create backup only"
    echo "  verify           Verify current deployment"
    echo "  cleanup          Clean up unused Docker resources"
    echo ""
    echo "Options:"
    echo "  --skip-tests     Skip running tests"
    echo "  --skip-backup    Skip creating backup"
    echo "  --force          Force deployment without confirmation"
    echo ""
    echo "Examples:"
    echo "  $0 deploy development"
    echo "  $0 deploy production --skip-tests"
    echo "  $0 rollback"
    echo "  $0 test"
}

# Main deployment function
main() {
    local command="$1"
    local environment="${2:-development}"

    # Parse options
    local skip_tests=false
    local skip_backup=false
    local force=false

    for arg in "$@"; do
        case $arg in
            --skip-tests)
                skip_tests=true
                ;;
            --skip-backup)
                skip_backup=true
                ;;
            --force)
                force=true
                ;;
        esac
    done

    # Create log file
    touch "$LOG_FILE"

    case "$command" in
        deploy)
            log "Starting deployment for environment: $environment"

            # Confirmation for production
            if [[ "$environment" == "production" ]] && [[ "$force" != true ]]; then
                echo -n "Are you sure you want to deploy to production? [y/N] "
                read -r response
                if [[ ! "$response" =~ ^[Yy]$ ]]; then
                    log "Deployment cancelled by user"
                    exit 0
                fi
            fi

            check_prerequisites

            if [[ "$skip_tests" != true ]]; then
                run_tests
            fi

            if [[ "$skip_backup" != true ]]; then
                backup_deployment
            fi

            build_images
            deploy_services "$environment"
            wait_for_services
            post_deployment_tasks "$environment"
            verify_deployment
            cleanup

            log "Deployment completed successfully!"
            ;;
        rollback)
            log "Starting rollback..."
            check_prerequisites
            rollback_deployment
            wait_for_services
            verify_deployment
            log "Rollback completed successfully!"
            ;;
        test)
            log "Running tests..."
            run_tests
            log "Tests completed!"
            ;;
        build)
            log "Building images..."
            check_prerequisites
            build_images
            log "Build completed!"
            ;;
        backup)
            log "Creating backup..."
            check_prerequisites
            backup_deployment
            log "Backup completed!"
            ;;
        verify)
            log "Verifying deployment..."
            verify_deployment
            log "Verification completed!"
            ;;
        cleanup)
            log "Cleaning up..."
            cleanup
            log "Cleanup completed!"
            ;;
        *)
            usage
            exit 1
            ;;
    esac
}

# Error handling
trap 'error "Deployment failed! Check $LOG_FILE for details"' ERR

# Run main function
main "$@"
