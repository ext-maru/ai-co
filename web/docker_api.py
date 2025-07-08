#!/usr/bin/env python3
"""
Docker Management API Blueprint
Phase 1 Week 2 Day 13-14: Docker管理API基盤構築
Following 4 Sages coordination principles
"""

import json
import logging
from datetime import datetime
from pathlib import Path
import sys
from typing import Dict, Any, List, Optional

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from flask import Blueprint, jsonify, request
import docker
from docker.errors import DockerException, APIError, NotFound

from libs.docker_template_manager import DockerTemplateManager
from libs.shared_enums import SecurityLevel, ProjectType, RuntimeEnvironment

# Create blueprint
docker_api = Blueprint('docker_api', __name__, url_prefix='/api/docker')

# Logging setup
logger = logging.getLogger(__name__)

# Docker client initialization
try:
    docker_client = docker.from_env()
    docker_available = True
except Exception as e:
    logger.error(f"Failed to connect to Docker: {e}")
    docker_client = None
    docker_available = False

# Template manager
template_manager = DockerTemplateManager()

@docker_api.route('/health', methods=['GET'])
def health_check():
    """Docker API health check endpoint"""
    return jsonify({
        'status': 'healthy' if docker_available else 'unavailable',
        'docker_available': docker_available,
        'timestamp': datetime.now().isoformat(),
        'sage_coordination': 'active'
    })

