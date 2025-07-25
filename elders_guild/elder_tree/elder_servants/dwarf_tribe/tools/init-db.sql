-- Elder Tree v2 Database Initialization
-- Creates necessary schemas and permissions

-- Create schemas
CREATE SCHEMA IF NOT EXISTS elder_tree;
CREATE SCHEMA IF NOT EXISTS knowledge;
CREATE SCHEMA IF NOT EXISTS task;
CREATE SCHEMA IF NOT EXISTS incident;
CREATE SCHEMA IF NOT EXISTS rag;

-- Grant permissions
GRANT ALL PRIVILEGES ON SCHEMA elder_tree TO elders_guild;
GRANT ALL PRIVILEGES ON SCHEMA knowledge TO elders_guild;
GRANT ALL PRIVILEGES ON SCHEMA task TO elders_guild;
GRANT ALL PRIVILEGES ON SCHEMA incident TO elders_guild;
GRANT ALL PRIVILEGES ON SCHEMA rag TO elders_guild;

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For text search
CREATE EXTENSION IF NOT EXISTS "btree_gin"; -- For composite indexes

-- Set search path
ALTER DATABASE elders_guild_db SET search_path TO elder_tree, knowledge, task, incident, rag, public;

-- Create common tables
CREATE TABLE IF NOT EXISTS elder_tree.system_health (
    id SERIAL PRIMARY KEY,
    component VARCHAR(100) NOT NULL,
    status VARCHAR(20) NOT NULL,
    last_check TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    details JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_system_health_component ON elder_tree.system_health(component);
CREATE INDEX idx_system_health_status ON elder_tree.system_health(status);

-- Insert initial health records
INSERT INTO elder_tree.system_health (component, status, details)
VALUES 
    ('knowledge_sage', 'initializing', '{"message": "Waiting for startup"}'),
    ('task_sage', 'initializing', '{"message": "Waiting for startup"}'),
    ('incident_sage', 'initializing', '{"message": "Waiting for startup"}'),
    ('rag_sage', 'initializing', '{"message": "Waiting for startup"}'),
    ('elder_flow', 'initializing', '{"message": "Waiting for startup"}');

-- Create performance metrics table
CREATE TABLE IF NOT EXISTS elder_tree.performance_metrics (
    id SERIAL PRIMARY KEY,
    component VARCHAR(100) NOT NULL,
    metric_name VARCHAR(100) NOT NULL,
    value FLOAT NOT NULL,
    tags JSONB DEFAULT '{}',
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_performance_metrics_component_time ON elder_tree.performance_metrics(component, timestamp DESC);
CREATE INDEX idx_performance_metrics_name_time ON elder_tree.performance_metrics(metric_name, timestamp DESC);