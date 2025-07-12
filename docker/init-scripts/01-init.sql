-- Elder Flow PostgreSQL Initialization Script

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Create schemas
CREATE SCHEMA IF NOT EXISTS elder_flow;
CREATE SCHEMA IF NOT EXISTS grimoire;

-- Set default search path
ALTER DATABASE elderflow SET search_path TO elder_flow, grimoire, public;

-- Grant permissions
GRANT ALL ON SCHEMA elder_flow TO elderflow;
GRANT ALL ON SCHEMA grimoire TO elderflow;