@docker_api.route('/containers', methods=['GET'])
def list_containers():
    """List all containers with optional filters"""
    if not docker_available:
        return jsonify({'error': 'Docker is not available'}), 503
    
    try:
        all_containers = request.args.get('all', 'false').lower() == 'true'
        filters = {}
        
        # Apply filters if provided
        if 'status' in request.args:
            filters['status'] = request.args.get('status')
        if 'label' in request.args:
            filters['label'] = request.args.get('label')
        
        containers = docker_client.containers.list(all=all_containers, filters=filters)
        
        container_list = []
        for container in containers:
            container_list.append({
                'id': container.short_id,
                'name': container.name,
                'status': container.status,
                'image': container.image.tags[0] if container.image.tags else 'unknown',
                'created': container.attrs['Created'],
                'ports': container.attrs.get('NetworkSettings', {}).get('Ports', {}),
                'labels': container.labels
            })
        
        return jsonify({
            'containers': container_list,
            'count': len(container_list),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error listing containers: {e}")
        return jsonify({'error': str(e)}), 500

@docker_api.route('/containers/<container_id>', methods=['GET'])
def get_container(container_id):
    """Get detailed information about a specific container"""
    if not docker_available:
        return jsonify({'error': 'Docker is not available'}), 503
    
    try:
        container = docker_client.containers.get(container_id)
        
        # Get container stats
        stats = container.stats(stream=False)
        
        return jsonify({
            'id': container.id,
            'short_id': container.short_id,
            'name': container.name,
            'status': container.status,
            'image': container.image.tags[0] if container.image.tags else 'unknown',
            'created': container.attrs['Created'],
            'started_at': container.attrs['State'].get('StartedAt'),
            'finished_at': container.attrs['State'].get('FinishedAt'),
            'exit_code': container.attrs['State'].get('ExitCode'),
            'ports': container.attrs.get('NetworkSettings', {}).get('Ports', {}),
            'labels': container.labels,
            'environment': container.attrs['Config'].get('Env', []),
            'mounts': container.attrs.get('Mounts', []),
            'stats': {
                'cpu_percent': stats.get('cpu_stats', {}).get('cpu_usage', {}).get('total_usage', 0),
                'memory_usage': stats.get('memory_stats', {}).get('usage', 0),
                'memory_limit': stats.get('memory_stats', {}).get('limit', 0)
            }
        })
        
    except NotFound:
        return jsonify({'error': f'Container {container_id} not found'}), 404
    except Exception as e:
        logger.error(f"Error getting container {container_id}: {e}")
        return jsonify({'error': str(e)}), 500

@docker_api.route('/containers', methods=['POST'])
def create_container():
    """Create a new container from template or custom configuration"""
    if not docker_available:
        return jsonify({'error': 'Docker is not available'}), 503
    
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Use template if specified
        if 'template' in data:
            template_name = data['template']
            project_type = ProjectType[data.get('project_type', 'GENERAL').upper()]
            security_level = SecurityLevel[data.get('security_level', 'DEVELOPMENT').upper()]
            
            # Generate Docker configuration from template
            template_config = template_manager.get_template(
                project_type=project_type,
                security_level=security_level
            )
            
            if not template_config:
                return jsonify({'error': 'Template not found'}), 404
            
            # Merge template with custom config
            image = template_config.base_image
            environment = template_config.environment_vars
            ports = {p.split(':')[0]: p.split(':')[1] for p in template_config.ports if ':' in p}
            volumes = template_config.volumes
            command = template_config.startup_command
            
        else:
            # Use custom configuration
            image = data.get('image')
            if not image:
                return jsonify({'error': 'Image name is required'}), 400
            
            environment = data.get('environment', {})
            ports = data.get('ports', {})
            volumes = data.get('volumes', [])
            command = data.get('command')
        
        # Container configuration
        container_config = {
            'image': image,
            'name': data.get('name'),
            'environment': environment,
            'ports': ports,
            'volumes': volumes,
            'detach': True,
            'labels': {
                'ai.company.managed': 'true',
                'ai.company.created_by': 'docker_api',
                'ai.company.created_at': datetime.now().isoformat(),
                'ai.company.sage_coordination': 'enabled'
            }
        }
        
        if command:
            container_config['command'] = command
        
        # Add resource limits if specified
        if 'resource_limits' in data:
            container_config['mem_limit'] = data['resource_limits'].get('memory')
            container_config['cpu_quota'] = data['resource_limits'].get('cpu_quota')
        
        # Create container
        container = docker_client.containers.create(**container_config)
        
        # Start container if requested
        if data.get('start', False):
            container.start()
            container.reload()
        
        return jsonify({
            'id': container.short_id,
            'name': container.name,
            'status': container.status,
            'created': True,
            'message': f'Container {container.name} created successfully'
        }), 201
        
    except APIError as e:
        logger.error(f"Docker API error: {e}")
        return jsonify({'error': f'Docker API error: {e.explanation}'}), 500
    except Exception as e:
        logger.error(f"Error creating container: {e}")
        return jsonify({'error': str(e)}), 500

@docker_api.route('/containers/<container_id>/start', methods=['POST'])
def start_container(container_id):
    """Start a stopped container"""
    if not docker_available:
        return jsonify({'error': 'Docker is not available'}), 503
    
    try:
        container = docker_client.containers.get(container_id)
        container.start()
        container.reload()
        
        return jsonify({
            'id': container.short_id,
            'name': container.name,
            'status': container.status,
            'message': f'Container {container.name} started successfully'
        })
        
    except NotFound:
        return jsonify({'error': f'Container {container_id} not found'}), 404
    except APIError as e:
        return jsonify({'error': f'Docker API error: {e.explanation}'}), 500
    except Exception as e:
        logger.error(f"Error starting container {container_id}: {e}")
        return jsonify({'error': str(e)}), 500

@docker_api.route('/containers/<container_id>/stop', methods=['POST'])
def stop_container(container_id):
    """Stop a running container"""
    if not docker_available:
        return jsonify({'error': 'Docker is not available'}), 503
    
    try:
        container = docker_client.containers.get(container_id)
        timeout = request.json.get('timeout', 10) if request.json else 10
        container.stop(timeout=timeout)
        container.reload()
        
        return jsonify({
            'id': container.short_id,
            'name': container.name,
            'status': container.status,
            'message': f'Container {container.name} stopped successfully'
        })
        
    except NotFound:
        return jsonify({'error': f'Container {container_id} not found'}), 404
    except Exception as e:
        logger.error(f"Error stopping container {container_id}: {e}")
        return jsonify({'error': str(e)}), 500

@docker_api.route('/containers/<container_id>/remove', methods=['DELETE'])
def remove_container(container_id):
    """Remove a container"""
    if not docker_available:
        return jsonify({'error': 'Docker is not available'}), 503
    
    try:
        container = docker_client.containers.get(container_id)
        force = request.args.get('force', 'false').lower() == 'true'
        container.remove(force=force)
        
        return jsonify({
            'id': container_id,
            'removed': True,
            'message': f'Container {container_id} removed successfully'
        })
        
    except NotFound:
        return jsonify({'error': f'Container {container_id} not found'}), 404
    except Exception as e:
        logger.error(f"Error removing container {container_id}: {e}")
        return jsonify({'error': str(e)}), 500

@docker_api.route('/containers/<container_id>/logs', methods=['GET'])
def get_container_logs(container_id):
    """Get container logs"""
    if not docker_available:
        return jsonify({'error': 'Docker is not available'}), 503
    
    try:
        container = docker_client.containers.get(container_id)
        
        # Get query parameters
        tail = request.args.get('tail', 'all')
        since = request.args.get('since')
        timestamps = request.args.get('timestamps', 'false').lower() == 'true'
        
        # Get logs
        logs = container.logs(
            tail=tail if tail != 'all' else 'all',
            since=since,
            timestamps=timestamps,
            decode=True
        )
        
        return jsonify({
            'container_id': container.short_id,
            'container_name': container.name,
            'logs': logs.split('\n') if logs else [],
            'timestamp': datetime.now().isoformat()
        })
        
    except NotFound:
        return jsonify({'error': f'Container {container_id} not found'}), 404
    except Exception as e:
        logger.error(f"Error getting logs for container {container_id}: {e}")
        return jsonify({'error': str(e)}), 500

@docker_api.route('/images', methods=['GET'])
def list_images():
    """List all Docker images"""
    if not docker_available:
        return jsonify({'error': 'Docker is not available'}), 503
    
    try:
        images = docker_client.images.list()
        
        image_list = []
        for image in images:
            image_list.append({
                'id': image.short_id,
                'tags': image.tags,
                'created': image.attrs['Created'],
                'size': image.attrs['Size'],
                'labels': image.labels
            })
        
        return jsonify({
            'images': image_list,
            'count': len(image_list),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error listing images: {e}")
        return jsonify({'error': str(e)}), 500

@docker_api.route('/templates', methods=['GET'])
def list_templates():
    """List available Docker templates"""
    try:
        templates = template_manager.list_templates()
        
        template_list = []
        for template in templates:
            template_list.append({
                'name': template.name,
                'project_type': template.project_type.value,
                'runtime': template.runtime.value,
                'security_level': template.security_level.value,
                'base_image': template.base_image,
                'ports': template.ports,
                'description': f"{template.project_type.value} project with {template.security_level.value} security"
            })
        
        return jsonify({
            'templates': template_list,
            'count': len(template_list),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error listing templates: {e}")
        return jsonify({'error': str(e)}), 500

@docker_api.route('/system/info', methods=['GET'])
def system_info():
    """Get Docker system information"""
    if not docker_available:
        return jsonify({'error': 'Docker is not available'}), 503
    
    try:
        info = docker_client.info()
        version = docker_client.version()
        
        return jsonify({
            'docker_version': version['Version'],
            'api_version': version['ApiVersion'],
            'containers': info['Containers'],
            'containers_running': info['ContainersRunning'],
            'containers_paused': info['ContainersPaused'],
            'containers_stopped': info['ContainersStopped'],
            'images': info['Images'],
            'driver': info['Driver'],
            'memory_total': info.get('MemTotal', 0),
            'operating_system': info['OperatingSystem'],
            'architecture': info['Architecture'],
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting system info: {e}")
        return jsonify({'error': str(e)}), 500

# Error handlers
@docker_api.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@docker_api.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500